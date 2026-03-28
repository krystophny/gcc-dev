# Bug 102333: invalid `PROCEDURE` statement accepted

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102333
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/78
- **Status:** patch on Bugzilla as attachment `64064`; branch `origin/pr102333-fix` at `0cbbde19fd43`

## Summary

The original report was an ICE in `gfc_generate_function_code` for a
contained function declaring `procedure(f)` where the host function `f`
returns an unlimited polymorphic pointer or allocatable result.

That crash no longer reproduces on current trunk. A non-ICE testcase was
committed on 2026-03-12 as `r16-8026-g8a0a1a0c7b1`.

Bugzilla was reopened on 2026-03-28 because the front end still accepted
invalid contained `PROCEDURE` declarations. The patch on `origin/pr102333-fix`
rejects the original pointer-result reproducer and the simplified comment-2
variants while leaving existing valid procedure-pointer uses alone.

## Remaining Work

The remaining upstream work is review and commit. The fix is semantic
validation in `resolve_procedure_interface`, not crash handling or codegen.
It rejects contained `procedure(f)` declarations that use the host function
`f` as an interface when that host function has an unlimited polymorphic
pointer or allocatable result.

## Local Validation

With the local development compiler after the fix:

```bash
gcc-build/gcc/gfortran -B gcc-build/gcc -c pr/102333/reproducer.f90
```

this now fails with the expected frontend error.

Additional validation completed on 2026-03-28:

```bash
cd gcc-build/gcc && make -j32 check-gfortran RUNTESTFLAGS='dg.exp=pr102333*.f90'
make -C gcc-build/gcc -j32 -k check-gfortran
make -C gcc-build -j32 check-target-libgomp-fortran
```

The focused PR102333 tests, full `check-gfortran`, and full
`check-target-libgomp-fortran` all completed with `0 FAIL`, `0 XPASS`, and
the libgomp rerun also with `0 UNRESOLVED`.
