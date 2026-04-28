# Build, Test, and Debug

## Installed Compilers

### Offload Build (gcc-offload-build/install)

Full GCC 16 with NVPTX offload support for OpenACC/OpenMP GPU testing.
Built by `scripts/build-gcc16-nvptx.sh`, installs into `gcc-offload-build/install/`.

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
  --disable-bootstrap --enable-valgrind-annotations \
  CFLAGS='-Og -g' CXXFLAGS='-Og -g'
make -j32
```

`--enable-valgrind-annotations` is enabled by default in local builds.  This
keeps direct `valgrind .../f951` investigations meaningful by suppressing known
sparse-set false positives.  Outside Valgrind, these annotations compile to
client-request sequences that return default values on the real CPU, so the
expected cost for normal development builds is negligible.

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

**Run from the meta-repo root:**

```bash
scripts/check-fortran.sh > /tmp/test.log 2>&1
```

**Results:**
```bash
grep -E "^(FAIL|XPASS|UNRESOLVED|ERROR):" \
  gcc-build/gcc/testsuite/gfortran/gfortran.sum
```

**Single test:**
```bash
scripts/check-fortran.sh dg.exp=pr123280.f90
```

### DejaGnu Harness Rules

Use `scripts/check-fortran.sh` for GCC Fortran frontend tests in this
meta-repo.  It regenerates the build-tree `gcc/site.exp` and lets GCC's
own DejaGnu rules select the rebuilt compiler, `-B` paths, libgfortran,
libatomic, and libquadmath.  Do not hand-roll `GFORTRAN_UNDER_TEST`,
`--srcdir`, or runtime library paths at the prompt.  The script runs the
GCC test target in parallel by default; set `GCC_TEST_JOBS=<n>` to
override the job count.

Valid commands:

```bash
scripts/check-fortran.sh dg.exp=pr123280.f90
scripts/check-fortran.sh > /tmp/check-fortran.log 2>&1
```

Invalid commands:

```bash
make check-gfortran RUNTESTFLAGS="GFORTRAN_UNDER_TEST='... -B...' dg.exp=pr123280.f90"
make check-fortran RUNTESTFLAGS="--srcdir=... GFORTRAN_UNDER_TEST=/usr/bin/gfortran"
```

A test run counts only if `testsuite/gfortran/gfortran.sum` contains a real
`=== gfortran Summary ===` block with expected-pass counts and names the
rebuilt compiler with `-B` build-tree paths, not `/usr/bin/gfortran`.  A
run that produces no summary, zero tests, `cannot execute 'f951'`, `cannot
find -lcaf_single`, a missing `GFORTRAN_16`, or a system-compiler version
line is a harness failure, not a test result.

Known expected local failure on this workstation:

```text
FAIL: gfortran.dg/bessel_6.f90   -O0  execution test
FAIL: gfortran.dg/bessel_6.f90   -O1  execution test
FAIL: gfortran.dg/bessel_6.f90   -O2  execution test
FAIL: gfortran.dg/bessel_6.f90   -O3 -fomit-frame-pointer -funroll-loops -fpeel-loops -ftracer -finline-functions  execution test
FAIL: gfortran.dg/bessel_6.f90   -O3 -g  execution test
FAIL: gfortran.dg/bessel_6.f90   -Os  execution test
```

`scripts/check-fortran.sh` treats only those exact lines as expected; every
other `FAIL`, `XPASS`, `UNRESOLVED`, or `ERROR` remains a failed run.

### Full Test Suite Validation (MANDATORY for all patches)

Every patch MUST pass the full Fortran frontend suite before being accepted.
No partial passes. No skipped tests. Zero new failures.

```bash
scripts/check-fortran.sh > /tmp/test.log 2>&1
grep -cE "^(FAIL|XPASS|UNRESOLVED|ERROR):" \
  gcc-build/gcc/testsuite/gfortran/gfortran.sum  # must be 0
```

The frontend suite covers `gomp`, `goacc`, and `goacc-gomp`
directories, but it does not cover the libgomp Fortran runtime harnesses.
Before posting any patch, also run this from `gcc-build/`:

```bash
make -j32 check-target-libgomp-fortran > /tmp/libgomp-fortran.log 2>&1
```

Treat any `FAIL` or `XPASS` in that runtime run as blocking, exactly like
the frontend suite, and verify in the log that both
`libgomp.fortran/fortran.exp` and `libgomp.oacc-fortran/fortran.exp` ran.
If either harness is missing, run it explicitly via `check-target-libgomp`
before posting.

Compare FAIL/XPASS counts against baseline recorded before fixes. If a fix
introduces regressions, fix them or revert the patch.

### OpenACC Tests

OpenACC runtime tests require actual GPU offload. Tests marked with
`{ dg-skip-if "" { *-*-* } { "*" } { "-DACC_MEM_SHARED=0" } }` only run
when ACC_MEM_SHARED=0 (real GPU, not unified memory).

For libgomp Fortran runtime coverage, review the `check-target-libgomp-fortran`
log and confirm that `libgomp.oacc-fortran/fortran.exp` ran. If not, rerun
that harness explicitly with `check-target-libgomp` before posting.

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

**OpenMP testcase placement:**
- OpenMP compile-only frontend tests belong in `gcc/testsuite/gfortran.dg/gomp/`.
  Those tests get `-fopenmp` automatically; do not add it manually unless the
  testcase has a specific non-default driver requirement.
- OpenMP link or runtime tests belong in `libgomp/testsuite/libgomp.fortran/`.
  This includes any test that uses `dg-do run`, `omp_lib.h`, or `use omp_lib`,
  because `libgomp` and the Fortran OpenMP module are only available there.
- If an OpenMP testcase executes code rather than only checking diagnostics or
  dumps, default to `libgomp.fortran/` and move it to `gcc/testsuite/` only
  when there is a frontend-specific reason.

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

# Run full Fortran frontend checks (in tmux)
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
