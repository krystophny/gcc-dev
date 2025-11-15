# Fortran Finalization Standards History - CORRECTED

## Complete Evolution of Finalization Across Fortran Standards

### FORTRAN 77 (ISO 1539:1980)
- **Finalization support**: ❌ None
- **Finalizers**: Not available

### Fortran 90 (ISO/IEC 1539:1991)
- **Finalization support**: ❌ None
- **Finalizers**: Not available

### Fortran 95 (ISO/IEC 1539-1:1997)
- **Finalization support**: ❌ None
- **Finalizers**: Not available

### Fortran 2003 (ISO/IEC 1539-1:2004)
- **Finalization support**: ✅ **INTRODUCED**
- **FINAL procedures**: Added as part of derived type enhancements
- **When finalization occurs**:
  - End of scope
  - DEALLOCATE statement
  - Intrinsic assignment (for variables)
- **Feature status**: New feature in F2003
- **Function results**: Finalized (function result is a VARIABLE)
- **Structure/array constructors**: Finalized in original F2003

### Fortran 2008 Original (ISO/IEC 1539-1:2010)
- **Finalization support**: ✅ Inherited from F2003
- **Initial standard text**: Structure/array constructors finalized after intrinsic assignment
- **Section**: 4.5.6.3 para 5

### ⚠️ Fortran 2008 Corrigendum 1 (f08/0011) - CRITICAL CHANGE
- **Status**: **DELETED constructor finalization**
- **Interpretation f08/0011**: "How many times are constructed values finalized?"
- **Decision**: Structure and array constructor finalization **PERMANENTLY DELETED**
- **Rationale**: Finalization applies to VARIABLES, not VALUES
  - Function results create VARIABLES → finalized ✅
  - Structure/array constructors create VALUES → NOT finalized ❌
- **Impact**:
  - `a = derived_type(components...)` → constructor result NOT finalized
  - `a = function_returning_derived()` → function result IS finalized

### Fortran 2018 (ISO/IEC 1539-1:2018)
- **Status**: ✅ **NO CHANGE from F2008 Corrigendum 1**
- **Section 7.5.6.3**: "When finalization occurs"
- **Behavior**: Same as F2008 Corrigendum 1
  - Function results finalized (they are variables)
  - Structure/array constructors NOT finalized (they are values)
- **Common misconception**: F2018 did NOT restore constructor finalization

### Fortran 2023 (ISO/IEC 1539-1:2023)
- **Finalization support**: ✅ Unchanged from F2018
- **Section 7.5.6.3**: Maintained F2018 finalization semantics
- **Focus**: Minor corrections and feature additions, no finalization changes

## Key Distinction: Variables vs Values

**Critical concept from F2008 Corrigendum 1:**

> "From a conceptual point of view, it is the value **of a variable** that is finalized,
> not just any data entity. Structure constructors and array constructors just construct
> values, so the thing they construct is not finalized."

### Function Results (VARIABLES)
```fortran
function construct_t(x) result(r)
  type(t) :: r  ! r is a VARIABLE
  ! ... initialize r ...
end function

! Usage:
a = construct_t(x)  ! Function result 'r' IS finalized after assignment
```

### Structure Constructors (VALUES)
```fortran
! Direct structure constructor:
a = t(component1=x, component2=y)  ! Constructor creates a VALUE, NOT finalized

! Via interface (this is actually a function call):
interface t
  module procedure construct_t  ! This is a FUNCTION
end interface

a = t(x)  ! This calls construct_t() → function result → IS finalized
```

## GCC Implementation Strategy

### Behavior Matrix

| Expression Type | Creates | Finalized? | Standard |
|----------------|---------|------------|----------|
| Function result | Variable | ✅ Yes | F2003+ |
| `interface t` → function | Variable | ✅ Yes | F2003+ |
| Structure constructor `t(...)` | Value | ❌ No | F2008 Corr.1+ |
| Array constructor `[...]` | Value | ❌ No | F2008 Corr.1+ |

### Standard Version Behavior

**ALL versions from F2008 onward behave the same:**

| `-std=` flag | Function finalized? | Constructor finalized? |
|-------------|-------------------|----------------------|
| (default) | ✅ Yes | ❌ No |
| `-std=f2003` | ✅ Yes | ✅ Yes (pre-corrigendum) |
| `-std=f2008` | ✅ Yes | ❌ No (post-corrigendum) |
| `-std=f2018` | ✅ Yes | ❌ No |
| `-std=f2023` | ✅ Yes | ❌ No |

### Implementation Logic (trans-expr.cc)

```c
// Line ~13087: Set must_finalize for finalizable RHS expressions
expr2->must_finalize = 1;

// Line ~13092: Pointer function results not finalized
if (EXPR_FUNCTION && is_pointer)
  expr2->must_finalize = 0;

// Line ~13099: Structure/array constructors NOT finalized (F2008 Corr.1+)
if (EXPR_STRUCTURE || EXPR_ARRAY)
  expr2->must_finalize = 0;  // Always disable for constructors

// Line ~8986: Finalize function results
if (EXPR_FUNCTION && must_finalize && finalizable)
  gfc_finalize_tree_expr(...);  // Finalize the function result variable
```

## ISO Standard References

### F2008 Corrigendum 1 Interpretation f08/0011

**Question**: "How many times are constructed values finalized?"

**Answer**: Structure and array constructor entities are NOT finalized.
They create values, not variables. Only variables are finalized.

**Edits**: Deleted paragraphs 5 and 7 from section 4.5.6.3 (F2008).

### Fortran 2018 Section 7.5.6.3 "When finalization occurs"

Maintains the F2008 Corrigendum 1 behavior:
- Function results (variables) are finalized
- Structure/array constructors (values) are NOT finalized

## Testing Strategy

### Multi-Compiler Validation

Test finalization behavior with:
1. **GCC gfortran** (system and patched versions)
2. **Intel ifx** 2025.2+ (excellent F2008+ compliance)
3. **NVIDIA nvfortran** 25.9+ (excellent F2008+ compliance)
4. **NAG Fortran** (excellent standards compliance)
5. **LLVM Flang** (developing F2008+ support)
6. **LFortran** (modern implementation)

### Expected Behavior

For code using **function via interface**:
```fortran
interface t
  module procedure construct_t  ! This is a FUNCTION
end interface

type(t) :: a
a = t(constructor_args)  ! Calls function construct_t()
```

**Expected finalization count**: 2
1. LHS (`a`) finalized before assignment (if `intent(out)` in defined assignment)
2. **Function result finalized after assignment** (result is a variable)

For code using **true structure constructor**:
```fortran
type(t) :: a
a = t(component1=x, component2=y)  ! Direct structure constructor
```

**Expected finalization count**: 1
1. LHS (`a`) finalized before assignment (if `intent(out)` in defined assignment)
2. ❌ Constructor result NOT finalized (creates value, not variable)

## Implementation Status

### PR121472 Fix

This patch implements correct F2008+ finalization behavior:
- Adds finalization of function results (variables) after intrinsic assignment
- Does NOT finalize structure/array constructors (values)
- Fixes ICE when finalizing unevaluated CALL_EXPR for types without allocatable components

### Test Cases

1. **finalize_constructor_1.f90**: Constructor **via interface** (function call) with finalizer
2. **finalize_45.f90**: Constructor **via interface** (function call) with pointer component

Both tests use `interface t` which maps to a FUNCTION, not a direct structure constructor,
so the function result IS finalized.

### Expected Test Results

Full test suite: ~3400 expected passes, 6 expected failures (pre-existing OpenACC TODOs)

## Common Misconceptions - CORRECTED

### ❌ WRONG: "F2018 restored constructor finalization"
**✅ CORRECT**: F2018 did NOT change F2008 Corrigendum 1 behavior.
Constructors remain NOT finalized from F2008 Corrigendum 1 through F2023.

### ❌ WRONG: "Constructor interfaces behave like structure constructors"
**✅ CORRECT**: `interface t` pointing to a function makes `t(...)` a FUNCTION CALL,
not a structure constructor. Function results ARE finalized.

### ❌ WRONG: "Default GCC behavior differs from explicit `-std=f2018`"
**✅ CORRECT**: Default, F2008, F2018, and F2023 all have the SAME finalization behavior
for constructors (not finalized) and functions (finalized).
