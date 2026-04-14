# Bug 124751: Wrong-code after packing assumed-rank actuals for contiguous dummies

- **Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124751
- **GitHub issue:** https://github.com/krystophny/gcc-dev/issues/114

## Description

`PR100194` was fixed on April 1, 2026 by
`r16-8375-g89293f0c2c091db384a7519e4ed56e8f37ef403f`, which removed the
original ICE for assumed-rank actual arguments passed to contiguous
assumed-rank dummies.

That change left a wrong-code regression in the new repacking path.
The frontend packs the data with `_gfortran_internal_pack`, but for
assumed-rank descriptors it reused stale stride and offset metadata from
the original noncontiguous actual argument.

The fix builds a descriptor for the packed temporary before the call.
