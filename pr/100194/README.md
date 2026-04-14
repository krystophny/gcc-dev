# Bug 100194: ICE in gfc_trans_create_temp_array with assumed-rank + contiguous

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=100194

## Description

Passing an assumed-rank array to a contiguous assumed-rank dummy causes an ICE
in `gfc_trans_create_temp_array` at the assertion `gcc_assert (ss->dimen > 0)`.
The scalarizer sets `dimen = -1` for assumed-rank arrays because rank is unknown
at compile time.

## Root Cause

The contiguous-copy path at `gfc_conv_procedure_call` (trans-expr.cc) routes
assumed-rank actuals through `gfc_conv_subref_array_arg`, which uses the
scalarizer.  The scalarizer requires known rank at compile time, but
assumed-rank arrays have `rank = -1`.

## Fix

Skip the `gfc_conv_subref_array_arg` path for assumed-rank expressions
(`e->rank == -1`) and let them fall through to `gfc_conv_array_parameter`,
which handles assumed-rank via the runtime pack/unpack functions
(`_gfortran_internal_pack`/`_gfortran_internal_unpack`).
