#!/usr/bin/env python3
"""Build a fingerprint index over corpusbin/src/.

Indexes every source file under corpusbin/src/<project>/ into a sqlite DB
at corpusbin/index/corpus.sqlite plus a pickled MinHashLSH for fast
nearest-neighbour lookup.

Schema:
    files(id PK, project, relpath, bytes, tokens, kgrams, tlsh, minhash,
          winnow_hashes, winnow_positions, sha256)
    fingerprints(fp_hash, file_id)  -- winnow hashes, indexed on fp_hash
    meta(key PK, value)

Re-running is idempotent: files with matching sha256 are skipped. If
--rebuild is passed the tables are dropped first.
"""

from __future__ import annotations

import argparse
import hashlib
import pickle
import sqlite3
import sys
import time
from pathlib import Path

import tlsh
from datasketch import MinHashLSH

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.provenance._lib import is_text_candidate  # noqa: E402
from scripts.provenance.fingerprint import (  # noqa: E402
    DEFAULT_K,
    DEFAULT_MINHASH_PERM,
    DEFAULT_WINDOW,
    fingerprint_text,
    minhash_from_bytes,
)

CORPUS_ROOT = REPO_ROOT / "corpusbin" / "src"
INDEX_ROOT = REPO_ROOT / "corpusbin" / "index"
DB_PATH = INDEX_ROOT / "corpus.sqlite"
LSH_PATH = INDEX_ROOT / "corpus.lsh.pkl"

LSH_THRESHOLD = 0.2
MIN_BYTES = 256
MAX_BYTES = 2 * 1024 * 1024


SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    relpath TEXT NOT NULL,
    bytes INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    kgrams INTEGER NOT NULL,
    tlsh TEXT NOT NULL,
    minhash BLOB NOT NULL,
    winnow_hashes BLOB NOT NULL,
    winnow_positions BLOB NOT NULL,
    sha256 TEXT NOT NULL,
    UNIQUE(project, relpath)
);
CREATE TABLE IF NOT EXISTS fingerprints (
    fp_hash INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS fp_hash_idx ON fingerprints(fp_hash);
CREATE INDEX IF NOT EXISTS fp_file_idx ON fingerprints(file_id);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(rebuild: bool) -> sqlite3.Connection:
    INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    if rebuild and DB_PATH.exists():
        DB_PATH.unlink()
        if LSH_PATH.exists():
            LSH_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def iter_corpus_files():
    for project_dir in sorted(CORPUS_ROOT.iterdir()):
        if not project_dir.is_dir():
            continue
        project = project_dir.name
        for file in project_dir.rglob("*"):
            if not file.is_file():
                continue
            if ".git" in file.parts:
                continue
            if file.name == ".corpus-sha":
                continue
            rel = file.relative_to(project_dir).as_posix()
            if not is_text_candidate(rel):
                continue
            try:
                size = file.stat().st_size
            except OSError:
                continue
            if size < MIN_BYTES or size > MAX_BYTES:
                continue
            yield project, rel, file


def hash_pack(values: list[int]) -> bytes:
    return b"".join(
        int(v).to_bytes(8, "little", signed=True) for v in values
    )


def index(rebuild: bool, limit: int | None) -> None:
    conn = connect(rebuild)
    cur = conn.cursor()
    existing: dict[tuple[str, str], tuple[int, str]] = {
        (row[0], row[1]): (row[2], row[3])
        for row in cur.execute("SELECT project, relpath, id, sha256 FROM files")
    }

    added = 0
    skipped = 0
    failed = 0
    started = time.monotonic()

    for project, rel, path in iter_corpus_files():
        if limit is not None and added >= limit:
            break
        try:
            data = path.read_bytes()
        except OSError:
            failed += 1
            continue
        sha = hashlib.sha256(data).hexdigest()
        key = (project, rel)
        if key in existing and existing[key][1] == sha:
            skipped += 1
            continue

        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            failed += 1
            continue

        fp = fingerprint_text(text, k=DEFAULT_K, window=DEFAULT_WINDOW, num_perm=DEFAULT_MINHASH_PERM)
        # Require meaningful body after stripping the file-level header comment.
        if fp.token_count < 80 or fp.kgram_count < 40:
            skipped += 1
            continue

        try:
            digest = tlsh.hash(data)
        except Exception:
            digest = ""

        if key in existing:
            file_id = existing[key][0]
            cur.execute("DELETE FROM fingerprints WHERE file_id = ?", (file_id,))
            cur.execute(
                "UPDATE files SET bytes=?, tokens=?, kgrams=?, tlsh=?, minhash=?, "
                "winnow_hashes=?, winnow_positions=?, sha256=? WHERE id=?",
                (
                    len(data), fp.token_count, fp.kgram_count, digest,
                    fp.minhash_bytes, hash_pack(fp.winnow_hashes),
                    hash_pack(fp.winnow_positions), sha, file_id,
                ),
            )
        else:
            cur.execute(
                "INSERT INTO files(project, relpath, bytes, tokens, kgrams, tlsh, "
                "minhash, winnow_hashes, winnow_positions, sha256) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    project, rel, len(data), fp.token_count, fp.kgram_count,
                    digest, fp.minhash_bytes, hash_pack(fp.winnow_hashes),
                    hash_pack(fp.winnow_positions), sha,
                ),
            )
            file_id = cur.lastrowid

        cur.executemany(
            "INSERT INTO fingerprints(fp_hash, file_id) VALUES (?, ?)",
            [(h, file_id) for h in set(fp.winnow_hashes)],
        )
        added += 1
        if added % 500 == 0:
            conn.commit()
            elapsed = time.monotonic() - started
            print(f"  indexed {added} files in {elapsed:.1f}s", flush=True)

    conn.commit()
    cur.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("k", str(DEFAULT_K)),
    )
    cur.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("window", str(DEFAULT_WINDOW)),
    )
    cur.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("num_perm", str(DEFAULT_MINHASH_PERM)),
    )
    cur.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("indexed_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    )
    conn.commit()

    print(f"added={added} skipped={skipped} failed={failed}")
    build_lsh(conn)
    conn.close()


def build_lsh(conn: sqlite3.Connection) -> None:
    print("building MinHash LSH index", flush=True)
    lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=DEFAULT_MINHASH_PERM)
    cur = conn.cursor()
    n = 0
    for row in cur.execute("SELECT id, minhash FROM files"):
        file_id, mh_bytes = row
        try:
            mh = minhash_from_bytes(mh_bytes)
        except ValueError:
            continue
        lsh.insert(str(file_id), mh, check_duplication=False)
        n += 1
        if n % 2000 == 0:
            print(f"  LSH inserted {n}", flush=True)
    with LSH_PATH.open("wb") as handle:
        pickle.dump(lsh, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"LSH index written: {LSH_PATH} ({n} entries)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true",
                        help="Drop and rebuild the index from scratch")
    parser.add_argument("--limit", type=int, default=None,
                        help="Stop after N files (for smoke tests)")
    args = parser.parse_args()
    if not CORPUS_ROOT.exists():
        print(f"corpus root missing: {CORPUS_ROOT}", file=sys.stderr)
        return 1
    index(rebuild=args.rebuild, limit=args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
