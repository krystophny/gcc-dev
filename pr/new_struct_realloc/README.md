# OpenACC: Illegal memory access with derived type component in repeated alloc/dealloc cycle

## Status
- **Confirmed**: Bug in GCC 16.0.0 (trunk)
- **Fixed**: libgomp/oacc-mem.c refcount handling
- **Bugzilla PR**: TBD

## Summary

When a derived type with an allocatable component is used in OpenACC parallel
regions, GCC produces an illegal memory access on iteration 2 of an
allocate/map/unmap/deallocate cycle. The bug is ORDER-DEPENDENT: it only
triggers when a parallel loop NOT using the struct runs BEFORE a parallel
loop that DOES use the struct.

## Root Cause

### The Problem: Refcount Double-Counting

Fortran allocatable arrays generate TO_PSET + POINTER mapping groups. When
`goacc_map_vars` creates the device mapping, it adds multiple list entries
that can point to the SAME splay tree key (the descriptor address):

```
list[0] = descriptor key (TO_PSET)
list[1] = same descriptor key (POINTER)
```

`gomp_map_vars_internal` sets `refcount = 2` (one per list entry).

In `goacc_enter_data_internal` (oacc-mem.c:1284-1289), the original code
incremented `dynamic_refcount` for EVERY list entry:

```c
for (j = 0; j < tgt->list_count; j++)
  if (tgt->list[j].key && !tgt->list[j].is_attach)
    tgt->list[j].key->dynamic_refcount++;
```

This results in: `refcount=2`, `dynamic_refcount=2`.

But `exit_data` only sends ONE RELEASE mapping per descriptor, so only
decrements by 1. This leaves: `refcount=1`, `dynamic_refcount=1`.

The mapping is never removed from the splay tree. On iteration 2:
1. Host deallocates and reallocates arrays (may get different addresses)
2. `enter_data` creates new device allocations
3. Stale mapping with old device addresses corrupts pointer attachment
4. Kernel accesses invalid device memory -> CRASH

### Trigger Conditions (ALL required)

1. Derived type with allocatable component (`s%c`)
2. Additional allocatable arrays (`w1`, `w2`)
3. TWO separate parallel loops where:
   - First loop does NOT reference the derived type component
   - Second loop DOES reference the derived type component
4. Repeated allocate/deallocate cycle (crashes on iteration 2)

### Key Observation: Loop Order Matters

| First Loop Uses | Second Loop Uses | Result |
|-----------------|------------------|--------|
| w1, w2 | w1, s%c | **CRASH** on iter 2 |
| w1, s%c | w1, w2 | PASS |
| w1, w2, s%c | (single loop) | PASS |

## The Fix

In `goacc_enter_data_internal`, track duplicate keys and:
1. Only increment `dynamic_refcount` once per UNIQUE key
2. Decrement `refcount` for duplicates to compensate

```c
splay_tree_key prev_key = NULL;
for (size_t j = 0; j < tgt->list_count; j++)
  {
    n = tgt->list[j].key;
    if (n && !tgt->list[j].is_attach)
      {
        if (n != prev_key)
          {
            n->dynamic_refcount++;
            prev_key = n;
          }
        else
          {
            /* Duplicate key: adjust refcount down to compensate
               for gomp_map_vars_internal counting it twice.  */
            if (n->refcount != REFCOUNT_INFINITY
                && n->refcount != REFCOUNT_ACC_MAP_DATA
                && n->refcount > 1)
              n->refcount--;
          }
      }
  }
```

## Minimal Reproducer (37 lines)

```fortran
module m
    use, intrinsic :: iso_fortran_env, only: dp => real64
    type :: t
        real(dp), allocatable :: c(:)
    end type
end module

program p
    use m
    implicit none
    type(t) :: s
    real(dp), allocatable :: w1(:,:,:), w2(:,:,:)
    integer :: i, iter

    do iter = 1, 3
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

## Compilers Tested

| Compiler | Version | Backend | Result |
|----------|---------|---------|--------|
| gfortran | 16.0.0 20251223 | nvptx | **FAIL** on iter 2 |
| gfortran | 16.0.0 20251223 | nvptx + fix | **PASS** |
| gfortran | 16.0.0 20251223 | host | PASS |
| nvfortran | 25.1 | nvidia | PASS |

## Build Commands

```bash
# gfortran with nvptx (crashes without fix)
/opt/gcc16/bin/gfortran -O3 -fopenacc -foffload=nvptx-none mre.f90 -o mre
LD_LIBRARY_PATH=/opt/gcc16/lib64 ./mre

# nvfortran (passes - reference behavior)
nvfortran -O3 -acc=gpu mre.f90 -o mre_nv
./mre_nv

# gfortran host fallback (passes)
ACC_DEVICE_TYPE=host LD_LIBRARY_PATH=/opt/gcc16/lib64 ./mre
```

## Workarounds

1. **Swap loop order**: Put struct-using loop FIRST
2. **Combine into single loop**: Access all variables in one parallel region
3. **Use host fallback**: `ACC_DEVICE_TYPE=host`

## Related PRs

This is a NEW bug, separate from:
- PR123252 (scalar field mapping on enter data)
- PR103276 (pointer mapping for pass-by-ref)

## Previous Incorrect Hypothesis

Initial analysis incorrectly identified GOMP_MAP_STRUCT stripping in
gimplify.cc as the root cause. While gimplify.cc:15949-15955 does strip
GOMP_MAP_STRUCT from OpenACC exit_data (introduced in commit 1afc4672561a),
this is NOT the actual bug. The real issue is the refcount double-counting
in oacc-mem.c for TO_PSET + POINTER descriptor mappings.

## Files of Interest

| File | Line | Purpose |
|------|------|---------|
| `libgomp/oacc-mem.c` | 1284-1289 | **BUG**: Refcount double-counting for duplicate keys |
| `libgomp/target.c` | - | gomp_map_vars_internal sets initial refcount |

## System Information

- OS: Linux 6.18.2-2-cachyos (x86_64)
- GPU: NVIDIA GeForce RTX 5060 Ti
- Driver: 590.48.01
- CUDA: 13.0
