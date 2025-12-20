FC_GCC = /home/ert/code/gcc-dev/gcc-build/gcc/gfortran -B /home/ert/code/gcc-dev/gcc-build/gcc
FC_SYS = /usr/bin/gfortran
FC_IFX = ifx
FC_NV = /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran

.PHONY: all clean test-gcc test-sys test-ifx test-nv

all: test-gcc

test-gcc: reproducer.f90
	$(FC_GCC) -g $< -o $@
	@echo "=== gfortran (patched) ==="
	./$@ || true

test-sys: reproducer.f90
	$(FC_SYS) -g $< -o $@
	@echo "=== gfortran (system) ==="
	./$@ || true

test-ifx: reproducer.f90
	source /opt/intel/oneapi/setvars.sh && $(FC_IFX) -g $< -o $@
	@echo "=== Intel ifx ==="
	./$@ || true

test-nv: reproducer.f90
	$(FC_NV) -g $< -o $@
	@echo "=== NVIDIA nvfortran ==="
	./$@ || true

clean:
	rm -f test-gcc test-sys test-ifx test-nv *.o *.mod
