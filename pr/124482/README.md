# Bug 124482: Segfault in resolve_cyclic_derived_type (use-after-free)

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124482
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/102
- **Branch:** `pr124482-fix`
- **Status:** MERGED upstream (`d8b00bf2e1514cd132a9febaa9849ab46cd316f5`, 2026-03-15)

## Summary

The test `gfortran.dg/pr106946.f90` (added by our PR 106946 fix, commit
r16-8021-g0d0fbb0a01e) segfaults on Solaris/SPARC.  This is a GCC 16 regression,
reported between compiler
snapshots 20260311 and 20260312, but reproducible on x86_64 with valgrind.

## Root Cause

CLASS containers are **shared** between components of the same class type and
attributes.  The PR106946 error-recovery cleanup (decl.cc:7018-7022) freed
the CLASS container symbol when removing a failed component, not checking
whether a previously committed component in the same type still references it.

Example from `pr106946.f90`, type `t3`:

```fortran
type :: t3
    class(w), allocatable :: ok       ! committed, uses __class_w_a
    class(w), allocatable :: x y      ! fails at 'y', cleanup frees __class_w_a
end type
```

After cleanup, `ok->ts.u.derived` is a dangling pointer.  Any later access
(`check_component` in `parse_derived`, `resolve_cyclic_derived_type`) reads
freed memory.  On SPARC this crashes; on x86_64 it silently reads stale data.

## Fix

Before freeing a CLASS container during error recovery, scan the remaining
component list for other references to the same container.  If shared, skip
the `gfc_delete_symtree` / `gfc_release_symbol`; the container stays in the
namespace and is cleaned up during normal namespace destruction.

Also NULL `c->ts.u.derived` before calling `gfc_free_component` to avoid
chasing into shared state.

File changed: `gcc/fortran/decl.cc`

## Validation

- Valgrind: 0 errors (was 25 before fix)
- DejaGnu `pr106946.f90`: 4/4 expected passes
- Full `check-gfortran`: 0 FAIL, 0 XPASS

## Patch Artifact

- GCC commit: `d8b00bf2e1514cd132a9febaa9849ab46cd316f5` (merged upstream on 2026-03-15)
- Fork branch commit: `d0863254583` (on `origin/pr124482-fix`)
- Exported patch:
  `pr/124482/0001-fortran-Fix-use-after-free-in-CLASS-component-error-.patch`
