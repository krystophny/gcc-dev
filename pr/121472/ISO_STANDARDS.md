# ISO Fortran Standards Reference for PR121472

## Primary Standard: ISO/IEC 1539-1:2018 (Fortran 2018)

### Section 7.5.6.3 - When finalization occurs

**Key requirement for PR121472:**

Function results (including elemental function results) SHALL be finalized
exactly once after assignment completes, before the result temporary goes
out of scope.

**Standard text (paraphrased):**
- Function results are VARIABLES
- Variables are finalized when they go out of scope
- After intrinsic assignment, function result temps go out of scope
- Therefore: function result → assign → finalize → deallocate

**Application to finalize_55.f90:**
```fortran
array(i) = elemental_func()
```
- elemental_func() creates function result (VARIABLE)
- Result assigned to array(i)
- Result finalized exactly once
- Result deallocated

**Compliance requirement:**
- ✅ ONE finalization per function result
- ❌ NOT multiple finalizations per result
- ❌ NOT zero finalizations

## Evolution of Finalization Across Standards

### FORTRAN 77 through Fortran 95
- **Finalization**: Not available
- No FINAL procedures

### Fortran 2003 (ISO/IEC 1539-1:2004)
- **INTRODUCED**: FINAL procedures
- **Function results**: Finalized (results are variables)
- **Structure constructors**: Finalized in original F2003

### Fortran 2008 Corrigendum 1 (f08/0011)
- **CRITICAL CHANGE**: Deleted structure/array constructor finalization
- **Rationale**: Finalization applies to VARIABLES, not VALUES
  - Function results → VARIABLES → finalized ✅
  - Structure constructors → VALUES → NOT finalized ❌
- **Interpretation**: "How many times are constructed values finalized?"
- **Decision**: Constructor finalization permanently deleted

### Fortran 2018 (ISO/IEC 1539-1:2018)
- **NO CHANGE** from F2008 Corrigendum 1
- Function results finalized (variables)
- Structure/array constructors NOT finalized (values)

### Fortran 2023
- **NO CHANGE** to finalization rules
- Same behavior as F2018

## GCC Compliance Status for PR121472

### Current Status: ❌ NON-COMPLIANT

**Issue:** Over-finalization of elemental function results
- **Expected**: 1 finalization per function result
- **Actual**: Multiple finalizations (per-element + array-temp + descriptor)
- **Test case**: finalize_55.f90 shows counter=12 (expected 6→16)

### Reference Compiler Compliance

**Intel ifx 2025.2.1:**
- ✅ STANDARD-COMPLIANT
- finalize_55.f90: correct count (16 total)

**NVIDIA nvfortran 25.9:**
- ✅ STANDARD-COMPLIANT
- finalize_55.f90: correct count (16 total)

**System gfortran 15.2.1:**
- ✅ STANDARD-COMPLIANT
- finalize_55.f90: correct count (16 total)

**Custom gfortran (development):**
- ❌ NON-COMPLIANT
- finalize_55.f90: incorrect count (12 at first checkpoint)

## Function Results vs Structure Constructors

**IMPORTANT DISTINCTION:**

### Function Interface (finalize_45.f90)
```fortran
interface t
  module procedure construct_t
end interface

subroutine test()
  type(t) :: x
  x = t(myname)  ! Calls FUNCTION construct_t
end subroutine
```
- `t(myname)` invokes FUNCTION `construct_t`
- Function result is a VARIABLE
- ✅ MUST be finalized per ISO §7.5.6.3

### Structure Constructor
```fortran
subroutine test()
  type(t) :: x
  x = t(components...)  ! Direct structure constructor
end subroutine
```
- `t(components...)` is a VALUE (not variable)
- ❌ NOT finalized (per F2008 Corrigendum 1)

## Implementation Requirements

To achieve ISO/IEC 1539-1:2018 Section 7.5.6.3 compliance:

1. **Track function result temps explicitly**
   - Use temp_finalizable flag in gfc_ss_info
   - Mark temps that hold function results

2. **Finalize at temp teardown**
   - ONE finalization call per temp
   - NOT per-element in scalarized loops
   - Check temp_finalizable before finalizing

3. **Avoid duplicate finalization**
   - Don't finalize per-element AND array-temp
   - Choose ONE location based on temp type
   - Use metadata to make informed decision

4. **Verify with reference compilers**
   - Intel ifx
   - NVIDIA nvfortran
   - System gfortran (recent version)

## Key ISO References

- **ISO/IEC 1539-1:2018** Section 7.5.6.3 - Primary requirement
- **ISO/IEC 1539-1:2010** Corrigendum 1 (f08/0011) - Constructor finalization deleted
- **ISO/IEC 1539-1:2004** Section 4.5.6 - Original finalization introduction

## Verification Protocol

1. Cite ISO standard section in commit message
2. Document expected vs actual behavior
3. Mark compliance status explicitly
4. Test against 2+ reference compilers
5. Verify finalization counts match reference behavior
6. Document any deviations as NON-COMPLIANT bugs
