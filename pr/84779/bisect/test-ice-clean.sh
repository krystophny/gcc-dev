#!/usr/bin/env bash
set -euo pipefail

src_dir=/home/ert/code/gcc-dev/gcc-bisect
build_dir=/home/ert/code/gcc-dev/gcc-bisect-build-clean
src1=/home/ert/code/gcc-dev/pr/84779/bisect/reproducer-entry4.f90
src2=/home/ert/code/gcc-dev/pr/84779/bisect/reproducer-comment13.f90
configure_log=/tmp/pr84779-bisect-clean-configure.log
build_log=/tmp/pr84779-bisect-clean-build.log
compile1_log=/tmp/pr84779-bisect-clean-entry4.log
compile2_log=/tmp/pr84779-bisect-clean-comment13.log

rm -rf "$build_dir"
mkdir -p "$build_dir"

(
  cd "$build_dir"
  "$src_dir/configure" \
    --enable-languages=fortran \
    --disable-multilib \
    --disable-bootstrap \
    CFLAGS='-Og -g' \
    CXXFLAGS='-Og -g'
) >"$configure_log" 2>&1 || exit 125

make -C "$build_dir" -j32 all-gcc >"$build_log" 2>&1 || exit 125

"$build_dir/gcc/gfortran" -B "$build_dir/gcc" \
  -O1 -fdefault-integer-8 -c "$src1" -o /tmp/pr84779-bisect-entry4.o \
  >"$compile1_log" 2>&1 || {
    if rg -qi 'internal compiler error|segmentation fault|abort' "$compile1_log"; then
      exit 1
    fi
    exit 125
  }

"$build_dir/gcc/gfortran" -B "$build_dir/gcc" \
  -O1 -fdefault-integer-8 -c "$src2" -o /tmp/pr84779-bisect-comment13.o \
  >"$compile2_log" 2>&1 || {
    if rg -qi 'internal compiler error|segmentation fault|abort' "$compile2_log"; then
      exit 1
    fi
    exit 125
  }

exit 0
