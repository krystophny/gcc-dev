# Bug 96080: OpenACC runtime library routines vs Fortran pointer semantics

- **URL:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96080
- **Status:** FIXED by PR 123280 patch
- **Related:** PR 123280 (same root cause)

## Summary

`acc_is_present()` and other OpenACC runtime routines fail to detect data mapped
via Fortran pointers. The spec was thought to be ambiguous about pointer vs target
semantics, but the actual issue was a gfortran codegen bug.

## Root Cause

Same as PR 123280: `acc_is_present_array_h` in libgomp/openacc.f90 had `contiguous`
on its assumed-rank dummy argument. Fortran pointers have descriptors, and when
passed to a `contiguous` dummy, gfortran creates a temporary copy. The lookup then
checks the copy's address instead of the actual mapped data.

## Test Results

| Test | nvfortran | GCC (unfixed) | GCC (PR123280 fix) |
|------|-----------|---------------|---------------------|
| Map target, check via pointer | PASS | FAIL | PASS |
| Map pointer directly | PASS | FAIL | PASS |
| Map target + attach pointer | PASS | FAIL | PASS |
| Pointer argument in subroutine | PASS | FAIL | PASS |
| Pointer as assumed-shape | PASS | FAIL | PASS |

## Fix

The PR 123280 patch (removing `contiguous` from `acc_is_present_array_h`) fixes
this bug as well. No additional changes needed.

## OpenACC Spec Clarification

The spec ambiguity noted in the bugzilla discussion is a red herring. The actual
behavior should be:
- Runtime routines operate on the **target data** (dereferenced pointer)
- This matches directive behavior
- nvfortran implements this correctly

GCC's failure was not a spec interpretation issue but a codegen bug that caused
temporary copies to be created and checked instead of the actual data.

## References

- [NVIDIA Forum: OpenACC Fortran Pointers](https://forums.developer.nvidia.com/t/openacc-fortran-pointers/135604)
- [Flang: OpenACC Descriptor Management](https://releases.llvm.org/20.1.0/tools/flang/docs/OpenACC-descriptor-management.html)
