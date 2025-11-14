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

## Process plan
1. **Characterize the fold path.** Run the new testsuite reproducer and capture
   dumps from `arith.cc` (`reduce_binary_ac`, `reduce_unary_ac`, and
   `gfc_convert_constant`) to prove exactly where the constructor elements lose
   their declared type once parentheses are present. Preserve short traces in
   this directory for future reference.
2. **Instrument folding locally.** Add temporary diagnostics (behind
   `-fdump-tree-original` or simple `fprintf` guarded by `flag_debug`) that log
   the constructor `ts` pointer before each reduction. Remove these once we
   have confirmation.
3. **Implement conversions when folding.** Introduce a helper that clones each
   constructor element and passes it through `gfc_convert_constant` right
   before arithmetic. Guard it so constructors without a `type_spec` remain
   untouched and implied-do loops are handled element by element.
4. **Extend regression coverage.** Grow the testsuite series
   (`array_constructor_typespec_*.f90`) to cover nested parentheses,
   implied-do loops, and COMPLEX literals once the integer/real coverage is
   stable. Each test should follow the `stop n` style and rely on semantic
   differences such as `range()` so we are not comparing textual output.
5. **History check.** After the fix is stable, bisect GCC 10→11 to document
   the introduction point and include that data in the eventual commit message
   and release notes.

## Minimal testsuite reproducer
- File: `gcc/gcc/testsuite/gfortran.dg/array_constructor_typespec_1.f90`
- Mechanism: compares the decimal range returned by `range()` for expressions
  with and without parentheses around the constructor (plain literals and
  implied-do loops) and checks the storage size of COMPLEX constructors. Bad
  compilers flip INTEGER⇄REAL ranges once parentheses introduce nested array
  constructors (`stop 1-4`) and shrink COMPLEX storage down to the REAL size
  (`stop 5`).
- Targeted run:
  ```bash
  cd /home/ert/code/gcc-dev/gcc-build/gcc
  make check-gfortran RUNTESTFLAGS="array_constructor_typespec_1.f90"
  ```
  (The file currently lives only on branch `pr107721-typespec`; wire it into
  `dg.exp` when we post the fix.)
- Follow-up: consider adding CLASS(*)/implied-do chains that mix scalars and
  array constructors once the main patch lands upstream, and wire the file
  into `dg.exp` before running the full `check-gfortran` sweep.

## Cross-compiler status (array_constructor_typespec_1.f90)
| Compiler | Command | Result |
| --- | --- | --- |
| GNU Fortran trunk (`gcc-build/gcc/gfortran -B gcc-build/gcc`) | `gcc-build/gcc/gfortran -B gcc-build/gcc -std=f2018 array_constructor_typespec_1.f90` | **Fails** with `STOP 1` |
| GNU Fortran 15.2.1 (`/usr/bin/gfortran`) | `/usr/bin/gfortran -std=f2018 array_constructor_typespec_1.f90` | **Fails** with `STOP 1` |
| LLVM flang-new 21.1.5 | `/usr/bin/flang-new -std=f2018 array_constructor_typespec_1.f90` | Pass |
| Intel ifx 2025.2.1 | `source /opt/intel/oneapi/setvars.sh && ifx -std18 array_constructor_typespec_1.f90` | Pass |
| NVIDIA nvfortran 25.9-0 | `/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran array_constructor_typespec_1.f90` | Pass |
| LFortran (HEAD) | `lfortran array_constructor_typespec_1.f90` | Pass |

Only GCC misbehaves, and both the system and in-tree compilers fail the
`range()` parity checks immediately, so the testcase is stable and exposes the
regression without depending on textual output.

## Files
- `reproducer.f90`: standalone reproducer.
- `bugzilla.txt`: curated notes from GCC Bugzilla (#107721) with references to
  key comments and suspected root causes.
