#!/bin/bash
# Bisect test for PR95879: ICE in gfc_resolve_formal_arglist
# Returns 0 (good) if compilation succeeds, 1 (bad) if ICE/segfault
# Returns 125 (skip) if build fails

set -e

SRCDIR="$(cd "$(dirname "$0")"/../../.. && pwd)"
BUILDDIR="$SRCDIR/gcc-bisect-build"

# Build fortran compiler
cd "$BUILDDIR"
make -j32 > /tmp/bisect-build.log 2>&1 || exit 125

# Test z1.f90
"$BUILDDIR/gcc/gfortran" -B "$BUILDDIR/gcc" -c "$SRCDIR/pr/95879/z1.f90" -o /dev/null 2>/tmp/bisect-test.log
rc1=$?

# Test z2.f90
"$BUILDDIR/gcc/gfortran" -B "$BUILDDIR/gcc" -c "$SRCDIR/pr/95879/z2.f90" -o /dev/null 2>>/tmp/bisect-test.log
rc2=$?

if [ $rc1 -ne 0 ] || [ $rc2 -ne 0 ]; then
    echo "BAD: compilation failed (rc1=$rc1, rc2=$rc2)"
    cat /tmp/bisect-test.log
    exit 1
fi

echo "GOOD: both files compile cleanly"
exit 0
