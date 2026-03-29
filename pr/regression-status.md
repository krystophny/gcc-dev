# Fortran Regression Status

Checked against `upstream/master` at `a3b49ec48b7` on 2026-03-29.

`Patch on Bugzilla` means a patch is actually posted on Bugzilla.
It does not just mean `patch-ready` on the fork.

## Merged on trunk / resolved

| PR | P | Summary | State | BZ |
|---|---:|---|---|---|
| 82721 | P4 | Corrupted text / ICE | merged on trunk; BZ still `NEW` | [82721](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82721) |
| 84779 | P4 | ICE with `-fdefault-integer-8` + `ENTRY` | fixed on trunk indirectly; BZ still `NEW` | [84779](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84779) |
| 95338 | P4 | ICE in `component_ref` conversion | merged on trunk; BZ still `NEW` | [95338](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95338) |
| 102459 | P4 | ICE in `gfc_conv_scalarized_array_ref` | merged on trunk; BZ still `NEW` | [102459](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102459) |
| 102596 | P4 | ICE in `gfc_omp_clause_default_ctor` | merged on trunk; BZ still `NEW` | [102596](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102596) |
| 102619 | P4 | ICE in `gfc_conv_descriptor_dtype` | merged on trunk; backports pending | [102619](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102619) |
| 106946 | P4 | ICE in `resolve_component` | merged on trunk; BZ `RESOLVED FIXED` | [106946](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=106946) |
| 120286 | P3 | OpenMP double free class pointers | merged on trunk; BZ still `NEW` | [120286](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120286) |
| 120723 | P3 | OpenACC ICE on `attach(scalar)` | merged on trunk; BZ still `NEW` | [120723](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120723) |
| 121743 | P3 | ICE in `build_function_decl` | BZ `RESOLVED FIXED` | [121743](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121743) |
| 122491 | P4 | ASAN UAF in missing `END BLOCK` recovery | merged on trunk; BZ `RESOLVED FIXED` | [122491](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=122491) |
| 123255 | P3 | OpenACC allocatable-component size regression | BZ `RESOLVED WORKSFORME` | [123255](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123255) |
| 123868 | P3 | Leak on nested allocatable assignment | merged on trunk; BZ `RESOLVED FIXED` | [123868](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123868) |
| 123943 | P4 | ICE in nested `BLOCK` / `DO CONCURRENT` | merged on trunk; BZ `RESOLVED FIXED` | [123943](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123943) |
| 123947 | P4 | ICE in `gfc_build_addr_expr` | merged on trunk; BZ `RESOLVED FIXED` | [123947](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123947) |
| 123949 | P4 | PDT ICE in `gfc_match_decl_type_spec` | merged on trunk; BZ `RESOLVED FIXED` | [123949](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123949) |
| 124161 | P4 | ICE in `fold_convert_loc` with submodule TBP | BZ `RESOLVED FIXED` | [124161](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124161) |
| 124208 | P4 | ICE in nested `ASSOCIATE/BLOCK` | merged on trunk; BZ `RESOLVED FIXED` | [124208](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124208) |
| 124235 | P4 | ICE in `ALLOCATE` of sub-objects | merged on trunk; BZ `RESOLVED FIXED` | [124235](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124235) |
| 124482 | P4 | SEGV in `resolve_cyclic_derived_type` | merged on trunk; BZ `RESOLVED FIXED` | [124482](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124482) |
| 119273 | P4 | subclass access in `associate` | merged on trunk and release branches | [119273](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=119273) |
| 124631 | P4 | UBSAN in `gfc_simplify_eoshift` | merged on trunk; BZ still `ASSIGNED` | [124631](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124631) |
| 95879 | P4 | UAF / ICE in `gfc_resolve_formal_arglist` | merged on trunk; backports pending | [95879](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95879) |
| 84245 | P4 | ICE in `delete_root` | merged on trunk; BZ `RESOLVED FIXED` | [84245](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84245) |
| 124512 | P1 | `libgfortran` shmem CAF pthread support | merged on trunk; BZ `RESOLVED FIXED` | [124512](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124512) |

## Patch on Bugzilla

| PR | P | Summary | State | BZ |
|---|---:|---|---|---|
| 108382 | P4 | wrong parsing with mixed acc/omp | patch on BZ; full `check-gfortran` clean on patch branch | [108382](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=108382) |
| 124661 | P4 | SIGSEGV with `-fcheck=bounds` | patch on BZ as attachment 64058; full `check-gfortran` clean on patch branch | [124661](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124661) |
| 102430 | P2 | ICE in OMP `linear(array)` | patch on BZ; also on ML; still open on trunk | [102430](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102430) |

## Still open

| PR | P | Summary | Notes | BZ |
|---|---:|---|---|---|
| 42954 | P5 | `TARGET_*_CPP_BUILTINS` issues | has upstream patch; not Fortran-specific | [42954](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=42954) |
| 60576 | P4 | `assumed_rank_7.f90` FAIL | `WAITING` on BZ | [60576](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=60576) |
| 79524 | P4 | valgrind error for `fimplicit_none_2.f90` | valgrind-only | [79524](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=79524) |
| 85352 | P4 | wrong error in spec expr with `ENTRY` | rejects valid code | [85352](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=85352) |
| 87352 | P4 | large stack usage | 204 MB object, 205 MB stack | [87352](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=87352) |
| 93554 | P4 | ICE in `expand_oacc_for` | alloc component in acc loop private | [93554](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93554) |
| 93715 | P4 | ICE in `gfc_trans_auto_array_allocation` | coarray + async read | [93715](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93715) |
| 93814 | P4 | ICE in `build_entry_thunks` | `BIND(C)` CHAR result + `ENTRY` | [93814](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93814) |
| 93832 | P4 | ICE in `gfc_convert_to_structure_constructor` | self-ref type in bounds | [93832](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93832) |
| 94978 | P4 | bogus out-of-bounds warning | valid code, spurious warning | [94978](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=94978) |
| 96986 | P4 | wrong `volatile` error for `ENTRY` | rejects valid code | [96986](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96986) |
| 100155 | P4 | ICE in `gfc_conv_intrinsic_size` | `class(*)` recursive + `size()` | [100155](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=100155) |
| 100194 | P4 | ICE in `gfc_trans_create_temp_array` | assumed-rank contiguous | [100194](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=100194) |
| 101760 | P4 | ICE in `make_ssa_name_fn` | open, no patch | [101760](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=101760) |
| 102314 | P4 | ICE in `verify_ssa` | now ICEs at `-O0` too | [102314](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102314) |
| 102333 | P4 | invalid `PROCEDURE` statement accepted | comment 1 already rejected on clean trunk; attachment 64064 is too broad and should be obsoleted; Paul's simpler `decl.cc` line is a no-op | [102333](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102333) |
| 103367 | P4 | ICE in `gfc_conv_array_initializer` | PDT array + `REAL` index | [103367](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103367) |
| 105168 | P4 | ICE in `gfc_maybe_dereference_var` | CLASS array + `size()` in result | [105168](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=105168) |
| 107425 | P4 | ICE in `gimplify_var_or_parm_decl` | undeclared var in OMP iterator | [107425](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107425) |
| 109788 | P4 | runtime error: shift exponent 64 | open, no patch | [109788](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=109788) |
| 110626 | P4 | duplicated finalization in derived | open, no patch | [110626](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110626) |
