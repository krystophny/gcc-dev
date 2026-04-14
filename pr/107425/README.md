# Bug 107425: ICE in gimplify_var_or_parm_decl with implicit var in iterator depend clause

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107425
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/89

## Root Cause

Regression introduced by r12-6780-gd2ad748eeef (PR103695).

gfc_match_iterator creates a block namespace for iterator variables.
When the locator expression x(j) is parsed with gfc_current_ns set to
this iterator namespace, the implicit variable j is created there. In
gfc_finish_var_decl, the FL_LABEL check for BLOCK constructs matched
before the omp_affinity_iterators check, routing j through
add_decl_as_local. Unlike real BLOCK construct variables, these never
get a proper BIND_EXPR, so the gimplifier rejects them.

## Fix

Check for omp_affinity_iterators before the FL_LABEL BLOCK construct
check. Only treat actual iterator variables as block-local; add other
variables to the enclosing function scope.

File: gcc/fortran/trans-decl.cc (gfc_finish_var_decl)
