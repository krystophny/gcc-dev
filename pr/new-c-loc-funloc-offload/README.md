# GCC 17 trunk: c_loc on array element rejected as C_FUNLOC with -foffload=nvptx-none

**Status:** not yet filed on Bugzilla
**Compiler:** GCC 17.0.0 20260604 (experimental), trunk cc58cf0d2f9b  
**Regression from:** GCC 16.1.1 20260430 (accepts the same code)

## Symptom

Fortran `c_loc(array(i))` is rejected with:

```
Error: Argument X at (1) to C_FUNLOC shall be a procedure or a procedure pointer
```

The error names `C_FUNLOC` but the source calls `c_loc`. The call is
valid F2008: `array` is either `dimension(:), pointer` or
`dimension(:), target` and `array(i)` is a data object, not a
procedure.

## Trigger conditions

All three must be present:

1. `-fopenacc -foffload=nvptx-none`
2. The module uses `use hdf5_tools` (HDF5 Fortran module, system libhdf5)
3. The module also uses `ISO_C_BINDING` and calls `c_loc(arr(i))`

Without the HDF5 module in scope the reproducer compiles clean under
GCC 17 with the same flags. The bug is likely in name or interface
resolution during the offload lowering pass when HDF5 symbols are
visible.

## Reproducer

`reproducer.f90`: stand-alone module. Does not reproduce without HDF5 in scope.

The actual failing file is
`libneo/src/hdf5_tools/hdf5_tools_f2003.f90` (itpplasma/libneo on
GitHub). Four call sites, all the same pattern:

```fortran
integer(kind=8), dimension(:), pointer :: ptr
ptr => value
f_ptr = c_loc(ptr(1))   ! Error here
```

And equivalently with `dimension(:,:)` subscripted `ptr(1,1)`.

## Compile command

```bash
gfortran \
  -I<hdf5-include> \
  -fopenacc -foffload=nvptx-none \
  -std=f2008 -fcheck=bounds -fpreprocessed \
  -c hdf5_tools_f2003.f90-pp.f90
```

The `-fpreprocessed` flag is set by CMake's two-pass build (preprocess
then compile); the error appears in the compile pass.

## Next steps

- Narrow whether the issue is in `resolve.cc` generic resolution or
  in the offload lowering (`omp-offload.cc` / `trans-openmp.cc`).
- Check if `c_loc` is being confused with `c_funloc` during interface
  matching when the HDF5 module exports overloaded interfaces.
- File on Bugzilla under Fortran / OpenACC; update directory name to
  `pr/<number>` once filed.
