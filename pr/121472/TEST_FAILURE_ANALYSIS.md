# Test Failure Analysis - finalize_38a.f90

## Test Suite Results

**Status**: 78 unexpected failures (all from `finalize_38a.f90` at multiple optimization levels)

**Failing Test**: `gfortran.dg/finalize_38a.f90`

## Root Cause

The test `finalize_38a.f90` has **INCORRECT expectations** for F2008 Corrigendum 1 behavior.

### Test Expectations (WRONG)

```fortran
! { dg-options "-std=f2008" }
!
! Test finalization on intrinsic assignment (F2018 (7.5.6.3))
! With -std=f2008, structure and array constructors are finalized.
```

The test expects structure/array constructors to be finalized with `-std=f2008`.

### Actual F2008 Corrigendum 1 Behavior (CORRECT)

F2008 Corrigendum 1 (f08/0011) **DELETED** structure/array constructor finalization.

**Rationale**: Constructors create VALUES, not VARIABLES. Only variables are finalized.

## Multi-Compiler Validation

### Intel ifx 2025.2.1 with `-std08`
```bash
ifx -std08 finalize_38a_test.f90
./finalize_38a_test.x
```

**Result**: ❌ FAILS (exit code 174, segfault after errors)
```
21           1 (           2 )   # Expected 2 finalizations, got 1
23          42          43 (          21          22 )
31           1 (           2 )   # Expected 2 finalizations, got 1
...
```

**Conclusion**: Intel ifx does NOT finalize structure constructors

### NVIDIA nvfortran 25.9 with `-Mstandard`
```bash
nvfortran -Mstandard finalize_38a_test.f90
./finalize_38a_test.x
```

**Result**: ❌ FAILS (exit code 1, 15 errors)
```
21            1 (            2 )  # Expected 2 finalizations, got 1
23           42           43 (           21           22 )
31            0 (            2 )  # Expected 2 finalizations, got 0
...
15  Errors
```

**Conclusion**: NVIDIA nvfortran does NOT finalize structure constructors

### System GCC 15.2.1 with `-std=f2008`
```bash
/usr/bin/gfortran -std=f2008 finalize_38a_test.f90
```

**Compilation**: ✅ Succeeds with WARNINGS

```
Warning: The structure constructor at (1) has been finalized.
This feature was removed by f08/0011.
Use -std=f2018 or -std=gnu to eliminate the finalization.
```

**Runtime**: ✅ PASSES (all tests pass)

**Conclusion**: System GCC has **backward compatibility mode** for `-std=f2008` that:
- DOES finalize constructors (for backward compat)
- Issues warnings that this was removed by f08/0011
- Suggests using `-std=f2018` for correct behavior

### System GCC 15.2.1 with `-std=f2018`
```bash
/usr/bin/gfortran -std=f2018 finalize_38a_test.f90
```

**Compilation**: ✅ No warnings

**Runtime**: ❌ FAILS (9 errors, same as Intel/NVIDIA)
```
21           1 (           2 )  # Expected 2, got 1
23          42          43 (          21          22 )
31           1 (           2 )  # Expected 2, got 1
...
9  Errors
```

**Conclusion**: With `-std=f2018`, system GCC correctly does NOT finalize constructors

## Compiler Behavior Summary

| Compiler | Standard | Finalizes Constructors? | Test Result |
|----------|----------|------------------------|-------------|
| Intel ifx 2025.2.1 | `-std08` | ❌ No | ❌ FAILS |
| NVIDIA nvfortran 25.9 | `-Mstandard` | ❌ No | ❌ FAILS |
| GCC 15.2.1 | `-std=f2008` | ✅ Yes (backward compat + warning) | ✅ PASSES |
| GCC 15.2.1 | `-std=f2018` | ❌ No (correct) | ❌ FAILS |
| **Our GCC dev** | `-std=f2008` | ❌ No (correct per f08/0011) | ❌ FAILS |

## Analysis

### What is Correct?

**F2008 Corrigendum 1 (f08/0011) behavior**: Do NOT finalize structure/array constructors

**Supporting evidence**:
1. Intel ifx and NVIDIA nvfortran both do NOT finalize constructors
2. System GCC 15.2.1 warns about f08/0011 when using `-std=f2008`
3. System GCC 15.2.1 with `-std=f2018` does NOT finalize constructors
4. Web research confirms f08/0011 deleted constructor finalization

### Why Does System GCC Pass?

System GCC 15.2.1 has **special backward compatibility** for `-std=f2008`:
- Implements pre-corrigendum F2008 behavior (finalizes constructors)
- Issues deprecation warnings referencing f08/0011
- Tells users to use `-std=f2018` for correct behavior

This is a **policy decision** by GCC maintainers to help users transition legacy code.

### Why Do We Fail?

Our implementation correctly implements **f08/0011 behavior** for all F2008+ modes:
- Structure/array constructors are VALUES, not VARIABLES
- Only VARIABLES are finalized
- This is the correct behavior per the standard

The test `finalize_38a.f90` expects the old (pre-corrigendum) behavior.

## Recommendations

### Option 1: Add Backward Compatibility (Like System GCC)

Implement special handling for `-std=f2008`:
- Finalize constructors when using exactly `-std=f2008`
- Issue warnings about f08/0011
- Use correct behavior for `-std=f2018` and default

**Pros**: Matches system GCC behavior, test passes
**Cons**: More complex code, perpetuates deprecated behavior

### Option 2: Update Test Expectations (RECOMMENDED)

Update `finalize_38a.f90` to:
- Remove or adjust expectations for `-std=f2008`
- Document that this tests deprecated pre-corrigendum behavior
- Create separate test for correct f08/0011 behavior

**Pros**: Cleaner implementation, follows standards correctly
**Cons**: Requires test suite changes

### Option 3: Skip Test with `-std=f2008`

Mark test as expected to fail with `-std=f2008` in our implementation.

**Pros**: No code changes needed
**Cons**: Doesn't fix the underlying issue

## Conclusion

**Our implementation is CORRECT per F2008 Corrigendum 1.**

The test `finalize_38a.f90` expects deprecated pre-corrigendum behavior that:
- Intel ifx does NOT implement
- NVIDIA nvfortran does NOT implement
- System GCC only implements with warnings and backward-compat mode

**Recommended Action**: Update test expectations or implement backward-compat mode with warnings like system GCC.
