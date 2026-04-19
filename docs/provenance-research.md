# Provenance Research Workflow

How to investigate a single provenance finding — one issue, one file, one
upstream match — from raw scanner hit to a defensible, documented chain of
custody. Use this when a `provenance` GitHub issue (e.g. #121, #122, #126) is
queued and you need to either confirm the fix, rewrite the proposed fix, or
close the issue as a false positive.

The source-level scanner (`scripts/provenance/scan_sources.py`) and the
testsuite scanner (`scripts/check_testsuite_provenance.py`) surface suspects.
This doc covers the **research** step that turns a suspect into a decision.

## 0. Inputs

Every provenance issue filed by the audit has:

- **Candidate path** — the local file (`gcc/<subtree>/<file>`).
- **Upstream match** — the corpus file (`.provenance/corpus-sources.toml`
  project name + relpath).
- **Scanner metrics** — winnow density, shingle/token Jaccard, line Jaccard,
  TLSH distance, optional PMD CPD clusters.
- **Severity** from `classify()` in `scan_sources.py`.

Treat the scanner verdict as a *starting hypothesis*, not a conclusion. The
matcher sees byte-level similarity; it does not know the real import route,
the historical license, or whether the sibling files carry the notice.

## 1. Read both files with the headers in view

```bash
# candidate
head -30 gcc/<subtree>/<file>

# upstream corpus copy
head -30 corpusbin/src/<project>/<relpath>
```

Record for each file:

- presence/absence of SPDX tag
- copyright lines and years
- origin phrase (`part of the GNU C Library`, `part of the GNU MP Library`,
  `The Go Authors`, `Ulf Adams`, `BSD 3-Clause`, …)
- any URL pointing back to upstream

A "silent" header at either end changes the story. If the upstream itself
ships the file with no header (as in #121), the GCC import cannot be faulted
for losing a notice that was never there — the fix must address both sides.

## 2. Compare to siblings in the same subtree

```bash
head -20 gcc/<subtree>/<sibling>.c ...
```

Sibling files usually tell you the import convention that subtree uses. If
every other file in `libquadmath/printf/` says *"part of the GNU MP Library"*
and every other file in `libquadmath/strtod/` says *"part of the GNU C
Library"*, the correct notice to add is the one used by the **donor** of
this specific file — not a blind copy of whatever the neighbours carry.

## 3. Find the GCC-side introduction commit

```bash
gh api repos/gcc-mirror/gcc/commits \
    -X GET -F path=<full-gcc-path> -F per_page=100 \
    -q '.[] | "\(.sha[0:12]) \(.commit.author.date[0:10]) \(.commit.author.name) | \(.commit.message|split("\n")[0])"'
```

If the list is short, inspect the oldest (introduction) commit:

```bash
gh api repos/gcc-mirror/gcc/commits/<sha> \
    -q '{author:.commit.author,message:.commit.message,
         files:[.files[] | select(.filename|contains("<pattern>")) | {filename,status}]}'
```

The message often spells out the origin verbatim (e.g. *"adds instead
floating point printing code from glibc"*). Pay attention to `From-SVN:
rXXXXXX` trailers — older commits reference SVN revisions rather than the
modern git SHA, and the SVN revision is the citable identifier.

## 4. Find the upstream-side introduction commit

The same pattern against the donor's public mirror:

| Donor             | GitHub mirror            |
|-------------------|--------------------------|
| glibc             | `bminor/glibc`           |
| LLVM              | `llvm/llvm-project`      |
| gofrontend        | `golang/gofrontend`      |
| musl              | `(use the musl git URL)` |
| FreeBSD / NetBSD  | `freebsd/freebsd-src`, `NetBSD/src` |
| GMP               | no canonical GitHub mirror; use `gmplib.org` release tarballs |

```bash
gh api repos/<mirror>/commits \
    -X GET -F path=<upstream-path> -F per_page=100 \
    -q '.[] | "\(.sha[0:12]) \(.commit.author.date[0:10]) \(.commit.author.name) | \(.commit.message|split("\n")[0])"'
```

Confirm whether the upstream file was *authored* there or itself imported
from a further-upstream project. A file can pass through multiple hands —
track the real origin, not just the nearest neighbour.

## 5. Cross-check on mailing-list archives

GCC mailing lists are at `https://gcc.gnu.org/pipermail/<list>/<YYYY-MM>/`.
The three most useful lists for import/provenance questions:

- `gcc-patches` — patch submissions, where an import is usually announced
- `gcc` — design discussion, long-form threads
- `libc-alpha` — glibc development, for glibc-origin files

Fetching the monthly archive index usually works even when interactive
Bugzilla/cgit pages are firewalled:

```bash
# use WebFetch on the monthly index
# https://gcc.gnu.org/pipermail/gcc-patches/<YYYY-Month>/thread.html
```

Legacy ML URLs (pre-2019 messages) live at
`https://gcc.gnu.org/legacy-ml/<list>/<YYYY-MM>/msgNNNNN.html` and are the
reference for SVN-era imports.

If the archive is hard to browse, a `WebSearch` with the bare filename plus
contributor name usually surfaces the right `msgNNNNN.html` page.

## 6. Check GCC Bugzilla for prior discussion

```bash
scripts/gcc-bugzilla.sh search '<symbol-or-filename>'        # fortran only
bugzilla --bugzilla=https://gcc.gnu.org/bugzilla/xmlrpc.cgi \
    query --product=gcc --summary='<term>' \
    --outputformat='%{bug_id} [%{component}|%{bug_status}] %{short_desc}'
```

Bugzilla's public search HTML is sometimes access-denied; the XMLRPC
endpoint used by the Python `bugzilla` CLI continues to work.

Also check the **upstream** project's tracker when relevant:

- glibc Bugzilla: `https://sourceware.org/bugzilla/` (product *glibc*)
- LLVM: GitHub issues on `llvm/llvm-project`
- GMP: Savannah bugs at `https://gmplib.org/`

## 7. Reconstruct the full chain before recommending a fix

Write the chain out literally, dated, with citations:

```
ORIGIN:   <project> <file> authored YYYY-MM-DD by <author>, <license>
HOP 1:    imported into <project> <file> on YYYY-MM-DD by <author>
          (<commit/SVN-rev>, ChangeLog entry: "<quote>")
HOP N:    imported into gcc/<path> on YYYY-MM-DD by <author>
          (<commit/SVN-rev>)
```

Only after this chain is explicit should you propose a header or structural
fix. A proposed fix that contradicts the chain (e.g. attributing to GMP a
file the chain shows is glibc-authored) does more harm than the trail gap
it was meant to repair.

## 8. License posture vs. trail gap

Distinguish these two outcomes:

- **License conflict** — donor license is incompatible with GCC (GPL-3+ or
  LGPL-2.1+ depending on the subtree). Action: rewrite or replace the file.
  Escalate immediately.
- **Trail gap** — donor license is compatible but the per-file notice is
  missing or ambiguous. Action: restore the notice in the style the subtree
  uses. No escalation; just a patch.

Same-license trail gaps are still worth fixing for downstream redistributors
who prune files by their per-file headers — but the fix is cosmetic, not
structural.

## 9. Write up the finding in the issue

Update the GitHub issue body (`gh issue edit <n> --body-file <file>`) so
that it carries:

- **Chain of custody** from §7
- **License posture** from §8
- **Proposed fix** that matches the subtree's convention
- **Whether an upstream fix is also warranted** (often yes when the donor
  file itself lacks a header)

Do not file *new* GitHub issues for research findings — fold the research
into the existing provenance issue.

## 10. Do NOT

- Do not act on the scanner verdict alone. It only proves text similarity.
- Do not guess the donor from the scanner's top hit when a transitive
  upstream is the real origin.
- Do not edit GCC source or send anything to gcc-patches / Bugzilla
  without explicit user permission — see `docs/upstream-submission.md`.
- Do not spawn sprawling markdown artefacts per-issue. One updated GitHub
  issue body is the record; only expand this doc if the workflow itself
  needs a new step.

## Worked example: issue #121

- Candidate: `gcc/libquadmath/strtod/tens_in_limb.c`, no header.
- Scanner hit: `glibc/stdlib/tens_in_limb.c` (winnow 0.80, line 0.79).
- Siblings in `libquadmath/printf/` carry full GMP LGPL-2.1+ notices; the
  scanner's "GMP data table" framing follows from that pattern.
- GCC introduction: SVN r170254 / github sha `a855debfb46e`, Jakub Jelinek,
  2011-02-17 — commit replaces the gdtoa (Netlib/David Gay) pathway with
  glibc's strtod/tens_in_limb/mpn2flt128 code. Mailing-list announcement:
  legacy-ml `gcc-patches/2011-02/msg00885.html` ("adds instead floating
  point printing code from glibc").
- Upstream introduction: github sha `72f1012788c0`, Ulrich Drepper,
  2008-03-08 — split `_tens_in_limb[]` out of `stdlib/strtod_l.c` into a
  standalone aux file. The split commit adds no header, and the current
  glibc master still ships the file header-less.
- Further upstream: GMP is the semantic source of `mp_limb_t` and
  `BITS_PER_MP_LIMB` but ships **no** `tens_in_limb` table (GMP uses
  `__mp_bases[]` instead).
- Chain: GMP constants → glibc-authored table (inline, 1997ish) → glibc
  standalone file (2008) → libquadmath (2011).
- License posture: donor is glibc (LGPL-2.1+), target is libquadmath
  (LGPL-2.1+). No conflict. Trail gap only.
- Correct fix: add the "part of the GNU C Library" / LGPL-2.1+ header used
  by the sibling `libquadmath/strtod/strtod_l.c`. **Not** the GMP notice
  the original issue body suggested. Additionally, glibc's own
  `stdlib/tens_in_limb.c` is missing a header upstream — a complete fix
  reports it to `libc-alpha` first and then re-imports.
