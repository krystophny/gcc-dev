# PR103276 - OpenACC: duplicate mapping for ENTER DATA on derived types

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103276
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/10
- **Status:** PENDING (patch on fork, awaiting upstream submission)

**Title:** [openacc] Trying to map already mapped data

**Component:** fortran (OpenACC)

## Summary

GCC can emit OpenACC ENTER DATA mapping code for a derived-type dummy argument
that includes a host address pointing into the current stack frame.  When the
mapping persists across the call, subsequent ENTER DATA regions may conflict
due to overlapping stack ranges, producing a runtime error like:

`libgomp: Trying to map into device [...] object when [...] is already mapped`

The failure is reported as sporadic in practice (stack layout dependent).

## Evidence (OMP lowering)

Both reproducers show the same problematic OMP lowering in the tree dump:

- `.omp_data_arr.*.var = &var;`
- followed by `map(alloc:var [pointer assign, bias: 0])`

This matches the Bugzilla discussion that the mapping should use the reference
value, not the address of the dummy-argument slot.

To inspect:

```bash
./gcc-build/gcc/gfortran -B ./gcc-build/gcc -O2 -fopenacc -c pr/103276/reproducer.f90 \
  -fdump-tree-omplower -dumpdir /tmp/ -dumpbase pr103276_reproducer

rg -n \"\\.omp_data_arr|&var|pointer assign\" /tmp/pr103276_reproducer.*.omplower
```

## Reproducers

- `reproducer.f90`: reduced runnable reproducer based on the local report
  (the original snippet used `W1` but the variable is `WDES1`).
- `reproducer_bugzilla_min.f90`: minimal structure based on the Bugzilla report
  (two separate procedures that do ENTER DATA on a derived-type argument).

Both target the same symptom: ENTER DATA on derived types leading to duplicate
mapping errors in libgomp.

## Patch

`0001-fortran-Skip-pointer-mapping-for-pass-by-ref-in-ENTE.patch`

Fixes the root cause in `gcc/fortran/trans-openmp.cc` by skipping
GOMP_MAP_POINTER mappings for ENTER/EXIT DATA on variables that are
only pointers at tree level due to Fortran pass-by-reference, not
actual POINTER/ALLOCATABLE variables.  This follows Tobias Burnus's
analysis in Bugzilla comment #8-9.

## Build / Run (NVPTX example)

This is a runtime/offload issue; compiling to an object file is not sufficient.

```bash
gfortran -O2 -fopenacc -foffload=nvptx-none pr/103276/reproducer.f90 -o /tmp/pr103276.x

# The error is reported to be sporadic; repeat runs if needed.
/tmp/pr103276.x
```

If using a non-default GCC install (e.g. `/opt/gcc16`), ensure the matching
`libgomp` is used at runtime (via `LD_LIBRARY_PATH` or rpath).
