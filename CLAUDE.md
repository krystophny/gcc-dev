# GCC Fortran Development Meta-Repository

## Repository Structure

```
gcc-dev/                    # META-REPO (GitHub: krystophny/gcc-dev)
├── gcc/                    # GCC SOURCE (separate git repo, local branches only)
│   ├── gcc/fortran/        # Fortran frontend
│   ├── gcc/testsuite/gfortran.dg/  # Frontend tests
│   └── libgomp/            # OpenMP/OpenACC runtime library
├── gcc-build/              # Local dev build (not tracked)
├── gcc-master-build/       # Upstream master build (not tracked)
├── pr/                     # Bug work directories (tracked)
│   └── <number>/           # reproducer.f90, *.patch, README.md
├── gcc-offload-build/      # NVPTX offload build + install (not tracked)
└── scripts/                # Build scripts for offload compiler
```

**Git remotes in gcc/:**
- `origin` = github.com/krystophny/gcc (fork, safe to push)
- `upstream` = gcc.gnu.org/git/gcc.git (NEVER push, use git send-email)

**Commands:**
```bash
git -C gcc log upstream/master..origin/master --oneline  # patches on fork
git -C gcc format-patch -1 HEAD -o ../pr/<number>/       # export patch
```

## Installed Compilers

### Offload Build (gcc-offload-build/install)

Full GCC 16 with NVPTX offload support for OpenACC/OpenMP GPU testing.
Built by `scripts/build_gcc16_nvptx.sh`, installs into `gcc-offload-build/install/`.

```bash
OFFLOAD=$PWD/gcc-offload-build/install

# Compile with GPU offload
$OFFLOAD/bin/gfortran -fopenacc -foffload=nvptx-none test.f90 -o test

# CRITICAL: Use matching libgomp at runtime
LD_LIBRARY_PATH=$OFFLOAD/lib64 ./test

# Or compile with rpath
$OFFLOAD/bin/gfortran -fopenacc -foffload=nvptx-none \
  -Wl,-rpath,$OFFLOAD/lib64 test.f90 -o test
```

**Common pitfall:** Running GPU code but seeing only host device means you loaded
system libgomp instead of `gcc-offload-build/install/lib64/libgomp.so`.

### Reference Compilers

| Compiler | Command | Best for |
|----------|---------|----------|
| nvfortran | `nvfortran -acc` | OpenACC reference behavior |
| ifx | `source /opt/intel/oneapi/setvars.sh && ifx` | Standards compliance |
| flang-new | `flang-new` | LLVM comparison |
| System gfortran | `gfortran` | Quick checks |

nvfortran is the gold standard for OpenACC behavior.

## Build Configurations

### Local Development Build (gcc-build/)

Fortran-only, debug build for quick iteration:

```bash
mkdir -p gcc-build && cd gcc-build
../gcc/configure --enable-languages=fortran --disable-multilib \
  --disable-bootstrap CFLAGS='-Og -g' CXXFLAGS='-Og -g'
make -j32
```

### Rebuilding libgomp Only

After editing libgomp sources (e.g., openacc.f90), rebuild just libgomp:

```bash
cd gcc-build/x86_64-pc-linux-gnu/libgomp
make -j32
```

Then test with the local build:
```bash
gcc-build/gcc/gfortran -B gcc-build/gcc \
  -L gcc-build/x86_64-pc-linux-gnu/libgomp/.libs \
  -Wl,-rpath,$PWD/gcc-build/x86_64-pc-linux-gnu/libgomp/.libs \
  -fopenacc test.f90 -o test
```

## Testing

### Running Tests

**CRITICAL: Run from gcc-build/gcc/ only:**

```bash
cd gcc-build/gcc
make -j32 -k check-gfortran > /tmp/test.log 2>&1 &
```

**Results:**
```bash
grep -E "^FAIL|^XPASS" gcc-build/gcc/testsuite/gfortran/gfortran.sum
```

**Single test:**
```bash
make check-gfortran RUNTESTFLAGS="dg.exp=pr123280.f90"
```

### Full Test Suite Validation (MANDATORY for all patches)

Every patch MUST pass the full `check-gfortran` test suite before being accepted.
No partial passes. No skipped tests. Zero new failures.

```bash
cd gcc-build/gcc && make -j32 -k check-gfortran > /tmp/test.log 2>&1
grep -cE "^FAIL|^XPASS" testsuite/gfortran/gfortran.sum  # must be 0 new
```

Compare FAIL/XPASS counts against baseline recorded before fixes. If a fix
introduces regressions, fix them or revert the patch.

### OpenACC Tests

OpenACC runtime tests require actual GPU offload. Tests marked with
`{ dg-skip-if "" { *-*-* } { "*" } { "-DACC_MEM_SHARED=0" } }` only run
when ACC_MEM_SHARED=0 (real GPU, not unified memory).

In gcc-build without NVPTX offload, these tests show as UNSUPPORTED.
Verify manually with the offload build:

```bash
OFFLOAD=$PWD/gcc-offload-build/install
$OFFLOAD/bin/gfortran -fopenacc -foffload=nvptx-none test.f90 -o test
LD_LIBRARY_PATH=$OFFLOAD/lib64 ./test
```

### Writing Test Cases

**Runtime tests:** Use if/stop with unique exit codes:
```fortran
if (.not. acc_is_present(arr)) stop 1
if (.not. acc_is_present(ptr)) stop 2
```

**DejaGnu directives:**
```fortran
! { dg-do run }
! { dg-skip-if "" { *-*-* } { "*" } { "-DACC_MEM_SHARED=0" } }
```

## Debugging Techniques

### Tree Dumps

Examine generated code with tree dumps:

```bash
gfortran -fopenacc -fdump-tree-original -fdump-tree-omplower test.f90
```

Key dumps:
- `*.original`: Initial tree after frontend
- `*.omplower`: After OpenMP/OpenACC lowering (shows map clauses)
- `*.gimple`: GIMPLE representation

**What to look for in omplower:**
```
map(to:var)                    # Data copied to device
map(alloc:var)                 # Space allocated on device
map(tofrom:var)                # Bidirectional
map(to:c.arr [pointer set...]) # Pointer set mapping
```

### Debugging OpenACC Mapping Issues

When acc_is_present returns wrong results or "already mapped" errors occur:

1. **Check what addresses are being mapped:**
```fortran
print *, "Address of arr:", loc(arr)
print *, "Is present:", acc_is_present(arr)
```

2. **Check tree dump for unexpected copies:**
Look for `atmp` variables in omplower dump - these indicate the compiler
created a temporary copy (often due to `contiguous` attribute).

3. **Compare with nvfortran:**
nvfortran's behavior is the reference for OpenACC. If it works there
but not gfortran, it's a gfortran bug.

## Key Files by Domain

### OpenACC/OpenMP

| File | Purpose |
|------|---------|
| `gcc/fortran/trans-openmp.cc` | Directive translation, map clause generation |
| `libgomp/openacc.f90` | Fortran OpenACC runtime interface |
| `libgomp/oacc-mem.c` | OpenACC memory management (C runtime) |
| `gcc/omp-low.cc` | Middle-end OMP lowering (rarely touch) |

### Finalization/Derived Types

| File | Purpose |
|------|---------|
| `gcc/fortran/trans.cc` | `gfc_finalize_tree_expr` - finalization lowering |
| `gcc/fortran/trans-expr.cc` | Expression translation, assignments |
| `gcc/fortran/trans-array.cc` | Deep copy, `structure_alloc_comps` |
| `gcc/fortran/class.cc` | CLASS/polymorphic, vtables |

### Parsing/Resolution

| File | Purpose |
|------|---------|
| `gcc/fortran/match.cc` | Syntax matching |
| `gcc/fortran/resolve.cc` | Semantic analysis |
| `gcc/fortran/parse.cc` | Statement ordering |

## Common Bug Patterns

### Pattern 1: contiguous Attribute Causing Copies

**Symptom:** acc_is_present fails for assumed-shape or pointer arguments.

**Root cause:** A library function has `contiguous` on its dummy argument.
When a non-contiguous array is passed, gfortran creates a temporary copy.
The runtime then checks the copy's address, not the original.

**Fix:** Remove `contiguous` if the function only needs base address/size.

**Evidence:** PR123280, PR96080 - fixed by removing `contiguous` from
`acc_is_present_array_h` in libgomp/openacc.f90.

### Pattern 2: Pass-by-Reference vs POINTER

**Symptom:** ENTER DATA maps wrong address, "already mapped" errors.

**Root cause:** Fortran pass-by-reference creates pointer types at tree level,
but these are NOT Fortran POINTER variables. Code checking `POINTER_TYPE_P`
catches both, but they need different handling.

**Fix:** Use `GFC_DECL_GET_SCALAR_POINTER` or `GFC_DECL_GET_SCALAR_ALLOCATABLE`
to check for actual Fortran POINTER/ALLOCATABLE, not just tree pointer types.

**Evidence:** PR103276 - ENTER DATA was creating GOMP_MAP_POINTER for
pass-by-reference scalars, mapping stack slot instead of data.

### Pattern 3: Missing Scalar Field Mapping

**Symptom:** Derived type scalar fields have garbage values on device.

**Root cause:** When mapping only array components of a derived type,
GOMP_MAP_STRUCT is created for the parent but scalar fields aren't copied.

**Fix:** Add explicit mappings for scalar fields in trans-openmp.cc.

**Evidence:** PR123252 - scalar fields not mapped with ENTER DATA copyin.

### Pattern 4: Zero-Size Type ICE

**Symptom:** ICE in gimplifier for types with empty components.

**Root cause:** Check for `!derived->components` misses types that HAVE
components but those components are zero-size.

**Fix:** Use tree-level `TYPE_SIZE_UNIT == 0` instead of Fortran-level check.

**Evidence:** PR121472.

### Pattern 5: Refcount Double-Counting for Duplicate Splay Tree Keys

**Symptom:** Illegal memory access on iteration 2+ of alloc/enter/exit/dealloc
cycles with Fortran allocatable arrays. Order-dependent: only triggers when
first parallel loop does NOT use a derived type component.

**Root cause:** TO_PSET + POINTER mapping groups create multiple `tgt->list`
entries pointing to the SAME splay tree key (descriptor address).
`gomp_map_vars_internal` sets `refcount=2` (one per entry), and
`goacc_enter_data_internal` incremented `dynamic_refcount` for every entry.
But `exit_data` only sends ONE release per descriptor, decrementing by 1.
Result: `refcount=1, dynamic_refcount=1` after exit - mapping never removed.

**Fix:** Track duplicate keys in `goacc_enter_data_internal`:
- Only increment `dynamic_refcount` once per unique key
- Decrement `refcount` for duplicates to compensate

**Key lesson:** Initial hypothesis (GOMP_MAP_STRUCT stripping in gimplify.cc)
was WRONG. Deep debugging with runtime tracing revealed the actual issue was
in libgomp refcount handling, not middle-end. Always verify fixes with actual
testing before assuming root cause is correct.

**Evidence:** PR123282.

### Pattern 6: Double Allocation in Deep Copy for Nested Allocatables

**Symptom:** Memory leak on derived type assignment when the type contains an
allocatable array component whose element type also has allocatable components.

**Root cause:** In `structure_alloc_comps()` COPY_ALLOC_COMP case, for allocatable
arrays with nested allocatables (`cmp_has_alloc_comps && c->as`), the
`add_when_allocated` code (generated by recursive call at lines 10290-10293)
already includes a `gfc_duplicate_allocatable()` call. However, a changed
condition at line 11066 can cause the code to enter a branch that calls
`gfc_duplicate_allocatable()` AGAIN, resulting in double allocation. The first
allocation is leaked when the second one overwrites the data pointer.

**Fix:** Limit the `add_when_allocated != NULL_TREE` condition to scalars only
(`!c->as`). For allocatable arrays with nested allocatables, fall through to
line 11100 which adds `add_when_allocated` directly (already contains allocation).

**Key lesson:** When recursive code generation creates nested helper code, ensure
the outer code doesn't duplicate the same operations. Tree dumps (`-fdump-tree-original`)
are essential for spotting double allocations.

**Evidence:** PR123868.

### Pattern 7: GC Collection During Wrapper Generation

**Symptom:** ICE (segfault / `contains_struct_check` failure) when compiling
ALLOCATE of sub-objects in derived types with mutually-referencing recursive
allocatable array components.

**Root cause:** `generate_element_copy_wrapper` (PR121628) calls
`cgraph_node::add_new_function` which during `PARSING` state calls
`finalize_function` → `ggc_collect()`.  This GC frees locally-computed
COMPONENT_REF tree nodes on caller stack frames of `structure_alloc_comps`
that haven't been attached to any GC-rooted structure yet.  Triggered only
with mutually-referencing types (3+ types) that require nested wrapper
generation.

**Fix:** Use `cgraph_node::finalize_function(fndecl, true)` (no_collect=true)
to skip GC during wrapper registration.

**Key lesson:** When adding new functions during tree lowering, avoid
`add_new_function` if callers hold unrooted tree nodes.  Use
`finalize_function(..., true)` to defer GC.  Confirm with
`--param ggc-min-heapsize=999999` which disables GC.

**Evidence:** PR124235.

### Pattern 8: Error Recovery Leaving Helper Symbols Behind

**Symptom:** Invalid code emits the expected diagnostic and then ICEs later in
resolution or on the following statement, often with dangling symbol or symtree
references.

**Root cause:** Some parser-generated helper symbols/components are created
outside the normal undo checkpoint machinery.  On `reject_statement()`,
`gfc_undo_symbols()` frees the main declaration state but leaves the helper
node alive, so it still points into freed structures.

**Fix:** Record the pre-statement tail/root state before matching, and on
`MATCH_ERROR` explicitly unlink any helper nodes created during that statement.
Delete related symtree entries before releasing the helper symbol.

**Key lesson:** Do not assume that all declaration byproducts participate in
the undo machinery.  CLASS container symbols created by
`gfc_build_class_symbol` are one concrete example.

**Evidence:** PR106946.  PR82721 may be the same general family of bug, but
that still needs to be verified from a stack trace or reduced fix.

### Pattern 9: Namespace Charlen Nodes Surviving Rejected Declarations

**Symptom:** Invalid `CHARACTER(len(...))` declarations diagnose correctly and
then later crash or emit corrupted follow-up errors while resolving the length
expression.

**Root cause:** `gfc_new_charlen` pushes fresh `gfc_charlen` nodes onto the
current namespace `cl_list`, but `reject_statement()` does not undo that list.
If declaration processing fails before the charlen is attached to a surviving
symbol, the stale `len(...)` expression remains reachable from the namespace and
later resolves through dangling symtree pointers.

**Fix:** Clean up the unattached charlen at the exact failure point that rejects
the declaration.  Do not bulk-roll back all fresh `cl_list` nodes for the whole
statement, because some invalid declarations intentionally keep their charlen
state around for later diagnostics.

**Evidence:** PR82721.

### Pattern 10: OpenMP Clause Lowering Must Use Overall Expression Rank

**Symptom:** OpenMP `depend` or `depobj` locators with nested references such
as `x(j)%a` ICE during lowering, often in
`gfc_conv_scalarized_array_ref` with missing scalarizer state.

**Root cause:** Clause lowering looks only at the first `REF_ARRAY` to decide
whether a locator is scalar or array-valued.  For `x(j)%a`, that first array
reference is the scalar base element `x(j)`, but the full expression is still
the rank-1 component array `a`.

**Fix:** Choose between `gfc_conv_expr_reference` and
`gfc_conv_expr_descriptor` from the rank of the full expression (or
equivalently from the last relevant reference), not from the first
`REF_ARRAY`.

**Evidence:** PR102459.

### Pattern 11: OpenMP Hooks Must Tolerate Missing Outer References When Unused

**Symptom:** OpenMP lowering ICEs in a language hook such as
`gfc_omp_clause_default_ctor` because `outer == NULL_TREE`.

**Root cause:** The middle end can legitimately invoke the hook without an
outer reference in some reduction paths.  If the language-specific constructor
path only needs fresh local storage and does not actually read outer state,
asserting on a non-null outer reference is too strict.

**Fix:** Require `outer` only for cases that actually use it, such as copied
descriptors or recursive walks of allocatable components.  Keep the assertion
for those cases; relax it only for the plain scalar cases that do not inspect
the outer object.

**Evidence:** PR102596.

### Pattern 12: Mixed ENTRY Results Must Use ABI Return Types

**Symptom:** A mixed `ENTRY` function compiles until the GIMPLE verifier sees a
non-trivial conversion in `COMPONENT_REF`, often only with ABI-changing flags
such as `-ff2c`.

**Root cause:** Shared mixed-ENTRY master unions are easy to build from the
Fortran result symbol types, but those are not always the frontend ABI return
types.  Under `-ff2c`, default `REAL` entries still have default-REAL result
symbols while their wrappers return C `double`.

**Fix:** When building shared ENTRY result storage, derive each field from the
actual ABI return type of the entry wrapper, not from the raw Fortran result
symbol type.

**Evidence:** PR95338.

### Pattern 13: OpenMP Privatization Hooks Must Inspect the Original Decl

**Symptom:** OpenMP `private` or `firstprivate` on a scalar polymorphic
pointer compiles, but the worker cleanup finalizes and frees the shared
target, leading to a crash or double free at runtime.

**Root cause:** The OpenMP clause copy/dtor hooks are easy to steer from the
lowered tree type alone, but scalar class pointers often pass through
artificial saved-descriptor temporaries whose tree type still looks like a
class record.  If those hooks classify the entity as an owned polymorphic
object instead of a pointer-like one, they take the finalize/free path.

**Fix:** In the clause-specific ctor/dtor hooks, unwrap saved descriptors
first and recognize class-pointer container types locally.  Preserve only
pointer association for those entities there, without changing the broader
polymorphic mapping classification used for warnings or deep mapping.

**Evidence:** PR120286.

### Pattern 14: Shared CLASS Containers in Error Recovery

**Symptom:** SEGV or use-after-free when compiling invalid CLASS component
declarations inside derived types, especially when a valid and invalid
component share the same class type and attributes.

**Root cause:** `gfc_build_class_symbol` reuses existing CLASS container
symbols (e.g., `__class_w_a`) when multiple components have the same class
type and attributes.  Error-recovery code that frees the container for a
failed component also invalidates the container for previously committed
components.

**Fix:** Before freeing a CLASS container during error recovery, scan the
remaining component list for other references to the same container.  Only
free if unshared.

**Key lesson:** CLASS container symbols are shared by design.  Any cleanup
code that frees them must check for shared references first.  Valgrind on
x86_64 catches these even when the crash only manifests on other platforms.

**Evidence:** PR124482 (regression against PR106946 fix).

## Fix Development Rules

### DO

1. **Start with the failing condition** - write it down before coding
2. **Minimal fix first** - most bugs are single-condition fixes
3. **Check at the right level** - tree-level bugs need tree-level checks
4. **Refine conditions** - make checks more precise, don't add bypass params
5. **Test with nvfortran** - it defines correct OpenACC behavior
6. **Add debug tracing when stuck** - fprintf in runtime reveals actual state
7. **Verify fix actually works** - rebuild, reinstall, test with real reproducer
8. **Question initial hypothesis** - first plausible explanation often wrong

### DON'T

1. **Add bypass parameters** - refine the condition instead
2. **Fix in middle-end** when issue is Fortran-specific
3. **Add new infrastructure** for single-condition fixes
4. **Trust POINTER_TYPE_P alone** - distinguish real POINTER from pass-by-ref
5. **Add contiguous unnecessarily** - it causes copies for assumed-shape
6. **Assume tree dumps tell the whole story** - runtime behavior may differ
7. **Skip runtime testing** - compile-time analysis misses refcount/state bugs
8. **Trust asymmetric enter/exit** - if enter does X, exit should undo X

## Patch Workflow (MANDATORY)

### Prerequisites (one-time setup in gcc/)

```bash
cd gcc

# Install GCC git aliases and prepare-commit-msg hook
bash contrib/gcc-git-customization.sh
# Answer: name, email, upstream=origin, account=ert, prefix=me, hook=yes

# Verify user.name is correct (not truncated)
git config user.name   # Must show "Christopher Albert"
git config user.email  # Must show "albert@tugraz.at"

# Required Python packages for mklog and gcc-verify
pip install --user --break-system-packages unidiff GitPython
```

### Creating patches

```bash
# 1. Create branch off upstream/master in gcc/
git -C gcc checkout upstream/master
git -C gcc checkout -b pr<number>-fix

# 2. Make changes, rebuild, test
cd gcc-build/gcc && make -j32
make check-gfortran RUNTESTFLAGS="dg.exp=pr<number>.f90"

# 3. Stage changes
git -C gcc add gcc/fortran/changed-file.cc

# 4. Commit using gcc-commit-mklog (MANDATORY - auto-generates ChangeLog)
#    Write the commit message to a file first, then commit with -F.
#    The prepare-commit-msg hook appends the ChangeLog automatically.
cat > /tmp/gcc-commit-msg.txt <<'EOF'
fortran: Short summary [PR<number>]

Description of the fix.
EOF
cd gcc && GCC_FORCE_MKLOG=1 GCC_MKLOG_ARGS='["-b", "fortran/<number>"]' \
  git commit -s -F /tmp/gcc-commit-msg.txt

# 5. Verify commit passes GCC checks (MANDATORY before push)
git gcc-verify HEAD

# 5b. gcc-verify does NOT check for Signed-off-by.  Check the final
#     commit message explicitly, especially after editor/template-based
#     commits or any hook-driven message rewrite.
git log -1 --format=%B | grep -q '^Signed-off-by: ' \
  || { echo "ERROR: missing Signed-off-by trailer in commit"; exit 1; }

# 6. Export patch
git format-patch -1 HEAD -o ../pr/<number>/

# 6b. Verify the exported patch still contains Signed-off-by.
patch=$(ls -t ../pr/<number>/0001-*.patch | head -n1)
grep -q '^Signed-off-by: ' "$patch" \
  || { echo "ERROR: exported patch missing Signed-off-by trailer"; exit 1; }

# 7. Push to fork
git push origin pr<number>-fix

# 8. Track in meta-repo
cd .. && git add pr/<number>/
git commit -m "pr<number>: add patch"
git push origin main
```

**If `gcc-verify` rejects an incomplete hook-generated ChangeLog skeleton:**
- Keep the mklog hook enabled, but switch from plain `git commit -F ...` to an
  editor-driven commit (`git commit -e` with a template/editor script).
- Let the hook run, then replace the message with the fully completed
  ChangeLog text before the commit is finalized.
- Re-run `git gcc-verify HEAD` immediately.  Repeating `git commit -F ...`
  with a fully written ChangeLog can otherwise lead to duplicated hook output.
- After any editor/template-based commit, explicitly re-check that the
  `Signed-off-by:` trailer is still present.  A full-message replacement can
  silently drop the `-s` trailer even when `git commit -s` was used.

### Commit rules (HARD RULES)

- **Always use `gcc-commit-mklog`** or the `GCC_FORCE_MKLOG=1` env var
  with the prepare-commit-msg hook. Never hand-write ChangeLog entries.
- **Always run `git gcc-verify HEAD`** before pushing. It checks
  ChangeLog format, PR references, and other GCC conventions.
- **Always use `-s`** (Signed-off-by) on commits.
- **Always verify `Signed-off-by:` in both the final commit message and the
  exported patch.** `git gcc-verify` does not check this.
- **Branches go off `upstream/master`**, not off other fix branches.
- **One fix per branch** (e.g., `pr123949-init-se-fix`), not stacked.

## PR Directory Structure

Each `pr/<number>/` contains:

```
pr/123280/
├── README.md           # Analysis, links, status
├── reproducer.f90      # Minimal test case
├── 0001-*.patch        # Exported patch
└── Makefile            # Optional multi-compiler testing
```

README.md header format:
```markdown
# Bug 123280: Short description

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123280
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/12
- **Status:** PENDING (patch on fork) | MERGED (gcc commit abc123)
```

## Issue Management (krystophny/gcc-dev)

Each GCC PR tracked in this repo has a GitHub issue. Issues use additive labels
to track progress through the submission pipeline:

| Label | Meaning |
|-------|---------|
| `patch-ready` | Working patch exists on the fork |
| `on-bugzilla` | Patch/analysis posted to GCC Bugzilla |
| `on-mailing-list` | Patch sent to gcc-patches@ mailing list |
| (closed) | Merged upstream |

Labels are additive: an issue can have all three simultaneously.

### When adding labels, always include a comment with links:

- **on-bugzilla**: link to the Bugzilla bug
  `https://gcc.gnu.org/bugzilla/show_bug.cgi?id=<number>`
- **on-mailing-list**: link to the mailing list archive post
  `https://gcc.gnu.org/pipermail/gcc-patches/YYYY-Month/NNNNNN.html`

### When closing issues (merged upstream), always include:

- Link to the upstream commit:
  `https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=<hash>`
- The GCC revision tag (e.g., `r16-7700-ge0b70284cfa`)

Example close comment:
```
Merged upstream: r16-7700-ge0b70284cfa
https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=e0b70284cfa...
```

## Current Patch Status

**On origin (individual branches + integration branch `openacc`):**

| PR | Branch | Description |
|----|--------|-------------|
| 102430 | `origin/master` | Reject array/allocatable LINEAR on DO |
| 120286 | `pr120286-fix` | Preserve scalar class pointers in OpenMP privatization |
| 123280+96080 | `pr123280-fix` | Fix acc_is_present for assumed-shape and pointers |
| 103276 | `pr103276-fix` | Skip pointer mapping for pass-by-ref in ENTER/EXIT DATA |
| 123252 | `pr123252-fix` | Map scalar fields on enter data for components |
| 123282 | `pr123282-fix` | Fix OpenACC refcount for Fortran allocatable array descriptors |

**Merged upstream:** 32365, 82721, 90519, 92613, 95338, 96255, 102333, 102459, 102596, 103139, 106946, 107721, 110877, 121472, 121475, 121628, 123868, 123943, 123947, 123949, 124208, 124235, 124482

## aarch64 Testing (Hetzner Cloud)

For testing on aarch64 (e.g., CI regressions reported by Linaro), use a
short-lived Hetzner Cloud VM via `scripts/hcloud-vm.sh`.

**Prerequisites:** `hcloud` CLI installed, `HCLOUD_TOKEN` in `~/.secrets`.

```bash
source ~/.secrets

# Spin up CAX41 (16 ARM cores, 32 GB, ~0.05 EUR/hr)
scripts/hcloud-vm.sh create

# Clone GCC at a specific commit (uses git://gcc.gnu.org)
scripts/hcloud-vm.sh clone <commit>    # or omit commit for master HEAD

# Debug build (fast, no bootstrap)
scripts/hcloud-vm.sh build

# OR: LTO bootstrap (slow, ~3-4 hrs, runs in tmux)
scripts/hcloud-vm.sh bootstrap-lto

# Monitor tmux build progress
scripts/hcloud-vm.sh tail

# Run a single test
scripts/hcloud-vm.sh test pr123949.f90

# Run full check-gfortran (in tmux)
scripts/hcloud-vm.sh check

# Interactive SSH (with agent forwarding for GitHub)
scripts/hcloud-vm.sh ssh

# Tear down (immediate)
scripts/hcloud-vm.sh destroy
```

**Multiple VMs:** Override `HCLOUD_VM_NAME` to manage parallel VMs:
```bash
HCLOUD_VM_NAME=gcc-aarch64-nofix scripts/hcloud-vm.sh create
HCLOUD_VM_NAME=gcc-aarch64-nofix scripts/hcloud-vm.sh tail
HCLOUD_VM_NAME=gcc-aarch64-nofix scripts/hcloud-vm.sh destroy
```

**VM layout mirrors local:** `/root/gcc-dev/{gcc,gcc-build,gcc-build-lto}`.
`build` creates `gcc-build` (debug, no bootstrap); `bootstrap-lto` creates
`gcc-build-lto` (LTO bootstrap). `test` and `check` auto-detect which exists.

**SSH key:** `ert-workstation` must be pre-registered on Hetzner Cloud.
SSH agent forwarding (`-A`) is used throughout for GitHub fork access.

## Upstream Submission

**ABSOLUTELY FORBIDDEN without explicit user permission:**
- `git send-email` to gcc-patches@gcc.gnu.org
- Posting to any GCC mailing list
- Updating Bugzilla (posting comments, attaching files)
- Any external communication

**NEVER use git send-email, gcc-send-patch.sh, or gcc-bugzilla.sh attach
without the user explicitly requesting it - this is a HARD RULE.**

Permitted without approval:
- Prepare patches, run tests, document readiness
- Push to origin (krystophny/gcc fork)
- Create PRs in the fork
- Export patches with `git format-patch`
- Query Bugzilla for bug info (`gcc-bugzilla.sh info <number>`)

### Tooling

**Backport-aware workflow**:
```bash
# Refresh canonical per-PR metadata from tracked READMEs/patches
python3 scripts/gcc-workflow.py sync-metadata --all

# Render maintainer packets and the regression backport matrix
python3 scripts/gcc-workflow.py render-packet --all --regressions
python3 scripts/gcc-workflow.py scan-regressions

# Run release-branch applicability checks in dedicated worktrees/build dirs
python3 scripts/gcc-workflow.py branch-check --branches gcc-15,gcc-14,gcc-13

# Generated files:
#   pr/<n>/status.json
#   pr/<n>/submission/{maintainer-summary.md,bugzilla-comment.txt,mailing-list-cover.txt}
#   pr/<n>/backports/<branch>/
#   pr/backport-matrix.{md,json}
```

**Bugzilla CLI** (`python-bugzilla`):
```bash
# Query bug info (always permitted)
scripts/gcc-bugzilla.sh info <pr-number>

# Search open fortran bugs by summary text (always permitted)
scripts/gcc-bugzilla.sh search "ICE in fold_convert"

# List all open fortran regressions (always permitted)
scripts/gcc-bugzilla.sh regressions

# Attach a patch (REQUIRES explicit user permission)
scripts/gcc-bugzilla.sh attach <pr-number> <file>

# Login (one-time, saves token in ~/.bugzillarc)
scripts/gcc-bugzilla.sh login

# Submit the generated packet (REQUIRES explicit user permission)
scripts/gcc-bugzilla.sh submit <pr-number> [--branch trunk|gcc-15|gcc-14|gcc-13] [--execute]
```

**Mailing list** (`git send-email`, configured in gcc/):
```bash
# Send patch (REQUIRES explicit user permission)
scripts/gcc-send-patch.sh pr/<number>/0001-*.patch

# Dry run (preview without sending, always permitted)
scripts/gcc-send-patch.sh --dry-run pr/<number>/0001-*.patch

# Send the generated packet (REQUIRES explicit user permission)
scripts/gcc-send-patch.sh submit <pr-number> [--branch trunk|gcc-15|gcc-14|gcc-13] [--execute]
```

Both scripts have interactive confirmation prompts as a safety net.
