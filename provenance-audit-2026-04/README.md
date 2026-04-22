# Fujitsu-CTS provenance attribution — 2026-04-22

## Scope (revised 2026-04-22)

The provenance audit originally flagged 27 testcases (#139–#165).  On
review, retroactive `! Contributed by <Bugzilla reporter>` headers are
not needed: when the Bugzilla reporter wrote the reducer themselves,
the existing `PR fortran/N` comment + Bugzilla URL is already an
adequate trace.

What DOES need an in-file header is external third-party material.
Four of the 27 cases are derivatives of the **Fujitsu Compiler Test
Suite** (github.com/fujitsu/compiler-test-suite, Apache-2.0 WITH
LLVM-exception, GPLv3-compatible).  For those, the chain of custody
belongs in the file itself.

## Deliverable

**One single upstream patch** on branch
`testsuite/fujitsu-cts-attribution-2026-04` adding the Fujitsu
provenance header to the three upstream-master testcases derived from
the Fujitsu CTS:

- `gcc/testsuite/gfortran.dg/pdt_85.f03`         (PR fortran/123949)
- `gcc/testsuite/gfortran.dg/pr123949.f90`       (PR fortran/123949)
- `gcc/testsuite/gfortran.dg/pr124208.f90`       (PR fortran/124208)

Two further Fujitsu-derived testcases live on fork branches and carry
the header via a per-branch commit (not externally distributed):

- `gcc/testsuite/gfortran.dg/pr124631.f90` on `pr124631-fix`
- `gcc/testsuite/gfortran.dg/pr124666.f90` on `pr124666-fix`

## Commit trailers

```
Assisted-by: Claude (Anthropic)
Assisted-by: GPT (OpenAI)
Signed-off-by: Christopher Albert <albert@tugraz.at>
```

`Assisted-by:` sits above the ChangeLog block because GCC's trailer
parser in `contrib/gcc-changelog/git_commit.py` does not whitelist it.

## Closed as not needed (23 issues)

Issues #139, #140, #141, #142, #143, #144, #145, #146, #147, #148,
#149, #150, #151, #152, #153, #154, #155, #156, #157, #158, #159,
#160, #161 — all tracked reducers are internal Bugzilla Comment #0
code from the reporter themselves, adequately traced via the PR
reference.  No header needed.

## Remaining open

- #162 PR123949 — in upstream/master, single patch below.
- #163 PR124208 — in upstream/master, single patch below.
- #164 PR124631 — fork-only, header on `pr124631-fix`.
- #165 PR124666 — fork-only, header on `pr124666-fix`.
- #166 follow-up tracker (next steps).
