# PR103276 - OpenACC: duplicate mapping for ENTER DATA on derived types

**Title:** [openacc] Trying to map already mapped data

**Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103276

**Component:** libgomp (OpenACC)

**Status:** UNCONFIRMED (Bugzilla); tracked locally for reproduction.

**Tracking issue:** https://github.com/krystophny/gcc-dev/issues/10

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

## Build / Run (NVPTX example)

This is a runtime/offload issue; compiling to an object file is not sufficient.

```bash
gfortran -O2 -fopenacc -foffload=nvptx-none pr/103276/reproducer.f90 -o /tmp/pr103276.x

# The error is reported to be sporadic; repeat runs if needed.
/tmp/pr103276.x
```

If using a non-default GCC install (e.g. `/opt/gcc16`), ensure the matching
`libgomp` is used at runtime (via `LD_LIBRARY_PATH` or rpath).
