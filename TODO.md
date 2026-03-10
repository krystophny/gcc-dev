# GCC Fortran Regression Fix TODO

## PR106946 (#88) - Finalize [IN PROGRESS]

**Status:** PATCH READY. Full `check-gfortran` passed, patch exported and pushed
on branch `origin/pr106946-fix` (`88049a3af71`).

### Task list

- [x] Task 1: Review the current fix and test for correctness/minimality.
- [x] Task 1 review: Self-review the changed code paths and test coverage before building.
- [x] Task 2: Rebuild the affected compiler pieces and run targeted PR106946 validation.
- [x] Task 2 review: Inspect the targeted test results and compiler behavior for regressions.
- [x] Task 3: Run a clean full `check-gfortran`.
- [x] Task 3 review: Check `FAIL`/`XPASS` deltas and confirm no new regressions.
- [x] Task 4: Commit with `gcc-commit-mklog`, run `git gcc-verify`, export the patch, and push the branch.
- [x] Task 4 review: Inspect commit metadata, generated patch contents, and pushed branch state.
- [x] Task 5: Update `pr/106946/` and GitHub issue `#88` to `patch-ready`.
- [x] Task 5 review: Verify the issue label/comment state and local meta-repo tracking files.

**Files changed:**
- `gcc/fortran/decl.cc` - CLASS component cleanup on error in `gfc_match_data_decl`
- `gcc/fortran/symbol.cc` - Extract `gfc_free_component`, make `gfc_delete_symtree` non-static
- `gcc/fortran/gfortran.h` - Declarations for above
- `gcc/testsuite/gfortran.dg/pr106946.f90` - Test case

**Root cause:** `gfc_build_class_symbol` (class.cc:747) creates CLASS container
symbols with `gfc_new_symbol` + `gfc_new_symtree`, bypassing the undo mechanism.
On syntax error, `gfc_undo_symbols` frees the referenced type but leaves the
CLASS container orphaned with dangling pointers. ICE in `resolve_fl_derived`.

**Fix:** In `gfc_match_data_decl` cleanup, detect CLASS components added during
the failed statement (via `attr.is_class` check on `ts.u.derived`), remove their
CLASS container from the namespace symtree, release the symbol, and free the
component. Non-CLASS components are left for secondary error reporting.

**Steps to finalize:**
```bash
cd gcc-build/gcc
make -j32 -k check-gfortran > /tmp/test-pr106946.log 2>&1
grep -cE "^FAIL|^XPASS" testsuite/gfortran/gfortran.sum  # must be 0

cd ../../gcc
git checkout -b pr106946-fix upstream/master
git add gcc/fortran/decl.cc gcc/fortran/symbol.cc gcc/fortran/gfortran.h \
        gcc/testsuite/gfortran.dg/pr106946.f90

cat > /tmp/gcc-commit-msg.txt <<'EOF'
fortran: Fix ICE on invalid CLASS component in derived type [PR106946]

When a CLASS component declaration inside a derived type has a syntax
error (e.g., missing comma), gfc_build_class_symbol creates a CLASS
container symbol outside the undo mechanism.  On error recovery,
gfc_undo_symbols frees the referenced type but leaves the CLASS
container as an orphan with dangling pointers, causing an ICE during
resolution.

Fix by detecting and removing CLASS container components and their
symbols from the namespace during error cleanup in gfc_match_data_decl.
Also extract gfc_free_component helper from free_components and make
gfc_delete_symtree available outside symbol.cc.

gcc/fortran/ChangeLog:

	PR fortran/106946
	* decl.cc (gfc_match_data_decl): Remove CLASS components and their
	container symbols on MATCH_ERROR inside derived type definitions.
	* symbol.cc (gfc_free_component): New, extracted from free_components.
	(free_components): Use gfc_free_component.
	(gfc_delete_symtree): Make non-static.
	* gfortran.h (gfc_free_component): Declare.
	(gfc_delete_symtree): Declare.

gcc/testsuite/ChangeLog:

	PR fortran/106946
	* gfortran.dg/pr106946.f90: New test.
EOF
GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/106946"]' \
  git commit -s -F /tmp/gcc-commit-msg.txt
git gcc-verify HEAD
git format-patch -1 HEAD -o ../pr/106946/
git push origin pr106946-fix
```

Patch exported: `pr/106946/0001-fortran-Fix-ICE-on-invalid-CLASS-component-in-derive.patch`

Then: `gh issue edit 88 --add-label patch-ready`

---

## Backlog Audit (2026-03-10)

**Confirmed locally still reproducing with `gcc-build/gcc/gfortran -B gcc-build/gcc`:**

- `PR82721` (`#56`) - still ICEs after the duplicate-type diagnostic.
- `PR102459` (`#79`) - still ICEs with `-fopenmp`.

**Quick compile check did not reproduce immediately; re-verify before spending
fix time:**

- `PR95338` (`#68`) - quick `-O1 -ff2c` compile did not ICE.
- `PR101760` (`#76`) - quick `-fopenmp` compile did not ICE.
- `PR102596` (`#80`) - quick `-fopenmp` compile did not ICE.

**Needs dedicated re-check / special setup:**

- `PR109788` (`#91`) - requires the precise UB-triggering path, likely with
  sanitizer instrumentation or exact IPA conditions.
- `PR79524` (`#55`) - needs Valgrind/ASan confirmation on the invalid-code path.
- `PR120723` (`#96`) - needs `openacc.mod` / OpenACC-capable setup for a real
  compile check.
- `PR120286` (`#95`) - runtime OpenMP wrong-code reproducer, not a quick
  compile-only check.
- `PR110626` (`#92`) - runtime/finalization behavior issue.
- `PR60576` (`#53`) - runtime/ASan descriptor overflow issue.
- `PR42954` (`#52`) - architectural preprocessor gap, not a quick ICE check.

## Remaining Open Issues (by priority, then complexity)

### P3 - High Priority

| GH# | PR | Title | Complexity | Category |
|-----|----|-------|------------|----------|
| #96 | 120723 | ICE attach(scalar) OpenACC | medium | ice, openacc |
| #95 | 120286 | Double free with OpenMP | high | wrong-code, openmp |

**PR120723:** Debug `trans-openmp.cc` map clause generation for scalar attach.
Should generate `GOMP_MAP_ATTACH`, not pointer mapping. Test with offload build.

**PR120286:** Refcount or deep-copy issue in `trans-openmp.cc` / `trans-array.cc`.
Compare tree dumps with/without OpenMP. May need runtime tracing in libgomp.

### P4 - Low Complexity

| GH# | PR | Title | Category |
|-----|----|-------|----------|
| #56 | 82721 | Corrupted error message, sometimes ICE | ice |
| #91 | 109788 | UB: shift exponent 64 | runtime UB |
| #55 | 79524 | Valgrind error fimplicit_none_2.f90 | memory |

**PR82721:** Likely similar undo/dangling pointer as PR106946. GDB to find
corrupt string source.

**PR109788:** Find Fortran code path passing 64 to shift in `hwint.h:293`.
Add bounds check.

**PR79524:** `valgrind ./f951 <test>` for exact stack trace. Fix at source.

### P4 - Medium Complexity

| GH# | PR | Title | Category |
|-----|----|-------|----------|
| #68 | 95338 | ICE ENTRY + -ff2c | ice |
| #76 | 101760 | ICE deferred-len + OMP target | ice, openmp |
| #79 | 102459 | ICE OMP iterator array ref | ice, openmp |
| #80 | 102596 | ICE OMP task reduction ctor | ice, openmp |

**PR95338:** ENTRY + `-ff2c` calling convention mismatch. Debug `trans-decl.cc`.

**PR101760:** SSA name wrong type for deferred-length char with OMP target.
Debug `trans-openmp.cc` target clause generation.

**PR102459:** Scalarizer wrong for OMP iterator variables. Debug
`trans-openmp.cc` iterator lowering.

**PR102596:** Default constructor fails for OMP task reduction derived type.
Debug `trans-openmp.cc` `clause_default_ctor`.

### P4 - High Complexity

| GH# | PR | Title | Category |
|-----|----|-------|----------|
| #53 | 60576 | FAIL assumed_rank_7.f90 | wrong-code |
| #92 | 110626 | Duplicated finalization | wrong-code |

### P5

| GH# | PR | Title | Category |
|-----|----|-------|----------|
| #52 | 42954 | TARGET_CPP_BUILTINS missing | preprocessor |

---

## Already Patch-Ready (awaiting upstream)

| GH# | PR | Description | Pipeline |
|-----|----|-------------|----------|
| #9 | 102430 | OpenMP linear(array) ICE | on-mailing-list |
| #10 | 103276 | OpenACC ENTER DATA mapping | on-mailing-list |
| #11 | 123252 | OpenACC scalar member | on-bugzilla |
| #12 | 123280 | acc_is_present assumed-shape | on-mailing-list |
| #13 | 96080 | OpenACC pointer semantics | on-mailing-list |
| #14 | 123282 | OpenACC refcount bug | on-bugzilla |

---

## Workflow for Each Fix

```bash
# 1. Branch off upstream
cd gcc && git checkout upstream/master && git checkout -b pr<N>-fix

# 2. Reproduce
cd ../gcc-build/gcc && ./gfortran -B . -c /tmp/reproducer.f90 -o /dev/null

# 3. Debug
gdb -batch -ex run -ex bt --args ./f951 /tmp/reproducer.f90 -quiet

# 4. Fix (minimal change in gcc/fortran/*.cc)

# 5. Rebuild
make -j32 f951

# 6. Verify fix
./gfortran -B . -c /tmp/reproducer.f90 -o /dev/null  # no crash

# 7. Write test: gcc/testsuite/gfortran.dg/pr<N>.f90

# 8. Single test
make check-gfortran RUNTESTFLAGS="dg.exp=pr<N>.f90"

# 9. Full test suite (MANDATORY - 0 FAIL/XPASS required)
make -j32 -k check-gfortran > /tmp/test-pr<N>.log 2>&1
grep -cE "^FAIL|^XPASS" testsuite/gfortran/gfortran.sum

# 10. Commit
cat > /tmp/gcc-commit-msg.txt <<'EOF'
fortran: Short summary [PR<N>]

Description.
EOF
cd ../../gcc
GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/<N>"]' \
  git commit -s -F /tmp/gcc-commit-msg.txt
git gcc-verify HEAD

# 11. Export and push
git format-patch -1 HEAD -o ../pr/<N>/
git push origin pr<N>-fix

# 12. Label issue
gh issue edit <GH#> --add-label patch-ready
```
