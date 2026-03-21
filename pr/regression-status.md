# Fortran Regression Status

Checked against `upstream/master` at `a60cf319b6c` on 2026-03-21.

`Patch on Bugzilla` means a patch is actually posted on Bugzilla.
It does not just mean `patch-ready` on the fork.

## Merged On Trunk / Resolved

| PR | Summary | State now | Links |
|---|---|---|---|
| 82721 | Corrupted text / ICE | merged on trunk; Bugzilla still `NEW` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82721) · [GH #56](https://github.com/krystophny/gcc-dev/issues/56) |
| 84779 | ICE with `-fdefault-integer-8` + `ENTRY` | fixed on trunk indirectly; Bugzilla still `NEW` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84779) · [GH #103](https://github.com/krystophny/gcc-dev/issues/103) |
| 95338 | ICE non-trivial conversion in `component_ref` | merged on trunk; Bugzilla still `NEW` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95338) · [GH #68](https://github.com/krystophny/gcc-dev/issues/68) |
| 102459 | ICE in `gfc_conv_scalarized_array_ref` | merged on trunk; Bugzilla still `NEW` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102459) · [GH #79](https://github.com/krystophny/gcc-dev/issues/79) |
| 102596 | ICE in `gfc_omp_clause_default_ctor` | merged on trunk; Bugzilla still `NEW` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102596) · [GH #80](https://github.com/krystophny/gcc-dev/issues/80) |
| 106946 | ICE in `resolve_component` | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=106946) · [GH #88](https://github.com/krystophny/gcc-dev/issues/88) |
| 120286 | OpenMP double free class pointers | merged on trunk; Bugzilla still `NEW` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120286) · [GH #95](https://github.com/krystophny/gcc-dev/issues/95) |
| 120723 | OpenACC ICE on `attach(scalar)` | merged on trunk in [`0af9613810e`](https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=0af9613810ecdc991633f58f5dd81a574aa2af31); Bugzilla still `NEW` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120723) · [GH #96](https://github.com/krystophny/gcc-dev/issues/96) |
| 122491 | ASAN UAF in missing `END BLOCK` recovery | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=122491) · [GH #50](https://github.com/krystophny/gcc-dev/issues/50) |
| 123255 | OpenACC allocatable-component size regression | Bugzilla `RESOLVED WORKSFORME` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123255) |
| 123868 | Memory leak on assignment with nested allocatables | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123868) · [GH #47](https://github.com/krystophny/gcc-dev/issues/47) |
| 123943 | `DO CONCURRENT` nested-in-`BLOCK` iterator-counting ICE | merged on trunk in [`edced0fe1e2`](https://gcc.gnu.org/git/?p=gcc.git;a=commit;h=edced0fe1e28a37c75b4e2c80a2a12db93d5002c); Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123943) |
| 123947 | ICE in `gfc_build_addr_expr` | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123947) · [GH #48](https://github.com/krystophny/gcc-dev/issues/48) |
| 123949 | PDT ICE in `gfc_match_decl_type_spec` | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123949) · [GH #49](https://github.com/krystophny/gcc-dev/issues/49) |
| 124208 | ICE in `gfc_resolve_forall` with nested `ASSOCIATE/BLOCK` | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124208) · [GH #100](https://github.com/krystophny/gcc-dev/issues/100) |
| 124235 | ICE in `ALLOCATE` of sub-objects | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124235) · [GH #51](https://github.com/krystophny/gcc-dev/issues/51) |
| 124482 | SEGV in `resolve_cyclic_derived_type` | merged on trunk; Bugzilla `RESOLVED FIXED` | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124482) · [GH #102](https://github.com/krystophny/gcc-dev/issues/102) |

## Patch On Bugzilla

| PR | Summary | State now | Links |
|---|---|---|---|
| 124512 | `libgfortran` shmem CAF lacks usable process-shared pthread support | `P1`; patch on Bugzilla; still open on trunk; not on mailing list | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124512) · [GH #104](https://github.com/krystophny/gcc-dev/issues/104) |
| 102430 | ICE in `fold_convert_loc` for OpenMP `linear(array)` | `P2`; patch on Bugzilla; also on mailing list; still open on trunk | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102430) · [GH #9](https://github.com/krystophny/gcc-dev/issues/9) |
| 95879 | UAF / ICE in `gfc_resolve_formal_arglist` | `P4`; patch on Bugzilla; still open on trunk; not on mailing list | [Bugzilla](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95879) · [GH #69](https://github.com/krystophny/gcc-dev/issues/69) |

## Still Open

| PR | Summary | Note | Bugzilla |
|---|---|---|---|
| 42954 | `TARGET_*_CPP_BUILTINS` issues | has upstream patch; not Fortran-specific | [42954](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=42954) |
| 60576 | `assumed_rank_7.f90` FAIL | `WAITING` on Bugzilla | [60576](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=60576) |
| 79524 | valgrind error for `fimplicit_none_2.f90` | valgrind-only | [79524](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=79524) |
| 84245 | ICE in `delete_root` | error-recovery family; same general area as PR106946 | [84245](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=84245) |
| 85352 | wrong error for dummy in spec expr with `ENTRY` | rejects valid code | [85352](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=85352) |
| 87352 | large stack usage | very large object / stack usage | [87352](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=87352) |
| 93554 | ICE in `expand_oacc_for` | allocatable component in OpenACC loop private | [93554](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93554) |
| 93715 | ICE in `gfc_trans_auto_array_allocation` | coarray + async read | [93715](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93715) |
| 93814 | ICE in `build_entry_thunks` | `BIND(C)` character result + `ENTRY` | [93814](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93814) |
| 93832 | ICE in `gfc_convert_to_structure_constructor` | self-referential type in array bounds | [93832](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=93832) |
| 94978 | bogus out-of-bounds warning | valid code; spurious warning | [94978](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=94978) |
| 96986 | wrong `volatile` error for `ENTRY` | rejects valid code | [96986](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96986) |
| 100155 | ICE in `gfc_conv_intrinsic_size` | `class(*)` recursive + `size()` | [100155](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=100155) |
| 100194 | ICE in `gfc_trans_create_temp_array` | assumed-rank `contiguous` case | [100194](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=100194) |
| 101760 | ICE in `make_ssa_name_fn` | open; no patch | [101760](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=101760) |
| 102314 | ICE in `verify_ssa` | now ICEs at `-O0` too | [102314](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102314) |
| 102619 | ICE in `gfc_conv_descriptor_dtype` | assumed-rank + `product(shape())` | [102619](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=102619) |
| 103367 | ICE in `gfc_conv_array_initializer` | PDT array + `REAL` index | [103367](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103367) |
| 105168 | ICE in `gfc_maybe_dereference_var` | CLASS array + `size()` in result | [105168](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=105168) |
| 107425 | ICE in `gimplify_var_or_parm_decl` | undeclared var in OpenMP iterator | [107425](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=107425) |
| 108382 | wrong parsing with mixed acc/omp | continuation line misclassified | [108382](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=108382) |
| 109788 | runtime error: shift exponent 64 | open; no patch | [109788](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=109788) |
| 110626 | duplicated finalization in derived | open; no patch | [110626](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110626) |
| 119273 | subclass access in `associate` | wrong index with `-fcheck=bounds` | [119273](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=119273) |
| 121743 | ICE in `build_function_decl` | coarray `-fcoarray=lib` | [121743](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121743) |
| 124161 | ICE in `fold_convert_loc` with submodule TBP | polymorphic dispatch | [124161](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=124161) |
