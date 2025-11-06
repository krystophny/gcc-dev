# Finalizer ICE Reproducer

Minimal program that triggers an internal compiler error when compiling a type
with allocatable recursive components and a FINAL procedure.

Compile with the in-tree compiler:

```
./gcc-build/gcc/gfortran -B ./gcc-build/gcc \
  -L ./gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
  -Wl,-rpath,$(pwd)/gcc-build/x86_64-pc-linux-gnu/libgfortran/.libs \
  -o finalizer_min.x finalizer_min.f90
```

Both trunk and GCC 15.2.1 ICE before runtime.
