# GCC Policy: F2008 Backward Compatibility

## ISO Standard vs GCC Implementation

### ISO Standard Timeline

1. **F2008 Original (2010)**: Structure/array constructors finalized
2. **F2008 Corrigendum 1 (f08/0011)**: Finalization **DELETED** (constructors create values, not variables)
3. **F2018 (2018)**: Maintains Corrigendum 1 behavior (no constructor finalization)

### GCC Policy Decision

When F2008 Corrigendum 1 was published, GCC faced a dilemma:
- Users wrote code from 2010-2018 expecting original F2008 behavior
- Changing `-std=f2008` would break existing code
- Need to guide users to corrected behavior

**GCC Solution**: Implement **backward compatibility mode** for `-std=f2008`

## Implementation Strategy

### Standard Flag Behavior

| Flag | Constructor Finalization | Rationale |
|------|------------------------|-----------|
| `-std=f2008` | ✅ YES (with warnings) | Backward compat for code written 2010-2018 |
| `-std=f2018` | ❌ NO | Correct per F2008 Corrigendum 1 |
| `-std=gnu` (default) | ❌ NO | Correct per F2008 Corrigendum 1 |

### Warning Messages

With `-std=f2008`, system GCC 15.2.1 issues:

```
Warning: The structure constructor at (1) has been finalized.
This feature was removed by f08/0011.
Use -std=f2018 or -std=gnu to eliminate the finalization.
```

This:
1. Alerts users their code uses deprecated behavior
2. Explains WHY it's deprecated (f08/0011)
3. Guides them to use `-std=f2018` or `-std=gnu`

## Code Logic

### `gfc_notification_std(GFC_STD_F2018_DEL)`

This function returns:
- **TRUE** (warning/error): When F2018_DEL is NOT in `allow_std`
- **FALSE** (silent): When F2018_DEL IS in `allow_std`

### Standard Definitions

From `libgfortran.h`:
```c
#define GFC_STD_F2018_DEL	(1<<11)	/* Deleted in F2018 */

// F2008 includes F2018_DEL for backward compat
#define GFC_STD_OPT_F08 (GFC_STD_OPT_F03 | GFC_STD_F2008 | ... | GFC_STD_F2018_DEL)

// F2018 explicitly excludes F2018_DEL
#define GFC_STD_OPT_F18 ((GFC_STD_OPT_F08 | GFC_STD_F2018) & (~GFC_STD_F2018_DEL))
```

### trans-expr.cc Logic

```c
/* Disable finalization for constructors when corrected behavior requested */
else if (gfc_notification_std (GFC_STD_F2018_DEL)
    && (expr2->expr_type == EXPR_STRUCTURE || expr2->expr_type == EXPR_ARRAY))
  expr2->must_finalize = 0;
```

**With `-std=f2008`**:
- `allow_std` includes `GFC_STD_F2018_DEL`
- `gfc_notification_std(GFC_STD_F2018_DEL)` returns FALSE
- `must_finalize = 0` is NOT executed
- Constructors ARE finalized (backward compat)

**With `-std=f2018`** or **`-std=gnu`**:
- `allow_std` does NOT include `GFC_STD_F2018_DEL`
- `gfc_notification_std(GFC_STD_F2018_DEL)` returns TRUE (issues warning)
- `must_finalize = 0` IS executed
- Constructors are NOT finalized (correct per f08/0011)

## Why Intel/NVIDIA Differ

### Intel ifx and NVIDIA nvfortran

Both compilers:
- Do NOT implement backward compat mode for original F2008
- Only implement corrected F2008 (post-corrigendum)
- Do NOT finalize constructors with `-std=f2008` or equivalent

This is a **policy choice**:
- Intel/NVIDIA: "F2008 means F2008 as corrected"
- GCC: "F2008 means F2008 original text for backward compat, with warnings to migrate"

## Migration Path

### For Users

1. **Old code (2010-2018)**: Use `-std=f2008`, expect warnings
2. **New code**: Use `-std=f2018` or `-std=gnu` (default)
3. **Migration**: Fix warnings, switch to `-std=f2018`

### For Implementers

When implementing F2008 Corrigendum changes:
1. Check if existing code relies on old behavior
2. If yes: Implement backward compat mode with warnings
3. Provide migration path to corrected behavior
4. Document policy decision

## Test Suite Implications

### finalize_38a.f90

This test:
- Uses `-std=f2008`
- Expects constructor finalization
- Expects warnings about f08/0011 (test comment: `! { dg-warning "has been finalized" }`)

**Purpose**: Test backward compatibility mode works correctly

### finalize_38.f90 (if exists)

Likely tests corrected behavior with `-std=gnu` or `-std=f2018`:
- NO constructor finalization
- NO warnings

## Conclusion

**GCC's approach is user-friendly**:
- Doesn't break existing code
- Warns about deprecated behavior
- Guides users to correct standard compliance

**Intel/NVIDIA's approach is standard-compliant**:
- Implements corrected standard immediately
- No backward compat burden
- Users must update code

Both are valid engineering choices with different tradeoffs.

## Our Implementation

We now match GCC's backward compatibility policy:
- **`-std=f2008`**: Finalizes constructors (backward compat)
- **`-std=f2018`** / **default**: Does NOT finalize (correct per f08/0011)
- Logic via `gfc_notification_std(GFC_STD_F2018_DEL)`

**Result**: finalize_38a.f90 should now PASS ✅
