# Bug 124482: SEGV in resolve_cyclic_derived_type (regression on Solaris/SPARC)

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124482
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/102
- **Status:** NEW (upstream, unconfirmed)

## Summary

The test `gfortran.dg/pr106946.f90` (added by our PR 106946 fix, commit
r16-8021-g0d0fbb0a01e) SEGVs on Solaris/SPARC (both 32-bit and 64-bit)
starting between compiler snapshots 20260311 and 20260312.

The crash is in `resolve_cyclic_derived_type` at `CLASS_DATA(c)->ts.u.derived`
in `gcc/fortran/resolve.cc`.

## Suspected Regressing Commit

Commit `a8b70a96c34` (r16-8082) "Fortran: gfortran PDT component access
[PR122696]" by Paul Thomas.  However, Paul notes that his change only affects
associate names with generic function targets, neither of which appear in
`pr106946.f90`.

## Analysis

The test contains invalid CLASS component declarations inside derived types:
```fortran
class(u), allocatable :: a b  ! missing comma
```

Our PR 106946 fix cleans up orphaned CLASS container symbols on error recovery.
`resolve_cyclic_derived_type` iterates components and checks `class_ok` before
dereferencing `CLASS_DATA(c)`.  If a leftover component has `class_ok` set but
invalid CLASS data, the dereference crashes.

This may be SPARC-specific (different memory layout / NULL behavior) or a
latent issue exposed by timing/GC changes in the PDT commit.  Needs Solaris/
SPARC access to reproduce.

## Reproducer

Same as `gcc/testsuite/gfortran.dg/pr106946.f90`:
```
f951 pr106946.f90 -quiet
```

## Relationship to Our Work

Our PR 106946 fix (Pattern 8 in CLAUDE.md) was merged as r16-8021.
This regression is filed against our test.  We need to verify whether the
crash reproduces on x86_64 and, if SPARC-specific, get access to a Solaris/
SPARC environment to debug.
