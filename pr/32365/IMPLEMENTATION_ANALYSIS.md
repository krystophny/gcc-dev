# Implementation Analysis - GCC Bug 32365

## Deep Dive: Error Generation in GCC Fortran Parser

### Root Cause Identified

The issue is exactly as described in the 2007 Bugzilla discussion. There are **two separate error handling mechanisms** in GCC's Fortran parser:

1. **`verify_st_order()`** - Provides excellent error messages
2. **`unexpected_statement()`** - Provides generic "Unexpected X statement" messages

The problem is that **`verify_st_order()` is not called consistently**, particularly in the executable section.

### Code Analysis

#### 1. The Good: `verify_st_order()` Function

**Location:** `gcc/fortran/parse.cc:3316-3418`

**Excellent Error Message:**
```c
/* Line 3413-3415 */
gfc_error ("%s statement at %C cannot follow %s statement at %L",
           gfc_ascii_statement (st),
           gfc_ascii_statement (p->last_statement), &p->where);
```

**Example Output:** `"INTEGER statement at X cannot follow ASSIGNMENT statement at Y"`

**Called From:**
- `parse_spec()` - Specification section parsing ✅
- `parse_progunit()` - Program unit declaration parsing ✅

#### 2. The Problem: `parse_executable()` Function

**Location:** `gcc/fortran/parse.cc:6662-7168`

**Issue:** Does **NOT** call `verify_st_order()`

**Current Flow:**
```c
/* Lines 6719-6723 */
case_executable:
  accept_statement (st);
  if (close_flag == 1)
    return ST_IMPLIED_ENDDO;
  break;

/* ... many more cases ... */

/* Lines 7139-7141 - THE PROBLEM */
unexpected_statement (st);  // Generic error!
reject_statement ();
st = next_statement ();
```

**Generic Error Message:** `unexpected_statement()` function:
```c
/* Line 3254 */
gfc_error ("Unexpected %s statement at %C", gfc_ascii_statement (st));
```

#### 3. The Specific Cases Affected

**Specification Statements (`case_decl`):**
```c
/* Line 1983-1984 */
#define case_decl case ST_ATTR_DECL: case ST_COMMON: case ST_DATA_DECL: \
  case ST_EQUIVALENCE: case ST_NAMELIST: case ST_STATEMENT_FUNCTION:
```

**OpenMP Declaration Statements (`case_omp_decl`):**
- `!$OMP THREADPRIVATE`
- Other OpenMP specification directives

### Why This Happens

1. **Two-stage parsing:**
   - **Specification stage:** Calls `verify_st_order()` ✅
   - **Executable stage:** Uses `parse_executable()` - no `verify_st_order()` ❌

2. **Design assumption:**
   - Specification statements shouldn't appear in executable section
   - When they do, they fall through to `unexpected_statement()`

3. **Missing validation:**
   - `parse_executable()` doesn't validate statement ordering
   - Only checks if statement is executable or not

## Implementation Options

### Option 1: Minimal Fix (Recommended)
**Difficulty:** EASY | **Risk:** LOW | **Impact:** HIGH

**Approach:** Add better error messages in `parse_executable()`

**Implementation:**
```c
/* In parse_executable(), replace lines 7135-7141 */

case_decl:
  gfc_error ("%s statement cannot appear after the first executable statement at %C",
             gfc_ascii_statement (st));
  reject_statement ();
  break;

case_omp_decl:
  gfc_error ("%s statement cannot appear after the first executable statement at %C",
             gfc_ascii_statement (st));
  reject_statement ();
  break;

default:
  unexpected_statement (st);  // Keep existing for truly unexpected statements
  break;
```

**Benefits:**
- Intel-style error messages
- Minimal code changes
- Low risk of breaking existing functionality
- Direct fix for the reported issue

### Option 2: Call `verify_st_order()` from `parse_executable()`
**Difficulty:** MEDIUM | **Risk:** MEDIUM | **Impact:** HIGH

**Approach:** Integrate `verify_st_order()` into executable parsing

**Implementation:**
```c
/* At the beginning of parse_executable() */
static st_state exec_state;
static bool exec_state_initialized = false;

if (!exec_state_initialized) {
  verify_st_order (&exec_state, ST_NONE, false);
  exec_state_initialized = true;
}

/* For each statement before accept_statement() */
if (!verify_st_order (&exec_state, st, false)) {
  reject_statement ();
  st = next_statement ();
  continue;
}
```

**Benefits:**
- Consistent error messaging everywhere
- Leverages existing excellent code

**Risks:**
- Complex integration
- May affect executable statement parsing flow
- Higher risk of breaking existing functionality

### Option 3: Enhanced `unexpected_statement()`
**Difficulty:** EASY | **Risk:** VERY LOW | **Impact:** MEDIUM

**Approach:** Make `unexpected_statement()` smarter

**Implementation:**
```c
static void
unexpected_statement (gfc_statement st)
{
  /* Check if this is a specification statement in executable part */
  if (in_exec_part && (st == ST_DATA_DECL || st == ST_COMMON ||
                       st == ST_OMP_THREADPRIVATE || /* other spec statements */)) {
    gfc_error ("%s statement cannot appear after the first executable statement at %C",
               gfc_ascii_statement (st));
  } else {
    gfc_error ("Unexpected %s statement at %C", gfc_ascii_statement (st));
  }

  reject_statement ();
}
```

## Recommended Implementation Plan

### Phase 1: Quick Win (Option 1)
1. **Add specific cases for specification statements** in `parse_executable()`
2. **Use Intel-style error message:** "X statement cannot appear after the first executable statement"
3. **Test with existing reproducers** to ensure improved messages
4. **Run test suite** to verify no regressions

### Phase 2: Consistency (Optional Future Enhancement)
1. **Consider Option 2** for complete consistency
2. **Evaluate performance impact**
3. **Ensure no edge case regressions**

## Technical Assessment

### Difficulty Level: **EASY**
- Clear code locations identified
- Simple conditional logic required
- Minimal changes to existing flow
- Well-understood problem domain

### Risk Assessment: **LOW**
- Changes are additive, not modifying existing logic
- Easy to test and validate
- Clear success criteria (error message improvement)
- Can be easily rolled back if issues arise

### Expected Impact: **HIGH**
- **User Experience:** Dramatically improved error messages
- **Educational Value:** Teaches Fortran statement ordering
- **Competitive Parity:** Matches Intel compiler quality
- **Maintenance:** Minimal ongoing maintenance burden

## Specific Implementation Locations

### Primary Files to Modify:
- **`gcc/fortran/parse.cc`** - Lines 7135-7141 (parse_executable function)

### Test Cases to Validate:
- **`pr/32365/simple_spec.f90`** - Variable declarations
- **`pr/32365/common_test.f90`** - COMMON statements
- **`pr/32365/simple_omp.f90`** - OpenMP threadprivate

### Success Criteria:
1. Error message: `"X statement cannot appear after the first executable statement"`
2. No test suite regressions
3. Consistent behavior across all specification statement types

## Conclusion

This is a **classic low-hanging fruit** enhancement that provides:
- **High user value** with **low implementation risk**
- **Clear path to implementation** with minimal code changes
- **Immediate educational benefits** for Fortran developers
- **Competitive parity** with other modern compilers

The implementation directly addresses the 15+ year old Bug 32365 and brings GCC's error messages in line with modern compiler user experience expectations.