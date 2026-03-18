#!/bin/sh
# Build GCC on cfarm428.cfarm.net (NetBSD 10.1, aarch64)
# Usage: ssh cfarm428.cfarm.net 'bash -s' < pr/124512/cfarm428-build.sh
#
# Prerequisites: git clone --depth 1 git://gcc.gnu.org/git/gcc.git ~/gcc-dev/gcc
#
# Known issues on this platform:
#   1. config.host missing NetBSD for aarch64 host_detect_local_cpu
#   2. libisl.so.23 in /usr/pkg/lib not in default search path
#   3. PR124512: pthread_condattr_setpshared missing (the bug we're reproducing)

set -e

GCC_DEV="$HOME/gcc-dev"
GCC_SRC="$GCC_DEV/gcc"
GCC_BUILD="$GCC_DEV/gcc-build"

# Workaround 1: patch config.host to add NetBSD to aarch64 host detection
if ! grep -q 'aarch64.*netbsd' "$GCC_SRC/gcc/config.host"; then
    echo "Patching config.host: adding aarch64-netbsd to host_detect_local_cpu..."
    cp "$GCC_SRC/gcc/config.host" "$GCC_SRC/gcc/config.host.bak"
    awk 'NR==103{gsub(/darwin\*\)/, "darwin* | aarch64*-*-netbsd*)")} {print}' \
        "$GCC_SRC/gcc/config.host.bak" > "$GCC_SRC/gcc/config.host"
fi

# Workaround 2: libisl in /usr/pkg/lib
export LD_LIBRARY_PATH=/usr/pkg/lib

mkdir -p "$GCC_BUILD"
cd "$GCC_BUILD"

# Configure (fortran-only, debug, no bootstrap)
if [ ! -f Makefile ] || [ ! -f config.status ]; then
    ../gcc/configure \
        --enable-languages=fortran \
        --disable-multilib \
        --disable-bootstrap \
        --with-gmp=/usr/pkg \
        --with-mpfr=/usr/pkg \
        --with-mpc=/usr/pkg \
        CFLAGS="-Og -g" \
        CXXFLAGS="-Og -g"
fi

# Build (use gmake on NetBSD)
gmake -j16
