#!/usr/bin/env bash
set -euo pipefail

build_dir=/home/ert/code/gcc-dev/gcc-bisect-build
src_dir=/home/ert/code/gcc-dev/gcc-bisect
src=/home/ert/code/gcc-dev/pr/84779/bisect/reproducer-entry4.f90
configure_log=/tmp/pr84779-bisect-configure.log
build_log=/tmp/pr84779-bisect-build.log
compile_log=/tmp/pr84779-bisect-compile.log

(
  cd "$build_dir"
  "$src_dir/configure" \
    --enable-languages=fortran \
    --disable-multilib \
    --disable-bootstrap \
    CFLAGS='-Og -g' \
    CXXFLAGS='-Og -g'
) >"$configure_log" 2>&1 || exit 125

find "$build_dir/gcc" \
  \( -name '*.o' -o -name '*.a' -o -name '*.so' -o -name '*.lo' -o -name '*.lai' \) \
  -delete
rm -f "$build_dir"/gcc/{cc1,cc1plus,f951,gfortran,lto1,collect2,xgcc}

make -C "$build_dir/gcc" -j32 f951 gfortran >"$build_log" 2>&1 || true

if [[ ! -x "$build_dir/gcc/gfortran" ]]; then
  exit 125
fi

"$build_dir/gcc/gfortran" -B "$build_dir/gcc" \
  -O1 -fdefault-integer-8 -c "$src" -o /tmp/pr84779-bisect.o \
  >"$compile_log" 2>&1 && exit 0

if rg -qi 'internal compiler error|segmentation fault|abort' "$compile_log"; then
  exit 1
fi

exit 125
