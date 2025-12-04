FC_CUSTOM = ../../gcc-build/gcc/gfortran -B ../../gcc-build/gcc
FC_SYSTEM = /usr/bin/gfortran
FC_FLANG  = /usr/bin/flang-new
FC_IFX    = /opt/intel/oneapi/compiler/2025.2/bin/ifx
FC_NVHPC  = /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran
FC_LFORT  = lfortran

FFLAGS = -Wa,--noexecstack -Wl,-z,noexecstack

.PHONY: all test-custom test-system test-flang test-ifx test-nvhpc test-lfortran clean

all: test-custom

# Reproduce the bug: preprocess then compile with -cpp -fpreprocessed
test-custom:
	$(FC_CUSTOM) -cpp reproducer.f90 -E -o reproducer.pp.f90
	$(FC_CUSTOM) -cpp -fpreprocessed reproducer.pp.f90 $(FFLAGS) -o reproducer-custom.x

test-system:
	$(FC_SYSTEM) -cpp reproducer.f90 -E -o reproducer.pp.f90
	$(FC_SYSTEM) -cpp -fpreprocessed reproducer.pp.f90 $(FFLAGS) -o reproducer-system.x

test-flang:
	$(FC_FLANG) -cpp reproducer.f90 -E -o reproducer.pp.f90
	$(FC_FLANG) -cpp -fpreprocessed reproducer.pp.f90 -o reproducer-flang.x || echo "Flang may not support -fpreprocessed"

test-ifx:
	bash -c "source /opt/intel/oneapi/setvars.sh && \
		$(FC_IFX) -cpp reproducer.f90 -E -o reproducer.pp.f90 && \
		$(FC_IFX) -cpp -fpreprocessed reproducer.pp.f90 -o reproducer-ifx.x" || echo "ifx may not support -fpreprocessed"

test-nvhpc:
	$(FC_NVHPC) -cpp reproducer.f90 -E -o reproducer.pp.f90
	$(FC_NVHPC) -cpp -fpreprocessed reproducer.pp.f90 -o reproducer-nvhpc.x || echo "nvfortran may not support -fpreprocessed"

test-lfortran:
	@if command -v $(FC_LFORT) >/dev/null 2>&1; then \
		$(FC_LFORT) -cpp reproducer.f90 -E -o reproducer.pp.f90 && \
		$(FC_LFORT) -cpp -fpreprocessed reproducer.pp.f90 -o reproducer-lfortran.x; \
	else \
		echo "LFortran not found"; \
	fi

clean:
	rm -f *.x *.o *.mod *.smod *.pp.f90
