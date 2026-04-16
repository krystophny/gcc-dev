# Bug 42954: Target CPP builtins missing in gfortran -cpp

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=42954
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/52
- **Status:** PENDING (v2 patch on Bugzilla, attachment 64225)

## Summary

`gcc/fortran/cpp.cc` carried the commented-out `TARGET_*_CPP_BUILTINS`
block (the "Pandora's Box" FIXME) since 2008.  `gfortran -E -cpp -dM`
was missing all target preprocessor macros that `gcc -E -dM` defined.

The fix provides Fortran-compatible wrapper macros for C-family
identifiers used in target config headers, then enables
TARGET_OS_CPP_BUILTINS and TARGET_OBJFMT_CPP_BUILTINS.  For
TARGET_CPU_CPP_BUILTINS (whose implementing functions live in
C-family-only object files), an x86 implementation is provided
directly in fortran/cpp.cc.

Key design choice: `flag_iso=1` (ISO mode) suppresses user-namespace
bare-name macros like `unix`, `linux`, `i386` that would silently
replace valid Fortran identifiers.  Only reserved-namespace forms
(`__unix__`, `__linux__`, `__i386__`) are defined.

Co-authored-by: Kai Tietz <ktietz@gcc.gnu.org>

## Patch history

| Version | Attachment | Changes |
|---------|-----------|---------|
| v1 | 64224 (obsoleted) | flag_iso=0; caused bare-name pollution and declare-variant-10 regression |
| v2 | 64225 | flag_iso=1; remove dead `__attribute__` from declare-variant-10; fix bare `i386` |

## Validation (v2)

```
check-gfortran:              76597 passes, 6 FAIL (bessel_6.f90 = PR124819)
check-target-libgomp-fortran: 1182 passes, 0 FAIL
  libgomp.fortran/fortran.exp:      ran
  libgomp.oacc-fortran/fortran.exp: ran
Zero new FAIL/XPASS vs unpatched trunk.
```

## Affected Versions

| Branch | Reproduces? | Notes |
|--------|-------------|-------|
| trunk (r16-xxxx) | yes | never worked; architectural gap since 2008 |

Not a regression.  The regression label on Bugzilla should be dropped.
