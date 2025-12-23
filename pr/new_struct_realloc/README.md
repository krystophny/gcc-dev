# OpenACC: Illegal memory access with derived type allocatable component

## Status
- **Confirmed**: Bug in GCC 16.0.0 (trunk and patched)
- **Bugzilla PR**: TBD

## Summary

When a derived type with an allocatable component is used in OpenACC data regions
alongside other allocatable arrays, GCC produces an illegal memory access on the
second iteration of an allocate/map/unmap/deallocate cycle.

## Minimal Reproducer (29 lines)

```fortran
module m
    use, intrinsic :: iso_fortran_env, only: dp => real64
    type :: t
        real(dp), allocatable :: c(:)
    end type
end module

program p
    use m
    type(t) :: s
    real(dp), allocatable :: w1(:,:,:), w2(:,:,:)
    integer :: i, iter

    do iter = 1, 3
        print *, iter
        allocate(s%c(8), w1(8,8,0:1), w2(8,8,0:1))
        !$acc enter data create(s%c, w1, w2)
        !$acc parallel loop present(w1, w2)
        do i = 1, 8
            w2(1,i,0) = w1(1,i,0)
        end do
        !$acc parallel loop present(w1, s%c)
        do i = 1, 8
            s%c(i) = w1(1,i,0)
        end do
        !$acc exit data delete(w1, w2, s%c)
        deallocate(w1, w2, s%c)
    end do
end program
```

## Behavior

- **Iteration 1**: Completes successfully
- **Iteration 2**: Crashes with illegal memory access

```
libgomp: cuStreamSynchronize error: an illegal memory access was encountered
```

## Key Requirements for Bug

All of these are required to trigger the crash:
1. Derived type with allocatable component (`s%c`)
2. Two additional allocatable arrays (`w1`, `w2`)
3. Two separate parallel loops accessing different combinations
4. Repeated allocate/deallocate cycle (crashes on iteration 2)

## Compilers Tested

| Compiler | Version | Result |
|----------|---------|--------|
| gfortran | 16.0.0 (trunk) | FAIL on iter 2 |
| gfortran | 16.0.0 (PR123252 patched) | FAIL on iter 2 |
| nvfortran | 25.1 | PASS |

## Build Commands

```bash
# gfortran (crashes on iter 2)
gfortran -O3 -fopenacc -foffload=nvptx-none mre.f90 -o mre_gcc
./mre_gcc

# nvfortran (passes)
nvfortran -O3 -acc=gpu mre.f90 -o mre_nv
./mre_nv
```

## Notes

This is a separate bug from PR123252 (struct remapping). The PR123252 fix does
not resolve this issue.
