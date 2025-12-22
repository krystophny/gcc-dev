# PR123254 - OpenACC present() on DT dummy arg (worksforme)

**Title:** OpenACC: SIGSEGV in GOACC_parallel_keyed when using present() clause
for derived type dummy argument

**Bugzilla:** https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123254

## Status

This no longer reproduces locally as of 2025-12-22 using trunk based on
`upstream/master` commit `769041822723208bf85a91ac409b9b0bdae3fff0`.

## Evidence (local)

- Host run (expected `y(1) = 2.0`): `/tmp/pr123254_run_host.log`
- NVPTX run (expected `y(1) = 2.0`): `/tmp/pr123254_run_nvptx.log`
- Host run without `/opt` runtime override: `/tmp/pr123254_run_host_system_libgomp.log`

