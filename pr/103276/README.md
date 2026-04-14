# PR103276 - OpenACC: duplicate mapping for ENTER DATA on derived types

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103276
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/10

**Component:** fortran (OpenACC)

## Summary

GCC can emit OpenACC ENTER DATA mapping code for a derived-type dummy argument
that includes a host address pointing into the current stack frame.  When the
mapping persists across the call, subsequent ENTER DATA regions may conflict
due to overlapping stack ranges, producing a runtime error like:

`libgomp: Trying to map into device [...] object when [...] is already mapped`

The failure is reported as sporadic in practice (stack layout dependent).

## Reproducers

- `reproducer.f90`: reduced runnable reproducer based on the local report
  (the original snippet used `W1` but the variable is `WDES1`).
- `reproducer_bugzilla_min.f90`: minimal structure based on the Bugzilla report
  (two separate procedures that do ENTER DATA on a derived-type argument).

Both target the same symptom: ENTER DATA on derived types leading to duplicate
mapping errors in libgomp.
