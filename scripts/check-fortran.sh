#!/bin/sh
set -eu

usage() {
  cat >&2 <<'EOF'
usage: scripts/check-fortran.sh [--build-dir DIR] [--gcc-src DIR] [--] [RUNTESTFLAGS...]

Runs the GCC Fortran frontend tests with a generated no-space wrapper for
the rebuilt gfortran.  Extra arguments are appended to RUNTESTFLAGS, e.g.:

  scripts/check-fortran.sh dg.exp=pr42954-linux.f90
  scripts/check-fortran.sh gomp.exp
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
gfortran=$gcc_build/gfortran
summary=$gcc_build/testsuite/gfortran/gfortran.sum
log=$gcc_build/testsuite/gfortran/gfortran.log
include_dir=$(find "$build_dir" -path '*/libgfortran/include' -type d | head -n 1)
caf_lib_dir=$(find "$build_dir" -path '*/libgfortran/.libs' -type d | head -n 1)
wrapper=${TMPDIR:-/tmp}/gcc-dev-gfortran-under-test.$$

[ -x "$gfortran" ] || { echo "error: missing rebuilt compiler: $gfortran" >&2; exit 2; }
[ -d "$testsuite_src" ] || { echo "error: missing testsuite source: $testsuite_src" >&2; exit 2; }
[ -d "$include_dir" ] || { echo "error: missing libgfortran include dir: $include_dir" >&2; exit 2; }
[ -d "$caf_lib_dir" ] || { echo "error: missing caf library dir: $caf_lib_dir" >&2; exit 2; }

cleanup() {
  rm -f "$wrapper"
}
trap cleanup EXIT HUP INT TERM

{
  echo '#!/bin/sh'
  printf 'exec "%s" -B"%s/" -I"%s" -L"%s" "$@"\n' \
    "$gfortran" "$gcc_build" "$include_dir" "$caf_lib_dir"
} > "$wrapper"
chmod +x "$wrapper"

rm -f "$summary" "$log"

runtest_flags="--srcdir=$testsuite_src GFORTRAN_UNDER_TEST=$wrapper"
if [ -n "$extra_flags" ]; then
  runtest_flags="$runtest_flags $extra_flags"
fi

set +e
make -C "$gcc_build" -k check-fortran RUNTESTFLAGS="$runtest_flags"
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
if grep -q '/usr/bin/gfortran' "$summary" "$log" 2>/dev/null \
   || grep -q '^Executing on host: gfortran ' "$log" 2>/dev/null; then
  echo "error: test harness used system gfortran" >&2
  exit 1
fi
if grep -qE '^(FAIL|XPASS|UNRESOLVED|ERROR):' "$summary"; then
  grep -E '^(FAIL|XPASS|UNRESOLVED|ERROR):' "$summary" >&2
  exit 1
fi

exit "$status"
