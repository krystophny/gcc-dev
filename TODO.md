# GCC Fortran Regression Fix TODO

## PR106946 (#88) - Patch Ready [DONE]

**Status:** PATCH READY. Full `check-gfortran` passed, signed patch exported
and pushed on branch `origin/pr106946-fix` (`d02ccf8946c`).

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
CLASS container from the namespace symtree when it is still present, release
the symbol, and free the component. Non-CLASS components are left for
secondary error reporting. The regression test now covers allocatable and
pointer CLASS declarations plus a valid component followed by a bad one.

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
Verified: commit and patch both contain `Signed-off-by:`.

Then: `gh issue edit 88 --add-label patch-ready`

---

## PR82721 (#56) - Patch Ready [DONE]

**Status:** PATCH READY. Full `check-gfortran` passed, signed patch exported
and pushed on branch `origin/pr82721-fix` (`98a30995f17`).

### Task list

- [x] Task 1: Reproduce the ICE with the minimal duplicate-type testcase.
- [x] Task 1 review: Confirm the failure mode and collect a useful backtrace.
- [x] Task 2: Debug the dangling symbol/symtree path around `reject_statement`.
- [x] Task 2 review: Verify the root cause against the actual cleanup flow.
- [x] Task 3: Implement a minimal fix and add a regression test.
- [x] Task 3 review: Check that the fix is precise and does not mask other errors.
- [x] Task 4: Rebuild and run targeted validation for PR82721.
- [x] Task 4 review: Inspect diagnostics and ensure the ICE is gone.
- [x] Task 5: Run a clean full `check-gfortran`.
- [x] Task 5 review: Check `FAIL`/`XPASS` deltas and confirm no regressions.
- [x] Task 6: Commit, `gcc-verify`, export, push, and update issue `#56`.
- [x] Task 6 review: Verify patch artifact, branch state, and issue metadata.

**Reproducer:**

```fortran
program p
   real :: a, b(4)
   character(len(c)) :: b
end
```

Expected end state:
- user-facing error diagnostic
- no internal compiler error

**Confirmed reproducer path:**

- `MALLOC_PERTURB_=165 gcc-build/gcc/gfortran -B gcc-build/gcc -fsyntax-only`
  on the minimal variant ICEs reliably on unfixed sources.
- Backtrace reaches `find_sym` via `resolve_charlen`, after the duplicate-type
  diagnostic.

**Root cause:** `gfc_match_decl_type_spec` adds new `gfc_charlen` nodes to the
current namespace `cl_list` while parsing `CHARACTER(len(...))`.  If the data
declaration is later rejected, `reject_statement()` undoes symbol-table changes
but does not roll back those fresh `gfc_charlen` nodes.  The stale `len(c)`
expression is then resolved later and walks dangling symtree pointers.

**Current local fix:** `build_sym` drops only the unattached fresh
`gfc_charlen` node created for a rejected duplicate-type declaration, leaving
charlen nodes that are still needed by surviving invalid declarations alone.
The regression test `gfortran.dg/pr82721.f90` sets `MALLOC_PERTURB_` to make
the old crash deterministic.

Patch exported: `pr/82721/0001-fortran-Fix-ICE-after-rejected-CHARACTER-duplicate-d.patch`
Verified: commit and patch both contain `Signed-off-by:`.

---

## PR102459 (#79) - Patch Ready [DONE]

**Status:** PATCH READY. Full `check-gfortran` passed, signed patch exported
and pushed on branch `origin/pr102459-fix` (`dcc53363931b`).

### Task list

- [x] Task 1: Reproduce the OpenMP iterator ICE and inspect the failing clause path.
- [x] Task 1 review: Confirm the crash enters `gfc_conv_scalarized_array_ref`
  with missing scalarizer state.
- [x] Task 2: Debug the reference-shape mismatch in `trans-openmp.cc`.
- [x] Task 2 review: Verify the whole expression is rank-1 even though the first
  `REF_ARRAY` is `AR_ELEMENT`.
- [x] Task 3: Implement the minimal fix and add a regression test.
- [x] Task 3 review: Check that scalar locators still use the reference path.
- [x] Task 4: Rebuild and run direct plus targeted PR102459 validation.
- [x] Task 4 review: Inspect direct `-fsyntax-only` and `-O -S` behavior for
  both `x(j)%a` and `x(j)%a(1)`.
- [x] Task 5: Run a clean full `check-gfortran`.
- [x] Task 5 review: Check merged `gfortran.sum` for `0` `FAIL`/`XPASS`.
- [x] Task 6: Commit, `gcc-verify`, export, push, and update issue `#79`.
- [x] Task 6 review: Verify the signed commit, exported patch footer, branch
  state, and issue metadata.

**Reproducer:**

```fortran
program p
   type t
      integer :: a(2)
   end type
   type(t) :: x(8)
   !$omp task depend (iterator(j=1:8), out:x(j)%a)
   !$omp end task
end
```

Expected end state:
- successful compile
- no internal compiler error

**Root cause:** `gfc_trans_omp_clauses` used
`n->expr->ref->u.ar.type == AR_ELEMENT` to decide between scalar-reference and
array-descriptor lowering.  For `x(j)%a`, the first `REF_ARRAY` is the scalar
base element `x(j)`, but the full expression is still the rank-1 component
array `a`.  That sends an array-valued expression through
`gfc_conv_expr_reference`, which later reaches
`gfc_conv_scalarized_array_ref` with `se->ss == NULL` and ICEs.

**Current local fix:** Choose the lowering path from `n->expr->rank == 0`
instead of the first `REF_ARRAY` kind, so `x(j)%a` goes through
`gfc_conv_expr_descriptor` while true scalars like `x(j)%a(1)` still use the
reference path.  Apply the same change to `gfc_trans_omp_depobj`.  The
regression test `gfortran.dg/pr102459.f90` covers both the original array case
and the scalar control case.

Patch exported: `pr/102459/0001-fortran-Fix-OpenMP-iterator-depend-lowering-for-comp.patch`
Verified: commit and patch both contain `Signed-off-by:`.

---

## PR102596 (#80) - Patch Ready [DONE]

**Status:** PATCH READY. Full `check-gfortran` passed, signed patch exported
and pushed on branch `origin/pr102596-fix` (`aba89bd758f1`).

### Task list

- [x] Task 1: Reproduce the OpenMP task-reduction ICE and inspect the failing hook call.
- [x] Task 1 review: Confirm `gfc_omp_clause_default_ctor` is called with
  `OMP_CLAUSE_TASK_REDUCTION` and `outer == NULL_TREE`.
- [x] Task 2: Debug whether the fix belongs in `omp-low` or the Fortran hook.
- [x] Task 2 review: Verify the first `omp-low` attempt was wrong because
  `build_outer_var_ref` itself has no valid outer source in this path.
- [x] Task 3: Implement the minimal fix and add a regression test.
- [x] Task 3 review: Keep `outer` mandatory for descriptor/alloc-comp cases and
  relax it only for plain scalar allocatables.
- [x] Task 4: Rebuild and run direct plus targeted PR102596 validation.
- [x] Task 4 review: Confirm the reproducer now compiles and targeted DejaGnu passes.
- [x] Task 5: Run a clean full `check-gfortran`.
- [x] Task 5 review: Check merged `gfortran.sum` for `0` `FAIL`/`XPASS`.
- [x] Task 6: Commit, `gcc-verify`, export, push, and update issue `#80`.
- [x] Task 6 review: Verify signed commit, exported patch footer, branch state,
  and issue metadata.

**Reproducer:**

```fortran
program p
  integer, allocatable :: r
  allocate (r)
  r = 0
  !$omp target parallel reduction(task, +:r)
  r = r + 1
  !$omp end target parallel
end
```

Expected end state:
- successful compile
- no internal compiler error

**Root cause:** `omp-low` can legitimately call
`gfc_omp_clause_default_ctor` for an `OMP_CLAUSE_TASK_REDUCTION` allocatable
scalar with `outer == NULL_TREE`.  Plain scalar allocatables only need fresh
storage allocation in that path, but the Fortran hook asserted
unconditionally on `outer != NULL_TREE` and ICEd during `omplower`.

**Current local fix:** Keep requiring `outer` for descriptor-based allocatables
and types with allocatable components, but allow `NULL_TREE` for plain scalar
allocatables that do not actually use the outer reference.  The regression
test `gfortran.dg/pr102596.f90` covers the task-reduction allocatable-scalar
case.

Patch exported: `pr/102596/0001-fortran-Allow-task-reduction-allocatable-scalars-wit.patch`
Verified: commit and patch both contain `Signed-off-by:`.

---

## PR95338 (#68) - Patch Ready [DONE]

**Status:** PATCH READY. Full `check-gfortran` passed, signed patch exported
and pushed on branch `origin/pr95338-fix` (`4ddac5d947e1`).

### Task list

- [x] Task 1: Reproduce the `-O1 -ff2c` mixed-ENTRY ICE and inspect the
  generated master union.
- [x] Task 1 review: Confirm the wrapper returns `real(kind=8)` while the
  shared union still stores `real(kind=4)` for the ENTRY result.
- [x] Task 2: Debug where the mixed-ENTRY union field types are chosen.
- [x] Task 2 review: Verify the ABI mismatch belongs in `trans-types.cc`
  rather than the wrapper-return code in `trans-decl.cc`.
- [x] Task 3: Implement the minimal fix and add a regression test.
- [x] Task 3 review: Keep the change limited to mixed-ENTRY union field typing
  and preserve existing wrapper signatures.
- [x] Task 4: Rebuild and run direct plus targeted PR95338 validation.
- [x] Task 4 review: Check the fresh `-fdump-tree-original` output and confirm
  `master.0.f` now uses `real(kind=8)` for entry `g`.
- [x] Task 5: Run a clean full `check-gfortran`.
- [x] Task 5 review: Check merged `gfortran.sum` for `0` `FAIL`/`XPASS`.
- [x] Task 6: Commit, `gcc-verify`, export, push, and update issue `#68`.
- [x] Task 6 review: Verify signed commit, exported patch footer, branch state,
  and issue metadata.

**Reproducer:**

```fortran
module m
contains
   function f(x)
      integer :: x
      integer :: f
      real :: g
      f = x
      return
   entry g(x)
      g = x
   end
end
program p
   use m
   print *, f(1)
   print *, g(1)
end
```

Expected end state:
- successful compile with `-O1 -ff2c`
- no internal compiler error

**Root cause:** `gfc_get_mixed_entry_union` built each shared union field from
the Fortran result symbol type.  Under `-ff2c`, default `REAL` ENTRY wrappers
return C `double`, so the wrapper for `g` returned `real(kind=8)` while the
master union field stayed `real(kind=4)`.  That left a non-trivial conversion
inside `COMPONENT_REF`, and the GIMPLE verifier rejected the lowered code.

**Current local fix:** Build mixed-ENTRY union fields from the ABI return type
instead of the raw Fortran result symbol type, so default `REAL` ENTRY results
under `-ff2c` contribute a `real(kind=8)` union member.  The regression test
`gfortran.dg/pr95338.f90` covers the original mixed `INTEGER`/`REAL` ENTRY
case under `-O1 -ff2c`.

Patch exported: `pr/95338/0001-fortran-Fix-mixed-ENTRY-union-ABI-under-ff2c-PR95338.patch`
Verified: commit and patch both contain `Signed-off-by:`.

---

## PR120286 (#95) - Patch Ready [DONE]

**Status:** PATCH READY. Full `check-gfortran` passed, signed patch exported
and pushed on branch `origin/pr120286-fix` (`985517a4dcc`).

### Task list

- [x] Task 1: Reproduce the OpenMP crash with a scalar polymorphic pointer in
  `private`/`firstprivate`.
- [x] Task 1 review: Confirm from the `omplower` dump that worker cleanup
  finalizes and frees the shared pointee.
- [x] Task 2: Debug the privatization ctor/dtor path in `trans-openmp.cc`.
- [x] Task 2 review: Verify the problem is misclassification in the
  clause-specific hooks, not a general deep-mapping or runtime refcount bug.
- [x] Task 3: Implement the minimal fix and add a regression test.
- [x] Task 3 review: Keep class-pointer detection local to the ctor/dtor hooks
  so existing OpenMP polymorphic-mapping warnings remain intact.
- [x] Task 4: Rebuild the frontend and run direct plus targeted validation.
- [x] Task 4 review: Re-check both the original reproducer and
  `gomp/polymorphic-mapping-1.f90` after rebuilding `f951`.
- [x] Task 5: Run a clean full `check-gfortran`.
- [x] Task 5 review: Confirm the rebuilt full-suite run finishes with `0`
  `FAIL`/`XPASS`.
- [x] Task 6: Commit, `gcc-verify`, export, push, and update issue `#95`.
- [x] Task 6 review: Verify the signed commit, exported patch footer, branch
  state, and issue metadata.

**Reproducer:**

```fortran
program main
  type foo_t
    integer :: dummy
  end type foo_t
  type fooPtr_t
    class(foo_t), pointer :: p
  end type fooPtr_t
  type fooPtrStack_t
    class(fooPtr_t), allocatable :: list(:)
  end type fooPtrStack_t
  type(fooPtrStack_t) :: x
  class(foo_t), pointer :: ptr
  integer :: n

  allocate (x%list(1))
  allocate (x%list(1)%p)
!$omp parallel do default(none) num_threads(2) private(n, ptr) shared(x)
  do n = 1, 1
    ptr => x%list(n)%p
  end do
!$omp end parallel do
end
```

Expected end state:
- successful compile and run with `-fopenmp`
- no segmentation fault or double free

**Root cause:** `gfc_omp_clause_copy_ctor` and `gfc_omp_clause_dtor` decided
their polymorphic class handling from the lowered tree type alone.  For scalar
class pointers privatized through OpenMP temporaries, that tree type still
looked like a class container, so the hooks took the owned-polymorphic path,
finalized `ptr._data`, and freed the shared pointee on thread exit.

**Current local fix:** Unwrap saved descriptors first and recognize
`__class_*_p` container types locally in those two OpenMP privatization hooks.
Treat those entities as pointer-association-only state there, while leaving
the broader `gfc_is_polymorphic_nonptr` classification unchanged for mapping
warnings and deep-mapping logic.  The regression test
`gfortran.dg/pr120286.f90` covers both the original `private(ptr)` crash and a
`firstprivate(ptr)` association check.

Patch exported: `pr/120286/0001-fortran-Preserve-scalar-class-pointers-in-OpenMP-pri.patch`
Verified: commit and patch both contain `Signed-off-by:`.

---

## Backlog Audit (2026-03-10)

**Confirmed locally still reproducing with dedicated validation:**

- `PR110877` (`#101`) - assignment from a polymorphic array dummy argument
  drops allocatable components on `g = f` while `allocate(g, source=f)`
  preserves them.  Current WIP fix reproduces the expected `T/T` behavior but
  regresses `class_transformational_1.f90`, so it is not patch-ready yet.
- `PR120723` (`#96`) - with local `openacc.mod`, `!$acc enter data
  attach(scalar)` still ICEs with `unexpected pointer mapping node`.

**Quick compile check did not reproduce immediately; re-verify before spending
fix time:**

- `PR101760` (`#76`) - quick `-fopenmp` compile did not ICE.

**Needs dedicated re-check / special setup:**

- `PR109788` (`#91`) - requires the precise UB-triggering path, likely with
  sanitizer instrumentation or exact IPA conditions.
- `PR79524` (`#55`) - needs Valgrind/ASan confirmation on the invalid-code path.
- `PR120723` (`#96`) - needs `openacc.mod` / OpenACC-capable setup for a real
  compile check.
- `PR110626` (`#92`) - runtime/finalization behavior issue.
- `PR60576` (`#53`) - runtime/ASan descriptor overflow issue.
- `PR42954` (`#52`) - architectural preprocessor gap, not a quick ICE check.

## Remaining Open Issues (by priority, then complexity)

### P3 - High Priority

| GH# | PR | Title | Complexity | Category |
|-----|----|-------|------------|----------|
| #96 | 120723 | ICE attach(scalar) OpenACC | medium | ice, openacc |

**PR120723:** Debug `trans-openmp.cc` map clause generation for scalar attach.
Should generate `GOMP_MAP_ATTACH`, not pointer mapping. Test with offload build.

### P4 - Low Complexity

| GH# | PR | Title | Category |
|-----|----|-------|----------|
| #91 | 109788 | UB: shift exponent 64 | runtime UB |
| #55 | 79524 | Valgrind error fimplicit_none_2.f90 | memory |

**PR109788:** Find Fortran code path passing 64 to shift in `hwint.h:293`.
Add bounds check.

**PR79524:** `valgrind ./f951 <test>` for exact stack trace. Fix at source.

### P4 - Medium Complexity

| GH# | PR | Title | Category |
|-----|----|-------|----------|
| #76 | 101760 | ICE deferred-len + OMP target | ice, openmp |
| #101 | 110877 | Dummy class assignment loses alloc comps | wrong-code, polymorphism |

**PR101760:** SSA name wrong type for deferred-length char with OMP target.
Debug `trans-openmp.cc` target clause generation.

**PR110877:** Reuse the dummy-array class container for scalarized element copy
without perturbing unrelated class-transformational lowering.  Current WIP
fixes the reproducer but regresses `class_transformational_1.f90`.

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
| #56 | 82721 | CHARACTER duplicate declaration ICE | patch-ready |
| #68 | 95338 | ENTRY + -ff2c ICE | patch-ready |
| #79 | 102459 | OMP iterator component array ICE | patch-ready |
| #80 | 102596 | OMP task reduction ctor ICE | patch-ready |
| #95 | 120286 | OpenMP polymorphic pointer privatization | patch-ready |

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
