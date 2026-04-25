# Provenance Research Workflow

> **Disclaimer.** Everything described in this document is a personal
> research workflow over scanner output. Findings produced by the
> workflow are working observations, not legal conclusions or
> allegations against any contributor or project. See
> [`../DISCLAIMER.md`](../DISCLAIMER.md). Severity tags, "silent" /
> "marked" classifications, and chain-of-custody narratives are
> heuristics, not legal judgements.

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

## 9a. Re-label and close based on the research outcome

Research almost always moves an issue off the severity it was filed at.
The scanner can only see byte-level similarity, so `[CRITICAL]` at filing
time regularly collapses to "same-license trail gap" or "not a defect at
all" once the chain is explicit. The labels and open/closed state have
to move with the finding, because downstream filters (sprint planning,
upstream queues, triage reports) read them — not the title, and not the
TOML registry.

Label vocabulary in `krystophny/gcc-dev`:

- `severity:critical`, `severity:high`, `severity:medium`, `severity:low`
  — post-research severity. Always applied, exactly one per issue.
- `provenance` — always applied; set by the filer.
- `bug` — applied when the finding is a real defect (trail gap, stripped
  notice, license conflict). Omitted for false positives.
- `invalid` — applied when the research outcome is `not_derived` or any
  other "scanner fired but this is not a defect" class.

Rules to apply after writing up §9:

1. **Set a severity label.** Remove any stale `severity:*` label and add
   the one matching the post-research severity.  Same-license trail gaps
   with preserved author credit are `severity:low` (cosmetic NOTE fix).
   Stripped copyright/license paragraphs are `severity:high`.  Genuine
   license conflicts are `severity:critical`.
2. **If the finding is not a defect, close the issue.**  Use
   `gh issue close <n> --reason 'not planned'` and add the `invalid`
   label.  Drop `bug` if it was applied by the filer.  Registry
   resolutions that trigger close: `not_derived`, `attributed`, and
   `wontfix` when the subtree does not use per-file notices.
3. **Leave `bug` only on real defects.**  `attributed` entries with a
   canonical-source note already present in the file are not bugs.
4. **Update `.provenance/source-review.toml` before touching the issue.**
   The label change is a consequence of the registry decision; do not
   reverse the order.

Example (research concluded `not_derived`):

```bash
gh issue comment <n> --body "Research outcome: not_derived. ..."
gh issue edit <n> --add-label invalid --remove-label bug
gh issue edit <n> --remove-label 'severity:critical'
gh issue close <n> --reason 'not planned'
```

Example (research concluded same-license trail gap downgrading from
`[HIGH]` to low-risk):

```bash
gh issue edit <n> --add-label 'severity:low' \
                  --remove-label 'severity:high'
```

The filer (`scripts/provenance/file_findings.py`) stamps the
scanner-reported severity label on creation.  The researcher's job is to
replace it with the **post-research** severity and, when appropriate,
close the issue.

## 10. Do NOT

- Do not act on the scanner verdict alone. It only proves text similarity.
- Do not guess the donor from the scanner's top hit when a transitive
  upstream is the real origin.
- Do not edit GCC source or send anything to gcc-patches / Bugzilla
  without explicit user permission — see `docs/upstream-submission.md`.
- Do not spawn sprawling markdown artefacts per-issue. One updated GitHub
  issue body is the record; only expand this doc if the workflow itself
  needs a new step.
- Do not leave a researched issue with its filing-time severity label or
  open state when the research has changed the picture. §9a is not
  optional — filters depend on the labels being current.
- Do not edit the issue title to encode the new severity. The title
  carries the scanner-reported severity at filing time for historical
  traceability; post-research severity lives in `severity:*` labels.

## 11. Reverse provenance (GCC code shipped by upstreams without credit)

The inbound direction above catches *GCC importing without credit*. The
outbound direction — external projects that took GCC code and dropped the
notice — is tracked under the `provenance:downstream` label. Two scanners
cover it:

**Quick post-filter.** `scripts/provenance/scan_downstream.py` consumes an
existing `scan_sources.py` JSON report and, for every `(gcc, upstream)`
pair, inspects the upstream header for GCC/FSF/RLE attribution. Cheap but
limited to pairs that scan_sources.py already surfaced (i.e., GCC files
that looked like potential imports).

```
python3 scripts/provenance/scan_downstream.py \
    /tmp/source-provenance-all-cpd.json \
    --require-gcc-fsf --json /tmp/downstream-findings.json
```

**Proper GCC-indexed probe.** `scripts/provenance/index_gcc.py` builds a
fingerprint index over GCC's widely-copied subtrees (libiberty, libgcc,
libstdc++-v3/{src,include,libsupc++}, libquadmath, libgfortran, libgomp,
libitm, libatomic, libbacktrace, libssp, libvtv, libobjc, libcpp, libcody,
libdecnumber, include, fixincludes). Then `scan_corpus.py` walks every
corpus file under `corpusbin/src/<project>/`, classifies its header for
GCC attribution, and probes the GCC LSH. Silent upstream + strong GCC
match is flagged.

```
python3 scripts/provenance/index_gcc.py --rebuild
python3 scripts/provenance/scan_corpus.py --require-silent \
    --min-severity medium --json /tmp/corpus-vs-gcc.json
python3 scripts/provenance/file_downstream.py \
    /tmp/corpus-vs-gcc.json --dry-run --min-severity high
```

`file_downstream.py` wraps the filing workflow with documented
`FALSE_POSITIVE_RULES` — patterns where the scanner match is explained by
a common non-GCC upstream or an acknowledged port. Every rule is a pair
of regexes `(upstream_pattern, gcc_pattern)`; pairs that match are
dropped before any issue is filed. Extend this map as new sibling
patterns are documented.

Directionality is DELIBERATELY not inferred from the corpus clones: the
`corpusbin/src/*` trees are all `--depth=1`, so `git log --reverse` returns
the clone date, not the real introduction date. `scan_downstream._git_has_history`
refuses to return a date when `.git/shallow` exists. Severity tops out at
`high` from the scanner alone; `critical` requires human review plus a
deep git history check.

`--require-gcc-fsf` drops pairs where the GCC-side file lacks an FSF
copyright. Without FSF, both GCC and upstream usually import from a
common third party (ulfjack/ryu, FreeBSD msun via openlibm, IBM
decNumber) and the scanner match is cross-upstream triangulation.

For every candidate still suspected of being a real downstream gap:

1. Deepen the upstream clone locally (`git -C corpusbin/src/<project>
   fetch --depth=50000 origin`) and rerun to confirm direction from dates.
2. If GCC genuinely predates the upstream copy AND the upstream file still
   carries no GCC/FSF attribution, file an issue in `krystophny/gcc-dev`
   with labels `provenance provenance:downstream severity:<post-research>`
   plus the upstream tracker URL (see the `TRACKERS` map in
   `scripts/provenance/scan_downstream.py` and `file_downstream.py`).
3. The gcc-dev issue is the tracking handle; the *corrective action* is
   filed on the upstream tracker. Do not attempt the upstream fix from
   this meta-repo; document the plan in the gcc-dev issue body and
   follow up.

Documented false-positive families (all in
`file_downstream.FALSE_POSITIVE_RULES`):

- `libstdc++-v3/src/c++17/ryu/*` vs ulfjack-ryu, libcxx ryu, llvm-libc
  ryu, picolibc libc/stdio/ryu, postgresql src/common/ryu tables,
  microsoft-stl xcharconv_ryu_tables, boost-charconv, dragonbox — all
  import from Ulf Adams' Apache-2.0/Boost upstream.
- `libquadmath/math/*q.c` vs openlibm {src,ld80,ld128}/, newlib libm,
  picolibc libm, bionic upstream-freebsd/msun, apple-libc math,
  musl src/math/ — Sun/FreeBSD msun shared source; Moshier relicensed
  his 2001 LGPL reworks.
- `libdecnumber/*` vs icu4c decNumber / decContext — IBM General Decimal
  Arithmetic library (Mike Cowlishaw); both GCC and ICU import it.
- `libiberty/{bsearch,strtol,strtoul,strncasecmp,strchr,memcpy,...}` vs
  freebsd-libc, netbsd-libc, openbsd-libc, apple-libc, postgresql
  src/port, illumos libc, newlib-cygwin libc/stdlib, bionic — all share
  the original UC Berkeley BSD origin.
- `gcc/rust/*` or `gcc/algol68/*` vs `gofrontend/go/*` — gccrs and gccra68
  port FROM gofrontend; GCC is downstream (issues #120, #126).
- `libgcc/config/visium/memcpy,memset` vs newlib/picolibc sibling sync
  (issues #132, #133).
- `libgcc/config/rl78/vregs.h` vs newlib libgloss sibling (issue #134).
- `libgcc/config/riscv/feature_bits.c` vs llvm-project compiler-rt
  riscv.c — coordinated riscv-c-api-doc ABI (issue #122).

As of 2026-04-20: scanning 44k corpus files against a 3k-file GCC index
yields ~355 raw findings, all reducible to one of the patterns above.
No genuine downstream-provenance defects detected.

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
