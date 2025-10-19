#!/bin/sh
cd gcc-build
../gcc/configure \
  --enable-languages=fortran \
  --disable-multilib \
  --disable-bootstrap \
  --enable-checking=yes \
  CFLAGS='-O0 -g' CXXFLAGS='-O0 -g'
