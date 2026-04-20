#!/usr/bin/env python3
"""Build a fingerprint index over the GCC source tree.

Mirrors scripts/provenance/index_corpus.py but sources from gcc/ rather
than corpusbin/src/. The resulting sqlite + LSH pickle feed
scripts/provenance/scan_corpus.py which hunts for upstream projects that
copy GCC code without retaining the FSF / Runtime Library Exception notice.

Scope is restricted to subtrees that are commonly lifted by other
projects: libiberty, libgcc, libstdc++-v3/{src,include,libsupc++}, the
small runtime libraries (libatomic, libbacktrace, libitm, libssp, libvtv,
libobjc, libquadmath, libgfortran, libgomp), include/, fixincludes/.
Pure-compiler trees (gcc/gcc/) are skipped because nobody lifts them as
a library.

Output files:
    corpusbin/index/gcc.sqlite
    corpusbin/index/gcc.lsh.pkl

Schema matches index_corpus.py so scan_corpus.py can reuse the same
winnow + minhash machinery.
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

GCC_ROOT = REPO_ROOT / "gcc"
INDEX_ROOT = REPO_ROOT / "corpusbin" / "index"
DB_PATH = INDEX_ROOT / "gcc.sqlite"
LSH_PATH = INDEX_ROOT / "gcc.lsh.pkl"

LSH_THRESHOLD = 0.2
MIN_BYTES = 256
MAX_BYTES = 2 * 1024 * 1024

# Subtrees widely copied by external projects. Each prefix is relative to
# the gcc/ worktree root. Keep this tight — scanning gcc/gcc/ floods the
# index with files nobody reuses as a library.
INCLUDE_PREFIXES = (
    "libiberty/",
    "libgcc/",
    "libstdc++-v3/src/",
    "libstdc++-v3/include/",
    "libstdc++-v3/libsupc++/",
    "libatomic/",
    "libbacktrace/",
    "libitm/",
    "libssp/",
    "libvtv/",
    "libobjc/",
    "libquadmath/",
    "libgfortran/",
    "libgomp/",
    "libcpp/",
    "libcody/",
    "libdecnumber/",
    "include/",
    "fixincludes/",
)

EXCLUDE_SUBSTR = (
    # Testsuites are handled elsewhere and add noise.
    "/testsuite/",
)

EXCLUDE_PREFIXES = (
    # Bundled upstream libraries; already covered via their own corpora.
    "libgo/",
    "libphobos/",
    "libffi/",
    "libgrust/",
    "libsanitizer/",
    "zlib/",
    # Pure-compiler tree (filters + transformations) is not a library.
    "gcc/",
    "gnattools/",
    "contrib/",
)


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


def in_scope(rel: str) -> bool:
    if not any(rel.startswith(prefix) for prefix in INCLUDE_PREFIXES):
        return False
    for bad in EXCLUDE_SUBSTR:
        if bad in rel:
            return False
    for bad in EXCLUDE_PREFIXES:
        if rel.startswith(bad):
            return False
    return True


def iter_gcc_files():
    for path in GCC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        try:
            rel = path.relative_to(GCC_ROOT).as_posix()
        except ValueError:
            continue
        if not in_scope(rel):
            continue
        if not is_text_candidate(rel):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size < MIN_BYTES or size > MAX_BYTES:
            continue
        yield rel, path


def hash_pack(values: list[int]) -> bytes:
    return b"".join(int(v).to_bytes(8, "little", signed=True) for v in values)


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

    project = "gcc"
    for rel, path in iter_gcc_files():
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
                (len(data), fp.token_count, fp.kgram_count, digest,
                 fp.minhash_bytes, hash_pack(fp.winnow_hashes),
                 hash_pack(fp.winnow_positions), sha, file_id),
            )
        else:
            cur.execute(
                "INSERT INTO files(project, relpath, bytes, tokens, kgrams, tlsh, "
                "minhash, winnow_hashes, winnow_positions, sha256) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (project, rel, len(data), fp.token_count, fp.kgram_count,
                 digest, fp.minhash_bytes, hash_pack(fp.winnow_hashes),
                 hash_pack(fp.winnow_positions), sha),
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
            print(f"  indexed {added} gcc files in {elapsed:.1f}s", flush=True)

    conn.commit()
    for key, val in (("k", str(DEFAULT_K)),
                     ("window", str(DEFAULT_WINDOW)),
                     ("num_perm", str(DEFAULT_MINHASH_PERM)),
                     ("indexed_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))):
        cur.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (key, val),
        )
    conn.commit()
    print(f"added={added} skipped={skipped} failed={failed}")
    build_lsh(conn)
    conn.close()


def build_lsh(conn: sqlite3.Connection) -> None:
    print("building MinHash LSH index over gcc/", flush=True)
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
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if not GCC_ROOT.exists():
        print(f"gcc source root missing: {GCC_ROOT}", file=sys.stderr)
        return 1
    index(rebuild=args.rebuild, limit=args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
