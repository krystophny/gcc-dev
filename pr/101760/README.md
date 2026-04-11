# Bug 101760: ICE in make_ssa_name_fn with deferred-length character in OMP target

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=101760
- **Related:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102314
- **Status:** PENDING (patch on fork)

## Affected Versions
| Branch | Reproduces? | Notes |
|--------|-------------|-------|
| trunk (r16-9877) | yes | ICE in make_ssa_name_fn at -O1/-O2 |
| releases/gcc-15 | likely | regression since r12-1319 |
| releases/gcc-14 | likely | regression since r12-1319 |
| releases/gcc-13 | likely | regression since r12-1319 |

## Root Cause

For `character(:), allocatable, target` variables, the character array type
`character(kind=1)[1:.x]` has `TYPE_SIZE` and `TYPE_SIZE_UNIT` wrapped in
SAVE_EXPRs (created by `variable_size` in `finalize_type_size`).

In `gfc_omp_finish_clause`, when computing `OMP_CLAUSE_SIZE` for implicitly
mapped variables, the code used `TYPE_SIZE_UNIT(TREE_TYPE(decl))` directly.
This shares the SAVE_EXPR tree node with the type.  When `gimplify_expr`
later resolves the SAVE_EXPR, it modifies it in place, storing a gimple
temporary in `TREE_OPERAND(save_expr, 0)`.  This corrupts the type's size
expression.

When the enclosing function is later inlined (at -O1 or higher),
`remap_type_1` walks `TYPE_SIZE` of the character array type and encounters
the stale gimple temporary as an unmappable SSA name, triggering an ICE in
`make_ssa_name_fn`.

## Fix

Compute the clause size from the array domain bounds (`TYPE_MAX_VALUE`,
`TYPE_MIN_VALUE`) and element size (`TYPE_SIZE_UNIT(element_type)`) instead
of using `TYPE_SIZE_UNIT` directly.  This creates a fresh tree expression
that is decoupled from the type's SAVE_EXPRs, so gimplification of the
clause size cannot corrupt the type.
