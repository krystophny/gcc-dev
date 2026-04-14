# GCC PR121472 - ICE with constructor and finalizer

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/2

## Two Fix Approaches

### Simple Fix (RECOMMENDED)

**Branch:** `pr121472-simple-fix`
**Patch:** `0001-fortran-Fix-ICE-with-constructor-for-finalized-zero-.patch`

Minimal 3-line condition change in `trans.cc`. Replaces the Fortran-level
check `!derived->components` with a tree-level `TYPE_SIZE_UNIT == 0` check
that catches all zero-size cases.

```diff
-      if (!derived->components && (!rank || attr.elemental))
+      tree type = TREE_TYPE (se->expr);
+      if (type && TYPE_SIZE_UNIT (type)
+          && integer_zerop (TYPE_SIZE_UNIT (type))
+          && (!rank || attr.elemental))
```

### Complex Fix (historical)

**Branch:** `pr121472-constructor-finalizer-ice`
**Patch:** `0001-fortran-Finalize-function-results-per-F2003-4.5.5.2.patch`

Large 6-file patch with temp metadata tracking infrastructure. Overkill for
this specific ICE.

## Relationship to PR121475

PR121472 and PR121475 are **independent** fixes in different code paths
within `gfc_finalize_tree_expr()`:

```c
gfc_finalize_tree_expr (...)
{
  if (attr.pointer)
    return;

  // ════════════════════════════════════════════════════════════
  // PR121475 LOCATION: Early return for defined_assign_comp
  // ════════════════════════════════════════════════════════════
  if (derived && (derived->attr.is_c_interop
                  || derived->attr.is_iso_c
                  || derived->attr.is_bind_c
                  || derived->attr.defined_assign_comp))  // <-- HERE
    return;

  if (is_class)
    { ... }
  else if (derived && gfc_is_finalizable (derived, NULL))
    {
      // ══════════════════════════════════════════════════════
      // PR121472 LOCATION: Zero-size type handling
      // ══════════════════════════════════════════════════════
      if (TYPE_SIZE_UNIT is zero)  // <-- HERE
        desc = gfc_create_var (type, "zero");
      ...
    }
}
```

Both can be applied separately without conflict.

### PR121475 Simple Variant

PR121475 also has a simpler fix than our original approach. Instead of adding
a `finalize_func_result` parameter to bypass the check, refine the condition:

```diff
   if (derived && (derived->attr.is_c_interop
                  || derived->attr.is_iso_c
                  || derived->attr.is_bind_c
-                 || derived->attr.defined_assign_comp))
+                 || (derived->attr.extension && derived->f2k_derived
+                    && derived->f2k_derived->tb_op[INTRINSIC_ASSIGN])
+                 || (!derived->attr.extension && derived->attr.defined_assign_comp)))
     return;
```

This distinguishes:
- **Extension types**: Only skip if there is an actual type-bound assignment
  operator (`tb_op[INTRINSIC_ASSIGN]`)
- **Non-extension types**: Keep original `defined_assign_comp` behavior

The original `defined_assign_comp` check was too broad - it skipped
finalization even when no actual defined assignment was involved.

## Root Cause Analysis

### PR121472: Zero-size types

The ICE occurs in `gfc_finalize_tree_expr()` when handling zero-size derived
types. The existing check `!derived->components` only catches types with no
components at all.

**The gap:** Types that HAVE components but where those components are
themselves empty (zero-size) were missed.

```fortran
type r
end type          ! Empty type - zero size

type ip
  type(r) :: r_member   ! Has component, but component is empty
contains
  final :: ipd
end type
```

Here `ip` has `derived->components` (it contains `r_member`), so
`!derived->components` is false. But the actual tree type has zero size
because `r` is empty.

**The fix:** Check the tree-level `TYPE_SIZE_UNIT` instead of the Fortran-level
component list. This catches ALL zero-size cases regardless of how the
zero size came about.

### PR121475: Defined assignment

The early return for `defined_assign_comp` was skipping finalization for
function results passed to defined assignment, violating F2003 4.5.5.2.

**The gap:** The check `derived->attr.defined_assign_comp` is set whenever
a type has components with defined assignment somewhere in its hierarchy.
But this doesn't mean the current assignment uses defined assignment.

**The fix:** Be more precise about when defined assignment actually applies:
- For extension types, check if there's a type-bound assignment operator
- For non-extension types, keep the original behavior

## Reproducer

See `reproducer.f90` and test case `gfortran.dg/pr121472.f90`.

## Lessons Learned

### 1. Understand the existing check before replacing it

The original `!derived->components` check was not arbitrary. It was handling
zero-size types to avoid gimplifier problems. The comment even explained this:

```c
/* Any attempt to assign zero length entities, causes the gimplifier
   all manner of problems. Instead, a variable is created to act as
   as the argument for the final call.  */
```

The bug was that this check was incomplete, not that it was wrong. The fix
extends the check to catch more zero-size cases, not replace the logic.

### 2. Prefer tree-level checks for size/layout issues

Fortran-level attributes like `derived->components` tell you about the source
structure. Tree-level information like `TYPE_SIZE_UNIT` tells you about the
actual compiled representation.

When the bug involves the gimplifier (a tree-level component), tree-level
checks are more reliable. The gimplifier doesn't care whether a type has
components in Fortran - it cares about actual memory size.

### 3. Look for the minimal fix first

Both PRs had complex multi-file fixes initially:

| PR | Complex Fix | Simple Fix |
|----|-------------|------------|
| 121472 | 6 files, 212+ lines, temp metadata infrastructure | 1 file, +3 lines, condition change |
| 121475 | 4 files, 115+ lines, new parameter threading | 1 file, +3 lines, condition refinement |

The complex fixes addressed broader issues (F2018 finalization semantics,
temp tracking infrastructure) but the actual bugs only needed condition
refinements.

**Ask:** "What is the exact condition that fails, and what should it be?"

### 4. Refine conditions, don't add bypass parameters

The complex PR121475 fix added a `finalize_func_result` parameter to bypass
the `defined_assign_comp` check when needed. The simple fix instead makes
the check itself more precise.

**Adding parameters:** Creates API surface, requires threading through
call sites, adds complexity for all callers.

**Refining conditions:** Keeps API unchanged, fixes the logic where it belongs,
easier to understand and maintain.

### 5. Preserve existing comments when logic is unchanged

The simple PR121472 fix keeps the original comment verbatim:

```c
/* Any attempt to assign zero length entities, causes the gimplifier
   all manner of problems. Instead, a variable is created to act as
   as the argument for the final call.  */
```

The reasoning hasn't changed - we're still creating a dummy variable to
avoid gimplifier problems with zero-length entities. Only the detection
of "zero-length" changed from `!derived->components` to `TYPE_SIZE_UNIT == 0`.

### 6. Understand what you're checking at each level

| Level | Check | What it tells you |
|-------|-------|-------------------|
| Fortran symbol | `derived->components` | Type has component declarations |
| Fortran symbol | `derived->attr.defined_assign_comp` | Type hierarchy includes defined assignment |
| Fortran symbol | `derived->attr.extension` | Type extends another type |
| Fortran f2k | `derived->f2k_derived->tb_op[INTRINSIC_ASSIGN]` | Type has type-bound assignment |
| Tree | `TYPE_SIZE_UNIT(type)` | Actual compiled size in bytes |
| Tree | `TREE_TYPE(expr)` | Compiled type of expression |

Bugs often arise from checking at the wrong level. PR121472 was checking
component existence when it should have checked compiled size. PR121475 was
checking hierarchy-wide attribute when it should have checked actual operator
binding.

### 7. Map out the code path structure

Drawing the code structure (as shown in "Relationship to PR121475" above)
immediately clarifies:
- These are independent code paths
- Each fix targets a specific location
- No interaction between the fixes

This prevents over-engineering where you try to create a unified solution
for unrelated issues.
