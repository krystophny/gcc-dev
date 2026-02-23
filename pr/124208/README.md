# Bug 124208: ICE in gfc_resolve_forall with nested ASSOCIATE/BLOCK

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124208
- **GitHub issue:** TBD
- **Status:** PENDING (patch on fork, branch `pr124208-fix`)

## Notes

Regression from PR96255 changes in iterator counting.
Fix counts nested FORALL/DO CONCURRENT iterators inside `EXEC_BLOCK`
namespace code chains when sizing `var_expr`.
