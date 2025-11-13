# PR107721 – Lost typespec when parentheses wrap array constructors

## Summary
GCC drops the explicit type specification on array constructors when the
constructor expression is wrapped in parentheses (or nested constructors such
as `((/2,3/))`). When constant folding evaluates expressions like
`[integer :: ([1.0])] ** 2`, the elements keep their original literal type, so
integer constructors produce reals, real constructors produce integers, and so
on. Intel ifx 2025.2.1, LLVM flang-new 21.1.5, and NVIDIA nvfortran 25.9-0 all
preserve the declared type, so GCC alone violates the Fortran 2018 rules
(R781/R782 and R1023) that require every constructor element to be converted to
the specified type before further evaluation.

## Reproducer
`reproducer.f90` is the program from comment #0. Build/run from repo root:

```bash
/usr/bin/gfortran -o pr/107721/reproducer.system.x pr/107721/reproducer.f90
./pr/107721/reproducer.system.x
```

Observed output (GNU Fortran 15.2.1 20250813):
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

Additional reference runs (all correct):

* LLVM flang-new 21.1.5

```
 *** Expect integer:
 1
 1
 *** Expect real:
 4.
 4.
 *** Expect complex:
 (9.,0.)
 (9.,0.)
```

* NVIDIA nvfortran 25.9-0

```
 *** Expect integer:
            1
            1
 *** Expect real:
    4.000000
    4.000000
 *** Expect complex:
 (9.000000,0.000000)
 (9.000000,0.000000)
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

## Plan of attack
1. **Nail down scope.** Drive the reproducer plus variants such as
   `((/2,3/))`, chained parentheses, and implied-do loops through the compiler
   while tracing which simplification/reduction helpers run. Capture that data
   in a log so we know exactly which functions must enforce the type-spec.
2. **Instrument constant folding.** Add temporary diagnostics in `arith.cc`
   (`reduce_binary_ac`, `reduce_unary_ac`, exponentiation helpers, and
   `gfc_convert_constant`) that print when a constructor carries `type_spec`
   but its elements reach arithmetic without conversion. Remove the tracing
   once we confirm the path and keep notes in this directory.
3. **Prototype conversions in folding.** Update the reduction helpers to call
   `gfc_convert_constant (ctor->value, ctor->ts)` (or equivalent) before each
   literal participates in arithmetic. Reuse existing scalar-conversion code so
   KIND/LEN semantics stay correct, and ensure constructors without a type-spec
   remain untouched.
4. **Regression and conformance tests.** Add a new
   `gfortran.dg/array_constructor_typespec_*.f90` test covering INTEGER/REAL/
   COMPLEX with and without parentheses, nested constructors, and implied-do
   loops inside exponentiation and addition. Run
   `make -C gcc-build/gcc check-gfortran RUNTESTFLAGS="dg.exp=..."` plus the
   full suite before posting patches, and compare runtime output with flang,
   ifx, and nvfortran binaries for tangible proof.
5. **History check.** Bisect GCC 10→11 once the fix is ready so we can document
   when the regression entered trunk and mention it in the eventual commit
   message or release notes.

## Files
- `reproducer.f90`: standalone reproducer.
- `bugzilla.txt`: curated notes from GCC Bugzilla (#107721) with references to
  key comments and suspected root causes.
