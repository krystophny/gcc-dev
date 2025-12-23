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
└── scripts/                # Build scripts for /opt/gcc16*
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

### /opt/gcc16 (Offload Build)

Full GCC 16 with NVPTX offload support for OpenACC/OpenMP GPU testing.

```bash
# Compile with GPU offload
/opt/gcc16/bin/gfortran -fopenacc -foffload=nvptx-none test.f90 -o test

# CRITICAL: Use matching libgomp at runtime
LD_LIBRARY_PATH=/opt/gcc16/lib64 ./test

# Or compile with rpath
/opt/gcc16/bin/gfortran -fopenacc -foffload=nvptx-none \
  -Wl,-rpath,/opt/gcc16/lib64 test.f90 -o test
```

**Common pitfall:** Running GPU code but seeing only host device means you loaded
system libgomp instead of /opt/gcc16/lib64/libgomp.so.

### /opt/gcc16-master (Upstream Master)

Vanilla upstream master without local patches. Use to verify behavior before/after
fixes and confirm bugs exist upstream.

```bash
# Test with upstream master
/opt/gcc16-master/bin/gfortran -fopenacc test.f90 -o test_upstream
LD_LIBRARY_PATH=/opt/gcc16-master/lib64 ./test_upstream
```

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

### OpenACC Tests

OpenACC runtime tests require actual GPU offload. Tests marked with
`{ dg-skip-if "" { *-*-* } { "*" } { "-DACC_MEM_SHARED=0" } }` only run
when ACC_MEM_SHARED=0 (real GPU, not unified memory).

In gcc-build without NVPTX offload, these tests show as UNSUPPORTED.
Verify manually with /opt/gcc16:

```bash
/opt/gcc16/bin/gfortran -fopenacc -foffload=nvptx-none test.f90 -o test
LD_LIBRARY_PATH=/opt/gcc16/lib64 ./test
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

## Fix Development Rules

### DO

1. **Start with the failing condition** - write it down before coding
2. **Minimal fix first** - most bugs are single-condition fixes
3. **Check at the right level** - tree-level bugs need tree-level checks
4. **Refine conditions** - make checks more precise, don't add bypass params
5. **Test with nvfortran** - it defines correct OpenACC behavior

### DON'T

1. **Add bypass parameters** - refine the condition instead
2. **Fix in middle-end** when issue is Fortran-specific
3. **Add new infrastructure** for single-condition fixes
4. **Trust POINTER_TYPE_P alone** - distinguish real POINTER from pass-by-ref
5. **Add contiguous unnecessarily** - it causes copies for assumed-shape

## Patch Workflow

```bash
# 1. Create branch in gcc/
git -C gcc checkout -b pr<number>-fix

# 2. Make changes, test
cd gcc-build/gcc && make -j32
make check-gfortran RUNTESTFLAGS="dg.exp=pr<number>.f90"

# 3. Commit with proper format
git -C gcc commit -s -m "$(cat <<'EOF'
fortran: Short summary [PR<number>]

Description of the fix.

	PR fortran/<number>

gcc/fortran/ChangeLog:

	* file.cc (function): Change description.

Signed-off-by: Name <email>
EOF
)"

# 4. Export patch
git -C gcc format-patch -1 HEAD -o ../pr/<number>/

# 5. Track in meta-repo
git add pr/<number>/
git commit -m "pr<number>: add patch"
git push origin main
```

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

## Current Patch Status

**On origin/master (awaiting upstream):**

| PR | Description |
|----|-------------|
| 102430 | Reject array/allocatable LINEAR on DO |
| 103276 | Skip pointer mapping for pass-by-ref in ENTER/EXIT DATA |
| 123252 | Map scalar fields on enter data for components |
| 123280 | Fix acc_is_present for assumed-shape and pointers |
| 123282 | Fix OpenACC refcount for Fortran allocatable array descriptors |

**Merged upstream:** 32365, 90519, 92613, 96080, 96255, 107721, 121472, 121475, 121628

## Upstream Submission

**NEVER submit without explicit user permission.**

Permitted without approval:
- Prepare patches, run tests, document readiness

Requires permission:
- Post to gcc-patches@gcc.gnu.org
- Update Bugzilla
- Any external communication
