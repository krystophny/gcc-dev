# GCC Bugzilla Submission

## Title
[OpenACC] Illegal memory access with derived type component in repeated alloc/dealloc cycle (order-dependent)

## Component
fortran

## Version
16.0

## Severity
normal

## Keywords
openacc, wrong-code

## Target
nvptx-none

## Summary

When a derived type with an allocatable component is used in OpenACC parallel
regions alongside other allocatable arrays, GCC produces an illegal memory
access on the second iteration of an allocate/map/unmap/deallocate cycle.

The bug is ORDER-DEPENDENT: it only triggers when a parallel loop that does
NOT use the struct component runs BEFORE a parallel loop that DOES use the
struct component. Swapping the loop order makes the code work correctly.

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

        !$acc parallel loop present(w1, w2)      ! Loop 1: no struct
        do i = 1, 8
            w2(1,i,0) = w1(1,i,0)
        end do

        !$acc parallel loop present(w1, s%c)     ! Loop 2: uses struct
        do i = 1, 8
            s%c(i) = w1(1,i,0)
        end do

        !$acc exit data delete(w1, w2, s%c)
        deallocate(w1, w2, s%c)
    end do
end program
```

## Build and Run

```bash
gfortran -O3 -fopenacc -foffload=nvptx-none mre.f90 -o mre
./mre
```

## Expected Behavior

All three iterations complete successfully.

## Actual Behavior

Iteration 1 completes, iteration 2 crashes:
```
libgomp: cuStreamSynchronize error: an illegal memory access was encountered
```

## Key Finding: Loop Order Matters

| First Loop Uses | Second Loop Uses | Result |
|-----------------|------------------|--------|
| w1, w2 | w1, s%c | **CRASH** on iter 2 |
| w1, s%c | w1, w2 | PASS |
| w1, w2, s%c | (single loop) | PASS |

Simply swapping the order of the two parallel loops makes the bug disappear.

## Root Cause Analysis

Using `-fdump-tree-omplower`, the failing case shows asymmetric struct mapping:

**Enter data generates:**
```
map(struct:s [len: 1]) map(to:s.c [pointer set]) map(alloc:s%c data) map(attach:s.c.data)
```

**Exit data generates:**
```
map(release:s.c [pointer set]) map(release:s%c data) map(detach:s.c.data)
```

Note: `map(struct:s)` is created on enter but NO corresponding `map(release:s)`
on exit. This is caused by gimplify.cc:15949-15955 which intentionally removes
GOMP_MAP_STRUCT from exit_data clauses (introduced in GCC 10.1, 2020-06-05).

**The code causing asymmetry (gimplify.cc:15949-15955):**
```c
if ((OMP_CLAUSE_MAP_KIND (c) == GOMP_MAP_STRUCT
     || OMP_CLAUSE_MAP_KIND (c) == GOMP_MAP_STRUCT_UNORD)
    && (code == OMP_TARGET_EXIT_DATA || code == OACC_EXIT_DATA))
  {
    remove = true;  // GOMP_MAP_STRUCT removed from exit_data
    goto end_adjust_omp_map_clause;
  }
```

**Original commit** `1afc4672561a41dfbf4e3f2c1f35f7a5b7a20339` (2020-05-20)
by Thomas Schwinge & Julian Brown:

```
[OpenACC 'exit data'] Strip 'GOMP_MAP_STRUCT' mappings

These are not itself necessary for OpenACC 'exit data' directives, and are
skipped over (now) in libgomp.  We might as well not emit them to start with,
in line with the equivalent OpenMP directive.
```

The assumption was that GOMP_MAP_STRUCT is purely a "grouping marker" with no
persistent state. However, on enter_data it creates struct mapping state in
the runtime splay tree, and without the corresponding struct on exit_data,
this state isn't properly cleaned up in repeated alloc/dealloc cycles.

**Runtime handling (oacc-mem.c:1372-1378):**
```c
case GOMP_MAP_STRUCT:
case GOMP_MAP_STRUCT_UNORD:
  /* Skip the 'GOMP_MAP_STRUCT' itself... This special handling exists
     for GCC 10.1 compatibility; afterwards, we're not generating these
     no-op 'GOMP_MAP_STRUCT's anymore.  */
  break;  // NO CLEANUP
```

**Why loop order matters:**

Failing case (non-struct loop first):
- Loop 1 runs with w1, w2 only - no struct mapping interaction
- Loop 2 tries to set up struct mapping for s
- Stale struct state from iteration 1 corrupts pointer attachment

Passing case (struct loop first):
- Loop 1 sets up struct mapping first - establishes correct state
- Loop 2 runs with w1, w2 only - doesn't touch struct mapping
- Struct state happens to be valid for next iteration

## compute-sanitizer Output

```
Invalid __global__ read of size 8 bytes
    at MAIN__$_omp_fn$1+0x...
    Access to 0x7f...400 is out of bounds
    and is inside the nearest allocation at 0x7f...000 of size 1.031 bytes
```

The "1.031 bytes" allocation size indicates corrupted/stale device pointer
metadata in the mapping table.

## Address Behavior

Memory allocator may return swapped addresses on reallocation:
```
Iteration 1: w1=0xBD00, w2=0xC110
Iteration 2: w1=0xC110, w2=0xBD00  (swapped)
```

The struct address stays the same, but the mapping state becomes inconsistent.

## Compilers Tested

| Compiler | Version | Backend | Result |
|----------|---------|---------|--------|
| gfortran | 16.0.0 20251223 | nvptx | FAIL on iter 2 |
| gfortran | 16.0.0 20251223 | host | PASS |
| nvfortran | 25.1 | nvidia | PASS |

## Workarounds

1. Swap loop order (put struct-using loop first)
2. Combine into single parallel loop accessing all variables
3. Use host fallback (ACC_DEVICE_TYPE=host)

## System Information

- OS: Linux 6.18.2-2-cachyos (x86_64)
- GPU: NVIDIA GeForce RTX 5060 Ti
- Driver: 590.48.01
- CUDA: 13.0

## Proposed Fix

The minimal fix is to remove the special case in gimplify.cc that strips
GOMP_MAP_STRUCT from exit_data (lines 15949-15955). This restores symmetric
enter/exit handling and lets the runtime properly clean up struct mappings.

**Patch sketch:**
```diff
--- a/gcc/gimplify.cc
+++ b/gcc/gimplify.cc
@@ -15949,11 +15949,6 @@ gimplify_adjust_omp_clauses (...)
-	  if ((OMP_CLAUSE_MAP_KIND (c) == GOMP_MAP_STRUCT
-	       || OMP_CLAUSE_MAP_KIND (c) == GOMP_MAP_STRUCT_UNORD)
-	      && (code == OMP_TARGET_EXIT_DATA || code == OACC_EXIT_DATA))
-	    {
-	      remove = true;
-	      goto end_adjust_omp_map_clause;
-	    }
```

This change:
1. Restores symmetric GOMP_MAP_STRUCT handling for enter/exit data
2. Allows runtime to properly clean up struct mapping state
3. Follows the principle from PR123252 where symmetric handling prevents stale state

**Safety**: The runtime (oacc-mem.c:1372-1378) already handles GOMP_MAP_STRUCT
on exit by skipping it (for GCC 10.1 compatibility). GOMP_MAP_STRUCT doesn't
allocate device memory, so there's no risk of memory leaks. If this fix is
insufficient, oacc-mem.c may also need to perform actual struct state cleanup.

## Files of Interest

| File | Line | Purpose |
|------|------|---------|
| gcc/gimplify.cc | 12680 | Creates GOMP_MAP_STRUCT for struct mappings |
| gcc/gimplify.cc | 15949-15955 | **BUG LOCATION**: Removes GOMP_MAP_STRUCT from exit_data |
| libgomp/oacc-mem.c | 1117-1130 | Runtime processes struct on enter |
| libgomp/oacc-mem.c | 1372-1378 | Runtime skips struct on exit (no cleanup) |
| gcc/fortran/trans-openmp.cc | - | Frontend translation (generates clauses) |
