# GCC Fortran Development

Meta-repository for GCC Fortran frontend and libgomp development.

## Quick Start

```bash
# Build local dev compiler
cd gcc-build && make -j$(nproc)

# Test with GPU offload (requires /opt/gcc16)
/opt/gcc16/bin/gfortran -fopenacc -foffload=nvptx-none test.f90
LD_LIBRARY_PATH=/opt/gcc16/lib64 ./a.out
```

## Structure

| Directory | Purpose |
|-----------|---------|
| `gcc/` | GCC source (separate git repo) |
| `gcc-build/` | Local development build |
| `pr/` | Bug reproducers and patches |
| `scripts/` | Build scripts for /opt/gcc16 |

## Current Work

**Pending patches (on fork):**
- [PR102430](pr/102430/) - OpenMP linear(array) ICE
- [PR103276](pr/103276/) - OpenACC ENTER DATA mapping
- [PR106946](pr/106946/) - CLASS component error-recovery ICE
- [PR110877](pr/110877/) - Polymorphic dummy-array assignment deep copy
- [PR120723](pr/120723/) - OpenACC scalar attach/detach lowering
- [PR123252](pr/123252/) - Derived type scalar fields
- [PR123280](pr/123280/) - acc_is_present for assumed-shape / pointers
- [PR123282](pr/123282/) - OpenACC refcount with allocatable descriptors

**Recently merged upstream:**
[PR122491](pr/122491/), [PR123868](pr/123868/), [PR123947](pr/123947/),
[PR123949](pr/123949/), [PR124208](pr/124208/), [PR124235](pr/124235/)

**Earlier merged upstream:**
[PR32365](pr/32365/), [PR90519](pr/90519/), [PR92613](pr/92613/),
[PR96255](pr/96255/), [PR107721](pr/107721/), [PR121472](pr/121472/),
[PR121475](pr/121475/), [PR121628](pr/121628/)

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete development guide
- [pr/README.md](pr/README.md) - PR tracking overview

## Installed Compilers

| Path | Description |
|------|-------------|
| `/opt/gcc16` | GCC 16 with NVPTX offload (local patches) |
| `/opt/gcc16-master` | Upstream master (no patches) |

## Links

- [GCC Bugzilla](https://gcc.gnu.org/bugzilla/)
- [GitHub Issues](https://github.com/krystophny/gcc-dev/issues)
- [GCC Fortran Mailing List](https://gcc.gnu.org/mailman/listinfo/fortran)
