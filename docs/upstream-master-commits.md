# GCC trunk commits — Christopher Albert

This page lists every commit signed off by Christopher Albert
(`albert@tugraz.at`) that is currently merged on `master` of the upstream
GCC repository. Snapshot date: 2026-06-11. Total: 46 commits.

Commit hashes link to the [gcc-mirror/gcc](https://github.com/gcc-mirror/gcc)
GitHub mirror, which tracks `git://gcc.gnu.org/git/gcc.git` 1:1. Bugzilla
PR numbers refer to [gcc.gnu.org/bugzilla](https://gcc.gnu.org/bugzilla/).

## Model attribution

The upstream `Assisted-by:` trailer was not yet part of my workflow when most
of these commits landed, so it is absent from the recorded message. During
development of every entry below I used both Anthropic Claude (Claude Code,
Opus 4.x / Sonnet 4.x) and OpenAI GPT-5 (Codex CLI) together: typically
Claude for repository navigation, hypothesis formation and patch drafting,
and GPT-5 for review, alternative diagnostics and adversarial cross-checks.
Final patches, ChangeLog entries and Bugzilla / mailing-list submissions
were authored, edited and validated by me.

All commits below predate the GCC steering committee's AI contributions
policy (2026), which now declines legally significant LLM-derived code
contributions. New fixes therefore land on the downstream fork
[lazy-fortran/gcc](https://github.com/lazy-fortran/gcc) instead of upstream
GCC, under a repository-level AI policy plus `Assisted-by:` lines on the
squashed fix commits.
Existing upstream commits are preserved verbatim and not rewritten.

Where an upstream commit also carries `Co-authored-by:` or `Suggested-by:`
trailers (a few have one), those are reproduced below for completeness.

## Commits, newest first

- 2026-04-11 — [`e41fd0a9`](https://github.com/gcc-mirror/gcc/commit/e41fd0a99aee94734537c067f96e3502628125c6) — fortran: Fix ICE in remap_type with deferred-length character in OMP target [PR101760, PR102314] — *Claude and GPT*
- 2026-04-08 — [`326fe37d`](https://github.com/gcc-mirror/gcc/commit/326fe37d6981c189fb0f2a5a4ab7f7a5b95ecf89) — fortran: Diagnose invalid array initializer after parameter substitution [PR103367] — *Claude and GPT*
- 2026-04-03 — [`010618b8`](https://github.com/gcc-mirror/gcc/commit/010618b8dcb73220790f8f82cf76e8a2aacc2122) — fortran: Fix ICE in expand_oacc_for with private derived type [PR93554] — *Claude and GPT*
- 2026-04-03 — [`d26055fe`](https://github.com/gcc-mirror/gcc/commit/d26055fec8ef07d9b998ec3217b25507ad080fcf) — fortran: Fix ICE with implicit variable in iterator depend clause [PR107425] — *Claude and GPT*
- 2026-04-03 — [`7660e306`](https://github.com/gcc-mirror/gcc/commit/7660e3067481159acc3ad76cfae22f71606670c7) — fortran: Clean up charlens after rejected parameter arrays [PR79524] — *Claude and GPT*
- 2026-04-03 — [`37e55123`](https://github.com/gcc-mirror/gcc/commit/37e551236bbf10ab631344d7370ed601a95c205e) — fortran: Add testcase [PR98203] — *Claude and GPT*
- 2026-04-01 — [`b8078514`](https://github.com/gcc-mirror/gcc/commit/b807851428512039bf827426e2143cc80d7c2463) — fortran: Fix assumed-rank repacking for contiguous dummies [PR124751] — *Claude and GPT* — Co-authored-by: Paul Thomas <pault@gcc.gnu.org>
- 2026-03-31 — [`0ea3035f`](https://github.com/gcc-mirror/gcc/commit/0ea3035ffbf1bfbc0274673fce367e9f6c6bc8e7) — fortran: Fix ICE in build_entry_thunks with CHARACTER bind(c) ENTRY [PR93814] — *Claude and GPT*
- 2026-03-31 — [`89293f0c`](https://github.com/gcc-mirror/gcc/commit/89293f0c2c091db384a7519e4ed56e8f37ef403f) — fortran: Fix ICE in gfc_trans_create_temp_array for assumed-rank [PR100194] — *Claude and GPT*
- 2026-03-29 — [`a9a1ed34`](https://github.com/gcc-mirror/gcc/commit/a9a1ed349974f03e9ba32dc21cce7e20cd7119ee) — fortran: Fix ICE in gfc_conv_array_initializer with invalid index [PR103367] — *Claude and GPT*
- 2026-03-29 — [`6be9db00`](https://github.com/gcc-mirror/gcc/commit/6be9db000810a44c5b6b5af320723b3af175bb8a) — fortran: Fix false explicit-interface-required for ENTRY with volatile [PR96986] — *Claude and GPT*
- 2026-03-29 — [`2b0a29a9`](https://github.com/gcc-mirror/gcc/commit/2b0a29a94c9946e32cf76f4f65da368b4f005566) — fortran: Fix ICE in gfc_trans_auto_array_allocation with scalar coarray [PR93715] — *Claude and GPT*
- 2026-03-28 — [`bd0134b0`](https://github.com/gcc-mirror/gcc/commit/bd0134b028968788165c515196dd8b179a889879) — fortran: Accept valid ENTRY specification expressions [PR85352] — *Claude and GPT*
- 2026-03-28 — [`790671b7`](https://github.com/gcc-mirror/gcc/commit/790671b708400d1fc6bb1abbf1601f3616e8220d) — fortran: Avoid bogus do-subscript warnings in skipped inner loops [PR94978] — *Claude and GPT*
- 2026-03-28 — [`ebc8ed32`](https://github.com/gcc-mirror/gcc/commit/ebc8ed3246ff5949c2e4cf8af6726c5111ef381f) — fortran: Fix character SPREAD intrinsic lowering [PR109788] — *Claude and GPT*
- 2026-03-22 — [`3d4039e9`](https://github.com/gcc-mirror/gcc/commit/3d4039e95d851b8543884962ecf1a8e9e20669a8) — fortran: Fix free-form mixed OpenACC/OpenMP continuation state [PR108382] — *Claude and GPT*
- 2026-03-20 — [`f57bcde8`](https://github.com/gcc-mirror/gcc/commit/f57bcde8598395f6e6aac50bc388352af76b8125) — libgfortran: Disable caf_shmem without usable process-shared pthreads [PR124512] — *Claude and GPT*
- 2026-03-13 — [`d8b00bf2`](https://github.com/gcc-mirror/gcc/commit/d8b00bf2e1514cd132a9febaa9849ab46cd316f5) — fortran: Fix use-after-free in CLASS component error recovery [PR124482] — *Claude and GPT*
- 2026-03-11 — [`34527d8b`](https://github.com/gcc-mirror/gcc/commit/34527d8b0b8c5ee53b0ff92812f9c9e78a562bec) — fortran: Add testcase [PR104827] — *Claude and GPT*
- 2026-03-11 — [`1cfd4447`](https://github.com/gcc-mirror/gcc/commit/1cfd44476e48750dad0a39b5c5c76a6c8bcb760f) — fortran: Add testcase [PR103139] — *Claude and GPT*
- 2026-03-11 — [`8a0a1a0c`](https://github.com/gcc-mirror/gcc/commit/8a0a1a0c7b187415e34dcf7a5cbf5e314c9de78a) — fortran: Add testcase [PR102333] — *Claude and GPT*
- 2026-03-11 — [`67431721`](https://github.com/gcc-mirror/gcc/commit/67431721378391be7cb774c789a8da10c0f827ee) — fortran: Add testcase [PR95163] — *Claude and GPT*
- 2026-03-11 — [`d0128de5`](https://github.com/gcc-mirror/gcc/commit/d0128de52fc637efd768d28dbd4edb7bc680a97b) — fortran: Add testcase [PR84779] — *Claude and GPT*
- 2026-03-10 — [`0af96138`](https://github.com/gcc-mirror/gcc/commit/0af9613810ecdc991633f58f5dd81a574aa2af31) — fortran: Fix scalar OpenACC attach/detach lowering [PR120723] — *Claude and GPT*
- 2026-03-10 — [`b018656f`](https://github.com/gcc-mirror/gcc/commit/b018656f8c016d1880d57ee79266cdecf98f41fa) — fortran: Fix class dummy-array assignment deep copy [PR110877] — *Claude and GPT*
- 2026-03-10 — [`60fbabc1`](https://github.com/gcc-mirror/gcc/commit/60fbabc1a182cca77d14c68a1b623c554310d135) — fortran: Preserve scalar class pointers in OpenMP privatization [PR120286] — *Claude and GPT*
- 2026-03-10 — [`490c7ba8`](https://github.com/gcc-mirror/gcc/commit/490c7ba8d880f5a89d25c2791e4b8a95c533c45c) — fortran: Fix mixed ENTRY union ABI under -ff2c [PR95338] — *Claude and GPT*
- 2026-03-10 — [`e53a7510`](https://github.com/gcc-mirror/gcc/commit/e53a7510be51139ff4297e65e69895a6243caa9d) — Fortran: Allow task-reduction allocatable scalars without outer ref [PR102596] — *Claude and GPT*
- 2026-03-10 — [`d2ab04fb`](https://github.com/gcc-mirror/gcc/commit/d2ab04fbba7b97d17e4f9e0885d71a4e1faafc96) — fortran: Fix OpenMP iterator depend lowering for component arrays [PR102459] — *Claude and GPT*
- 2026-03-10 — [`5cfaad50`](https://github.com/gcc-mirror/gcc/commit/5cfaad50af7dc25f6174044cdc05ebd56b6c4e3c) — Fortran: Fix ICE after rejected CHARACTER duplicate declaration [PR82721] — *Claude and GPT*
- 2026-03-10 — [`0d0fbb0a`](https://github.com/gcc-mirror/gcc/commit/0d0fbb0a01e4e77e274e0ff9b54506a495a7bdef) — Fortran: Fix ICE on invalid CLASS component in derived type [PR106946] — *Claude and GPT*
- 2026-02-25 — [`e0b70284`](https://github.com/gcc-mirror/gcc/commit/e0b70284cfac5b7a96f42e340b4c287fba7f8734) — fortran: Fix ICE in ALLOCATE of sub-objects with recursive types [PR121628 follow-up] — *Claude and GPT*
- 2026-02-23 — [`97965bdc`](https://github.com/gcc-mirror/gcc/commit/97965bdc1ed36f97a6e2ec2ee7bc208dd05d8c18) — fortran: Fix iterator counting in nested block scopes [PR124208] — *Claude and GPT*
- 2026-02-22 — [`33b945b4`](https://github.com/gcc-mirror/gcc/commit/33b945b4e637f4e46e0c3bc42bded2949124c940) — fortran: Initialize gfc_se in PDT component allocation [PR123949] — *Claude and GPT*
- 2026-02-19 — [`3a17cc11`](https://github.com/gcc-mirror/gcc/commit/3a17cc11cb5543be553774819c0a454b57ef739b) — Fortran: Fix PDT ICE with large KIND values [PR123949] — *Claude and GPT*
- 2026-02-18 — [`ff2f6c51`](https://github.com/gcc-mirror/gcc/commit/ff2f6c5153ecc142e1821a26b4a5184b4fe30607) — Fortran: Fix heap-use-after-free during malformed END recovery [PR123947] — *Claude and GPT* — Suggested-by: Jakub Jelinek <jakub@redhat.com>
- 2026-02-12 — [`edced0fe`](https://github.com/gcc-mirror/gcc/commit/edced0fe1e28a37c75b4e2c80a2a12db93d5002c) — fortran: Fix DO CONCURRENT nested-in-block iterator counting [PR123943] — *Claude and GPT* — Co-authored-by: Harald Anlauf <anlauf@gcc.gnu.org>
- 2026-01-30 — [`ca448bc5`](https://github.com/gcc-mirror/gcc/commit/ca448bc5e435a2076cb3683a9be823c08a14e69e) — Fortran: Fix double deep-copy of nested allocatable arrays [PR123868] — *Claude and GPT*
- 2025-12-21 — [`4f40d3a5`](https://github.com/gcc-mirror/gcc/commit/4f40d3a5b0db1041f79b375cafb92a029f6dd742) — fortran: Reject array/allocatable LINEAR on DO [PR102430] — *Claude and GPT*
- 2025-12-04 — [`15ffee4e`](https://github.com/gcc-mirror/gcc/commit/15ffee4e129937c07190bc2ce059470bbd8068ae) — fortran: Fix bogus warning with -cpp -fpreprocessed [PR92613] — *Claude and GPT*
- 2025-11-25 — [`c50d263b`](https://github.com/gcc-mirror/gcc/commit/c50d263beff78ab1133ccff1de78a50ea4851d7e) — fortran: Honor array constructor type-spec during folding [PR107721] — *Claude and GPT* — Co-authored-by: Harald Anlauf <anlauf@gcc.gnu.org>
- 2025-11-17 — [`7db49bf4`](https://github.com/gcc-mirror/gcc/commit/7db49bf4be2e5ec2d13b53963d33172c4a347b83) — fortran: Enforce spec statement ordering [PR32365] — *Claude and GPT*
- 2025-11-11 — [`5e62a23c`](https://github.com/gcc-mirror/gcc/commit/5e62a23cc3a64fa0312ffa414fcd1aaba18baa02) — fortran: Implement optional type spec for DO CONCURRENT [PR96255] — *Claude and GPT* — Co-authored-by: Steve Kargl <kargl@gcc.gnu.org>, Jerry DeLisle <jvdelisle@gcc.gnu.org>
- 2025-11-07 — [`a1fe2cfa`](https://github.com/gcc-mirror/gcc/commit/a1fe2cfa8965ac298f6541d46b90156b1cb34726) — fortran: Fix recursive deep-copy seen-set re-entry [PR121628] — *Claude and GPT*
- 2025-11-07 — [`1eb696fc`](https://github.com/gcc-mirror/gcc/commit/1eb696fc092ac39cdb55933b20ee25a99d63b907) — fortran: Fix ICE and self-assignment bugs with recursive allocatable finalizers [PR90519] — *Claude and GPT*
- 2025-11-06 — [`9636d90e`](https://github.com/gcc-mirror/gcc/commit/9636d90e4326003e6da1ea86df7c730852629920) — fortran: Implement deep copy for recursive allocatable derived types [PR121628] — *Claude and GPT*

## How this list is generated

```bash
# inside gcc-dev/gcc
git fetch upstream master
git log master --grep='Signed-off-by: Christopher Albert' \
    --pretty='%H %ai %s'
```

The same query against `%(trailers:only)` produces the per-commit
`Co-authored-by` / `Suggested-by` trailers reproduced above.
