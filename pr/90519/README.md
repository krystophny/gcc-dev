# GCC PR90519 – FINAL + recursive allocatable ICE

**Status:** ✅ COMPLETED — Patch `0001-fortran-Fix-ICE-and-self-assignment-bugs-with-recurs.patch`
has been validated locally (see compile log below) and is ready for upstream
submission.

This directory tracks the reproducer, investigation notes, and fixes for
[GCC Bug 90519](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=90519):
an internal compiler error when a derived type has

1. a recursive allocatable component of the same type, and
2. a FINAL procedure (either directly or via a non-allocatable component).

## Test Results

### Intel ifx 2025.2.1
- Status: PASS
- Compiles without errors

### Dev gfortran (2025-11-13 validation)
- Status: PASS
- Command:
  ```
  ./gcc-build/gcc/gfortran -B ./gcc-build/gcc \
    -L ./gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
    -Wl,-rpath,$PWD/gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
    -c pr/90519/finalizer_min.f90
  ```
- Output: (no diagnostics, object file produced)

## Reproducing

1. Build the in-tree compiler once (`../gcc/configure … && make`).
2. From the repo root run:

   ```bash
   ./gcc-build/gcc/gfortran -B ./gcc-build/gcc \
     -L ./gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
     -Wl,-rpath,$(pwd)/gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
     -c bugs/90519/finalizer_min.f90
   ```

   The current trunk ICEs in `gimplify_call_expr` because the compiler tries to
   call the FINAL wrapper via the function result variable instead of via the
   procedure pointer stored in the vtable.

## Root cause

- `generate_finalization_wrapper` builds the helper function `__final_<type>`
  and stores it in the vtable’s `_final` procedure pointer component.
- The helper is declared as a FUNCTION and `final->result` is set to `final`
  (the implicit Fortran “result equals function name” rule).
- When the front end later creates an expression for `_final`'s initializer,
  it calls `gfc_lval_expr_from_sym (final)`. Because the result symbol and the
  procedure symbol are the same, the resolver treats the expression as a
  variable reference (the function’s result) instead of as a procedure designator.
- During translation this expression collapses to the address of the implicit
  result variable (`__result___final_*`). The gimplifier then sees a
  `CALL_EXPR` whose callee has INTEGER type instead of FUNCTION/METHOD type and
  aborts with the tree-check ICE reported in PR90519.

## Fix plan

1. Give each generated FINAL wrapper its own artificial result symbol
   (`__result_<type>`), distinct from the procedure symbol.
2. Keep the wrapper’s return type as-is (still INTEGER(4)), but now references
   to `__final_<type>` no longer alias the result variable and the resolver
   correctly marks the initializer as `BT_PROCEDURE`.
3. Add regression tests to `gcc/testsuite/gfortran.dg`:
   - `finalizer_recursive_alloc_1.f90`: compile-only module reproducer.
   - `finalizer_recursive_alloc_2.f90`: runtime test that exercises nested
     recursive components and verifies finalizers actually fire.

## Files

- `finalizer_min.f90` – ultra-minimal module that ICEs on current trunk.
- `README.md` – this document.

Use `make -C bugs finalizer` (the top-level Makefile) to rebuild all PR90519
reproducers with the local compiler once the fix is in place.
