"""Winnowing + MinHash fingerprint helpers.

The winnowing algorithm (Schleimer, Wilkerson, Aiken 2003) selects a subset
of k-gram hashes by taking the min hash in each sliding window. That subset
is robust to insertions/deletions and small edits: two documents with a
common substring share the same winnowed fingerprints at aligned positions.

We combine that with MinHash (datasketch) signatures for LSH-accelerated
nearest-neighbour lookup: a candidate document's MinHash is compared against
a corpus-wide LSH index to pick the top-K likely sources before we compute
exact winnow-overlap and token-shingle Jaccard.

The k and window sizes (k=8, window=5) follow the MOSS defaults tuned for
source code. k smaller means more matches, larger means more robust to
rename; 8 is a good compromise for C/C++/Rust/Go.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import mmh3
from datasketch import MinHash

from scripts.provenance._lib import tokenize_for_similarity


DEFAULT_K = 8
DEFAULT_WINDOW = 5
DEFAULT_MINHASH_PERM = 128


def strip_leading_comment_block(text: str) -> str:
    """Strip the leading file-level comment so license boilerplate does not
    dominate the fingerprint. Conservative: only peel the header comment, not
    comments further down.
    """
    i = 0
    n = len(text)
    while i < n and text[i] in " \t\r\n":
        i += 1
    if i >= n:
        return text
    # /* ... */ style
    if text.startswith("/*", i):
        end = text.find("*/", i + 2)
        if end != -1:
            j = end + 2
            # eat trailing whitespace / blank lines
            while j < n and text[j] in " \t\r\n":
                j += 1
            return text[j:]
    # // ... line-comment block
    if text.startswith("//", i):
        lines = text[i:].splitlines(keepends=True)
        j = i
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("//") or stripped in ("\n", "\r\n", ""):
                j += len(line)
            else:
                break
        return text[j:]
    # Fortran ! header (each line starts with !)
    if text.startswith("!", i):
        lines = text[i:].splitlines(keepends=True)
        j = i
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("!") or stripped in ("\n", "\r\n", ""):
                j += len(line)
            else:
                break
        return text[j:]
    return text


def kgram_hashes(tokens: list[str], k: int = DEFAULT_K) -> list[int]:
    if len(tokens) < k:
        if not tokens:
            return []
        joined = " ".join(tokens).encode("utf-8")
        return [mmh3.hash64(joined, signed=True)[0]]
    out: list[int] = []
    for index in range(len(tokens) - k + 1):
        chunk = " ".join(tokens[index : index + k]).encode("utf-8")
        out.append(mmh3.hash64(chunk, signed=True)[0])
    return out


def winnow(hashes: list[int], window: int = DEFAULT_WINDOW) -> list[tuple[int, int]]:
    """Return the winnowed subset as (position, hash) pairs.

    At each sliding window, pick the rightmost occurrence of the minimum
    hash and emit it if it has not been emitted yet at that position. This
    matches the classical MOSS algorithm from section 4 of the paper.
    """
    if not hashes:
        return []
    if len(hashes) <= window:
        min_idx = min(range(len(hashes)), key=lambda idx: hashes[idx])
        return [(min_idx, hashes[min_idx])]

    out: list[tuple[int, int]] = []
    last_emitted = -1
    for start in range(len(hashes) - window + 1):
        end = start + window
        best_idx = start
        for i in range(start + 1, end):
            if hashes[i] <= hashes[best_idx]:
                best_idx = i
        if best_idx != last_emitted:
            out.append((best_idx, hashes[best_idx]))
            last_emitted = best_idx
    return out


@dataclass
class Fingerprint:
    token_count: int
    kgram_count: int
    winnow_hashes: list[int]
    winnow_positions: list[int]
    minhash_bytes: bytes
    kgram_set: frozenset[int]


def fingerprint_text(
    text: str,
    k: int = DEFAULT_K,
    window: int = DEFAULT_WINDOW,
    num_perm: int = DEFAULT_MINHASH_PERM,
    strip_header: bool = True,
) -> Fingerprint:
    if strip_header:
        text = strip_leading_comment_block(text)
    tokens = tokenize_for_similarity(text)
    kgrams = kgram_hashes(tokens, k=k)
    wins = winnow(kgrams, window=window)
    mh = MinHash(num_perm=num_perm)
    for h in kgrams:
        mh.update(h.to_bytes(8, "little", signed=True))
    return Fingerprint(
        token_count=len(tokens),
        kgram_count=len(kgrams),
        winnow_hashes=[h for _pos, h in wins],
        winnow_positions=[pos for pos, _h in wins],
        minhash_bytes=bytes(mh.digest().astype("<u4").tobytes()),
        kgram_set=frozenset(kgrams),
    )


def minhash_from_bytes(data: bytes, num_perm: int = DEFAULT_MINHASH_PERM) -> MinHash:
    import numpy as np

    mh = MinHash(num_perm=num_perm)
    arr = np.frombuffer(data, dtype="<u4")
    if arr.size != num_perm:
        raise ValueError(f"minhash bytes size {arr.size} != {num_perm}")
    mh.hashvalues = arr.astype(mh.hashvalues.dtype, copy=True)
    return mh


def winnow_density(
    candidate: Iterable[int], corpus: Iterable[int]
) -> tuple[int, float]:
    """Return (matched_count, matched/candidate_fraction) for winnow hashes."""
    cand_set = set(candidate)
    corp_set = set(corpus)
    if not cand_set:
        return (0, 0.0)
    matched = len(cand_set & corp_set)
    return (matched, matched / len(cand_set))


def longest_run(positions_a: list[int], positions_b: list[int], hashes_a: list[int], hashes_b: list[int]) -> int:
    """Length of the longest contiguous run of shared winnow hashes.

    Takes two aligned (position, hash) streams and finds the longest
    subsequence where both streams have matching hashes at consecutive
    positions of the candidate stream. This approximates the classic
    MOSS "match tile" length.
    """
    if not hashes_a or not hashes_b:
        return 0
    b_by_hash: dict[int, list[int]] = {}
    for pos, h in zip(positions_b, hashes_b):
        b_by_hash.setdefault(h, []).append(pos)
    best = 0
    current = 0
    last_a_pos = None
    for pos, h in zip(positions_a, hashes_a):
        if h in b_by_hash:
            if last_a_pos is not None and pos - last_a_pos <= 3:
                current += 1
            else:
                current = 1
            best = max(best, current)
            last_a_pos = pos
        else:
            current = 0
            last_a_pos = None
    return best
