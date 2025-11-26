# PR107721 - Array constructor type-spec lost during constant folding

## Bug Summary

GCC drops the explicit type specification on array constructors when elements
are parenthesized or nested.  Expressions like `[integer :: ([1.0])] ** 2`
return REAL instead of INTEGER because constant folding evaluates elements
with their literal type rather than the declared type-spec.

This also affects character constructors with concatenation:
`[character(16) :: 'a', 'b'] // '|'` fails with "Different CHARACTER lengths"
because elements are not padded to 16 characters before the CONCAT operation.

Intel ifx, NVIDIA nvfortran, and LLVM flang all handle these cases correctly
per Fortran 2018 R781/R782.

## Reproducer

```fortran
print *, [integer :: ([1.0])] ** 2  ! Should print INTEGER 1, not REAL 1.0
print *, [real :: ([2])] ** 2       ! Should print REAL 4.0, not INTEGER 4
```

## Root Cause

The type-spec IS preserved during parsing.  Two issues caused incorrect behavior:

1. **Parenthesized expressions create EXPR_OP nodes** - `([1.0])` becomes an
   INTRINSIC_PARENTHESES operation.  Type conversion in `check_constructor_type()`
   was applied to the EXPR_OP rather than its simplified contents.

2. **Character arrays not resolved before CONCAT** - Elements retained original
   lengths instead of being padded to the type-spec length before concatenation.

## Solution

The fix calls existing functions at the right places - no new algorithms needed:

**arith.cc `eval_intrinsic()`:**
- Call `gfc_check_constructor_type()` on array operands before operations
- Call `gfc_resolve_character_array_constructor()` before CONCAT operations
- Preserve `ts.u.cl` in `reduce_binary_*()` result arrays

**array.cc:**
- Call `gfc_simplify_expr()` in `check_constructor_type()` to handle `([1.0])`
- Propagate type-spec recursively to nested array constructors

Total: ~35 lines in arith.cc, ~48 lines in array.cc (net).

## Test Results

- 74,442 passes, 343 expected failures, 0 regressions
- All bugzilla cases verified (Comments #0, #7, #11, #12, #14, #17)
- Matches Intel ifx and NVIDIA nvfortran behavior exactly

## Files

- `0001-fortran-Honor-array-constructor-type-spec-during-fol.patch` - Final patch
- `reproducer.f90` - Original bug reproducer from Comment #0
- `bugzilla.txt` - Notes from GCC Bugzilla

## Status: Ready for upstream submission

Branch `pr107721-typespec` contains a single commit rebased on `upstream/master`.
