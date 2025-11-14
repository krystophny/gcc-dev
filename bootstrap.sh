#!/bin/sh
cd gcc-build
../gcc/configure \
  --enable-languages=fortran \
  --disable-multilib \
  --disable-bootstrap \
  CFLAGS='-Og -g' CXXFLAGS='-Og -g'
