# nvfortran 25.11 LLVM IR Bug - Minimal Reproducible Example

## Bug Description

nvfortran 25.11 generates invalid LLVM IR when compiling Fortran code with:
- OpenACC enabled (`-acc -gpu=cc89`)
- External precompiled `.mod` files
- Include statements for type definitions
- Two namelists sharing the same module variables

The generated LLVM IR contains `bitcast(i32 .V1_1352 to i8*)` where `.V1_1352`
is missing the `@` prefix required for global variable references.

## Error Message

```
/opt/nvidia/hpc_sdk/Linux_x86_64/25.11/compilers/share/llvm/bin/opt:
  /tmp/nvfortranXXX.ll:10:467: error: expected value token
@_scheduler_module_5_ = dso_local global %struct_scheduler_module_5_ < { ...
  ptr getelementptr(i8, i8* bitcast(i32 .V1_1352 to i8*), i32 0), ...
                                        ^
```

## Reproducing the Bug

### Prerequisites

1. NVIDIA HPC SDK 25.11 with nvfortran
2. CUDA toolkit at `/opt/cuda` (or set `NVHPC_CUDA_HOME`)
3. Precompiled `.mod` files from libneo built with OpenACC

### Steps

1. Copy `.mod` files from a libneo OpenACC build:
   ```bash
   cp /path/to/libneo/build-nvfortran-acc/*.mod .
   cp /opt/nvidia/hpc_sdk/Linux_x86_64/25.11/comm_libs/13.0/hpcx/hpcx-2.25.1/ompi/lib/*.mod .
   ```

2. Compile the test file:
   ```bash
   NVHPC_CUDA_HOME=/opt/cuda nvfortran -acc -gpu=cc89 -fast -O3 -c test_header_only.f90
   ```

3. Observe the LLVM IR error.

## Key Files

- `test_header_only.f90` - Main test file that triggers the bug
- `scheduler_header.f90` - Include file with type definitions and namelists
- `*_header.f90` - Supporting include files for listener/dispatcher types

## Trigger Conditions

The bug requires ALL of the following:
1. nvfortran 25.11 (tested - bug occurs with or without OpenACC flags)
2. External precompiled `.mod` files from nvfortran (inline module definitions don't trigger it)
3. Include statement structure (not inline code)
4. Two namelists sharing the same variables:
   ```fortran
   namelist / nmlGenericScheduler / loadBalancing, buffersize, verbose, activateMPE
   namelist / parallel / loadBalancing, buffersize, verbose, activateMPE
   ```

Note: The bug is NOT specific to OpenACC - it occurs in the LLVM IR generation
for regular CPU compilation as well. It was discovered during OpenACC builds
because that's when the scheduler_module was first compiled with nvfortran.

## Workaround

None known. The bug prevents building libneo's MyMPILib with nvfortran 25.11.

## Environment

- nvfortran 25.11
- CUDA 13.x
- Linux x86_64
