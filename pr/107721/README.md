# PR107721 – Lost typespec when parentheses wrap array constructors

## Summary
GCC drops the explicit type specification on array constructors when the
constructor expression is wrapped in parentheses (or nested constructors such
as `((/2,3/))`). When constant folding evaluates expressions like
`[integer :: ([1.0])] ** 2`, the elements keep their original literal type, so
integer constructors produce reals, real constructors produce integers, and so
on. Intel ifx preserves the declared type, so the result matches the Fortran
standard (Fortran 2018, R781/R782 and R1023).

## Reproducer
`reproducer.f90` is the program from comment #0. Build/run from repo root:

```bash
/usr/bin/gfortran -o pr/107721/reproducer.system.x pr/107721/reproducer.f90
./pr/107721/reproducer.system.x
```

Observed output (GNU Fortran 15.2.1 20250405):
```
 *** Expect integer:
           1
   1.00000000
 *** Expect real:
   4.00000000
           4
 *** Expect complex:
             (9.00000000,0.00000000)
           9
```

Reference behavior (Intel ifx 2025.2.1):
```
 *** Expect integer:
           1
           1
 *** Expect real:
   4.000000
   4.000000
 *** Expect complex:
 (9.000000,0.0000000E+00)
 (9.000000,0.0000000E+00)
```

## Diagnosis so far
* Parser (`gfc_match_array_constructor`) recognizes type-specs but stores the
  information only in a local `seen_ts`. Recursive matches invoked by
  `match_array_cons_element` reset `seen_ts`, so conversions are skipped once
  expressions contain nested array constructors or parentheses (comment #8).
* The type still exists on the outer constructor node, but constant folding in
  `arith.cc` (`reduce_binary_ac` and friends) iterates over constructor entries
  without inserting conversions to the declared type, so elements get evaluated
  with their literal type (comment #9).
* Simplifying `([1.0])` down to `[1.0]` would also avoid the issue but breaks
  for deeper nesting like `((([1.0])))` unless the simplifier strips an
  arbitrary number of `INTRINSIC_PARENTHESES` nodes (comment #5).

## Next steps
1. Confirm whether the regression began in GCC 11 when ac-value parsing was
   refactored; bisect to identify the exact change.
2. Prototype a fix in either `arith.cc` (insert conversions when reducing
   constructors with a type-spec) or `gfc_match_array_constructor` (propagate
   `seen_ts` and force an implicit `convert` on nested constructors).
3. Extend testing:
   * `((/2,3/))` (comment #7)
   * Combined implied-do loops and nested parentheses
   * Constant expressions where array constructors appear on both operands of
     `reduce_*` helpers (addition, multiplication, exponentiation).
4. Once a candidate fix exists, add a regression test under
   `gfortran.dg/array_constructor_typespec_*.f90` verifying INTEGER/REAL/
   COMPLEX cases both with and without parentheses.

## Files
- `reproducer.f90`: standalone reproducer.
- `bugzilla.txt`: curated notes from GCC Bugzilla (#107721) with references to
  key comments and suspected root causes.

