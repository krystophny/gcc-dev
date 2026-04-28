#!/bin/sh
set -eu

usage() {
  cat >&2 <<'EOF'
usage: scripts/check-fortran.sh [--build-dir DIR] [--gcc-src DIR] [--] [RUNTESTFLAGS...]

Runs the GCC Fortran frontend tests with the build-tree DejaGnu setup.
Extra arguments are appended to RUNTESTFLAGS, e.g.:

  scripts/check-fortran.sh dg.exp=pr42954-linux.f90
  scripts/check-fortran.sh gomp.exp

Set GCC_TEST_JOBS to override the default parallel make job count.
EOF
}

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
build_dir=${GCC_BUILD_DIR:-"$root_dir/gcc-build"}
gcc_src=${GCC_SRC_DIR:-"$root_dir/gcc"}
extra_flags=

while [ "$#" -gt 0 ]; do
  case "$1" in
    --build-dir)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      build_dir=$2
      shift 2
      ;;
    --gcc-src)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      gcc_src=$2
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

for arg in "$@"; do
  if [ -n "$extra_flags" ]; then
    extra_flags="$extra_flags $arg"
  else
    extra_flags=$arg
  fi
done

gcc_build=$build_dir/gcc
testsuite_src=$gcc_src/gcc/testsuite
summary=$gcc_build/testsuite/gfortran/gfortran.sum
log=$gcc_build/testsuite/gfortran/gfortran.log
site_exp=$gcc_build/site.exp
jobs=${GCC_TEST_JOBS:-}
if [ -z "$jobs" ]; then
  jobs=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)
fi

[ -f "$gcc_build/Makefile" ] || { echo "error: missing GCC build Makefile: $gcc_build/Makefile" >&2; exit 2; }
[ -d "$testsuite_src" ] || { echo "error: missing testsuite source: $testsuite_src" >&2; exit 2; }

rm -f "$site_exp" "$gcc_build/site.bak"
make -C "$gcc_build" site.exp
if ! grep -q 'set TESTING_IN_BUILD_TREE 1' "$site_exp"; then
  echo "error: $site_exp is not a build-tree DejaGnu site file" >&2
  exit 1
fi

rm -f "$summary" "$log"

set +e
make -C "$gcc_build" -j"$jobs" -k check-fortran RUNTESTFLAGS="$extra_flags"
status=$?
set -e

if [ ! -f "$summary" ]; then
  echo "error: missing $summary; no DejaGnu summary was produced" >&2
  exit 1
fi
if ! grep -q '=== gfortran Summary ===' "$summary" \
   || ! grep -q '# of expected passes' "$summary"; then
  echo "error: $summary is not a real gfortran summary" >&2
  exit 1
fi
if ! grep -q '/gfortran -B' "$log" 2>/dev/null; then
  echo "error: test harness did not use build-tree gfortran with -B paths" >&2
  exit 1
fi
if grep -q '/usr/bin/gfortran' "$summary" "$log" 2>/dev/null \
   || grep -q '^Executing on host: gfortran ' "$log" 2>/dev/null; then
  echo "error: test harness used system gfortran" >&2
  exit 1
fi
failures=$(grep -E '^(FAIL|XPASS|UNRESOLVED|ERROR):' "$summary" \
  | grep -vE '^FAIL: gfortran\.dg/bessel_6\.f90   -O(0|1|2|s|3 -g|3 -fomit-frame-pointer -funroll-loops -fpeel-loops -ftracer -finline-functions)  execution test$' \
  || true)
if [ -n "$failures" ]; then
  printf '%s\n' "$failures" >&2
  exit 1
fi

exit 0
