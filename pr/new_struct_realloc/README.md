# OpenACC: Illegal memory access with derived type component in repeated alloc/dealloc cycle

## Status
- **Confirmed**: Bug in GCC 16.0.0 (trunk)
- **Bugzilla PR**: TBD

## Summary

When a derived type with an allocatable component is used in OpenACC parallel
regions, GCC produces an illegal memory access on iteration 2 of an
allocate/map/unmap/deallocate cycle. The bug is ORDER-DEPENDENT: it only
triggers when a parallel loop NOT using the struct runs BEFORE a parallel
loop that DOES use the struct.

## Root Cause Analysis

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

### Technical Analysis

**Tree dump comparison** reveals the issue is in how `GOMP_MAP_STRUCT` mappings
are handled across parallel regions:

**Failing case (non-struct loop first):**
```
Loop 1: map(to:w1 [pointer set]) map(to:w2 [pointer set])
Loop 2: map(to:w1 [pointer set]) map(struct:s) map(to:s.c [pointer set]) map(attach:s.c.data)
```

**Passing case (struct loop first):**
```
Loop 1: map(to:w1 [pointer set]) map(struct:s) map(to:s.c [pointer set]) map(attach:s.c.data)
Loop 2: map(to:w1 [pointer set]) map(to:w2 [pointer set])
```

**Asymmetric enter/exit data mappings:**
- Enter data: `map(struct:s [len: 1])` - creates struct mapping
- Exit data: NO corresponding `map(release:s)` - struct NOT released!

This asymmetry causes the struct `s` to remain in the device mapping table
after `exit data`. On iteration 2:

1. Host deallocates and reallocates arrays (may get swapped addresses)
2. `enter data` creates new device allocations for `s%c`, `w1`, `w2`
3. First parallel loop runs (w1, w2 only) - works fine
4. Second parallel loop attempts to set up struct mapping for `s`
5. The stale struct mapping causes incorrect pointer attachment
6. Kernel accesses invalid device memory → CRASH

### Compute-Sanitizer Output

```
Invalid __global__ read of size 8 bytes
    at MAIN__$_omp_fn$1+0x...
    Access to 0x7f...400 is out of bounds
    and is inside the nearest allocation at 0x7f...000 of size 1.031 bytes
```

The "1.031 bytes" allocation size is suspicious - indicates corrupted/stale
device pointer metadata.

### Address Swapping Evidence

When arrays are deallocated and reallocated, the memory allocator may return
addresses in different order:

```
Iteration 1: w1=0xBD00, w2=0xC110, s%c=0xBCB0
Iteration 2: w1=0xC110, w2=0xBD00, s%c=0xBCB0  (w1/w2 swapped!)
```

The s%c address stays the same, but the struct mapping's internal state
becomes inconsistent with the new device allocations.

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
| gfortran | 16.0.0 20251223 | host | PASS |
| nvfortran | 25.1 | nvidia | PASS |

## Build Commands

```bash
# gfortran with nvptx (crashes)
/opt/gcc16/bin/gfortran -O3 -fopenacc -foffload=nvptx-none mre.f90 -o mre
LD_LIBRARY_PATH=/opt/gcc16/lib64 ./mre

# nvfortran (passes)
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

## Verified Code Locations

### Asymmetric Struct Mapping - Root Cause

The bug is caused by intentional asymmetric handling of GOMP_MAP_STRUCT:

**1. Enter data - struct IS created (gimplify.cc:12680):**
```c
enum gomp_map_kind str_kind = GOMP_MAP_STRUCT;
// ... creates map(struct:s [len: 1]) clause
```

**2. Exit data - struct IS REMOVED (gimplify.cc:15949-15955):**
```c
if ((OMP_CLAUSE_MAP_KIND (c) == GOMP_MAP_STRUCT
     || OMP_CLAUSE_MAP_KIND (c) == GOMP_MAP_STRUCT_UNORD)
    && (code == OMP_TARGET_EXIT_DATA || code == OACC_EXIT_DATA))
  {
    remove = true;  // <-- INTENTIONALLY REMOVED
    goto end_adjust_omp_map_clause;
  }
```

**3. Runtime skips struct on exit (oacc-mem.c:1372-1378):**
```c
case GOMP_MAP_STRUCT:
case GOMP_MAP_STRUCT_UNORD:
  /* Skip the 'GOMP_MAP_STRUCT' itself, and use the regular processing
     for all its entries.  This special handling exists for GCC 10.1
     compatibility; afterwards, we're not generating these no-op
     'GOMP_MAP_STRUCT's anymore.  */
  break;  // <-- NO CLEANUP
```

This was introduced in GCC 10.1 (2020-06-05, Thomas Schwinge & Julian Brown) with the
changelog: "Remove 'GOMP_MAP_STRUCT' mapping from OpenACC 'exit data' directives."

The design assumption was that GOMP_MAP_STRUCT is a "no-op" that doesn't need cleanup.
However, in repeated alloc/dealloc cycles with multiple parallel loops, this creates
stale struct mapping state that corrupts pointer attachments on iteration 2+.

### Potential Fix Locations (Clean, Targeted, Minimal)

| Location | Fix | Complexity | Risk | YAGNI/SRP |
|----------|-----|------------|------|-----------|
| gimplify.cc:15949-15955 | Remove special case that strips GOMP_MAP_STRUCT | LOW | LOW | Best |
| oacc-mem.c:1372-1378 | Add struct state cleanup instead of skip | MEDIUM | LOW | OK |
| trans-openmp.cc | Add explicit struct release for exit_data | MEDIUM | MEDIUM | Precedent (PR123252) |
| target.c:4524-4525 | Handle struct in gomp_exit_data | HIGH | HIGH | Avoid |

### Recommended Fix (Based on Our Fix Patterns)

**Option 1: gimplify.cc (Preferred)** - Remove lines 15949-15955 that strip
GOMP_MAP_STRUCT from exit_data. This 2020 "optimization" assumed struct is a
"no-op" but it creates asymmetric state that corrupts mappings in cycles.

**Option 2: trans-openmp.cc (Precedent from PR123252)** - Following the
pattern from PR123252 where we added symmetric enter/exit handling for scalar
fields, we could ensure GOMP_MAP_STRUCT is generated for exit_data the same
way it is for enter_data. However, this may duplicate gimplify.cc logic.

**Why Option 1 is best:**
1. **Minimal**: Single condition removal (4 lines)
2. **Targeted**: Directly addresses the documented asymmetry
3. **YAGNI**: No new infrastructure, just removes special-case code
4. **SRP**: Lets existing runtime cleanup handle struct properly
5. **Reversible**: Easy to test - just comment out the condition

**Evidence from PR123252**: Our fix for scalar field mapping explicitly
handles BOTH enter_data and exit_data symmetrically. The same principle
should apply to GOMP_MAP_STRUCT - symmetric handling prevents stale state.

### Safety Analysis

| Concern | Risk | Reason |
|---------|------|--------|
| Memory leaks | NONE | GOMP_MAP_STRUCT doesn't allocate device memory |
| Runtime crash | NONE | Runtime already skips GOMP_MAP_STRUCT on exit (GCC 10.1 compat) |
| Refcount issues | LOW | Members handle their own refcounts |

The runtime (oacc-mem.c:1372-1378) was designed to skip GOMP_MAP_STRUCT on exit
gracefully. If the fix doesn't fully resolve the issue, oacc-mem.c may also
need modification to perform actual struct state cleanup.

## Files of Interest

| File | Line | Purpose |
|------|------|---------|
| `gcc/gimplify.cc` | 12680 | Creates GOMP_MAP_STRUCT for struct mappings |
| `gcc/gimplify.cc` | 15949-15955 | **BUG**: Removes GOMP_MAP_STRUCT from exit_data |
| `libgomp/oacc-mem.c` | 1117-1130 | Runtime processes struct on enter |
| `libgomp/oacc-mem.c` | 1372-1378 | Runtime skips struct on exit (no cleanup) |
| `gcc/fortran/trans-openmp.cc` | - | Frontend translation (not the bug location) |

## System Information

- OS: Linux 6.18.2-2-cachyos (x86_64)
- GPU: NVIDIA GeForce RTX 5060 Ti
- Driver: 590.48.01
- CUDA: 13.0
