FC_CUSTOM = ../../gcc-build/gcc/gfortran -B ../../gcc-build/gcc
FC_SYSTEM = /usr/bin/gfortran
FC_FLANG  = /usr/bin/flang-new
FC_IFX    = /opt/intel/oneapi/compiler/2025.2/bin/ifx
FC_NVHPC  = /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran
FC_LFORT  = lfortran

FFLAGS = -Wa,--noexecstack -Wl,-z,noexecstack

all: test-simple test-common test-omp

test-simple: test-simple-custom test-simple-system test-simple-ifx test-simple-nvhpc

test-common: test-common-custom test-common-system test-common-ifx test-common-nvhpc

test-omp: test-omp-custom test-omp-system test-omp-ifx test-omp-nvhpc

# Simple specification statement tests
test-simple-custom:
	@echo "=== Testing simple_spec.f90 with custom gfortran ==="
	@if [ -f ../../gcc-build/gcc/gfortran ]; then \
		$(FC_CUSTOM) -c simple_spec.f90 2>&1 || true; \
	else \
		echo "Custom gfortran not built yet"; \
	fi

test-simple-system:
	@echo "=== Testing simple_spec.f90 with system gfortran ==="
	$(FC_SYSTEM) -c simple_spec.f90 2>&1 || true

test-simple-ifx:
	@echo "=== Testing simple_spec.f90 with Intel ifx ==="
	@bash -c "source /opt/intel/oneapi/setvars.sh >/dev/null 2>&1 && $(FC_IFX) -c simple_spec.f90 2>&1" || true

test-simple-nvhpc:
	@echo "=== Testing simple_spec.f90 with NVIDIA nvfortran ==="
	$(FC_NVHPC) -c simple_spec.f90 2>&1 || true

# Common statement tests
test-common-custom:
	@echo "=== Testing common_test.f90 with custom gfortran ==="
	@if [ -f ../../gcc-build/gcc/gfortran ]; then \
		$(FC_CUSTOM) -c common_test.f90 2>&1 || true; \
	else \
		echo "Custom gfortran not built yet"; \
	fi

test-common-system:
	@echo "=== Testing common_test.f90 with system gfortran ==="
	$(FC_SYSTEM) -c common_test.f90 2>&1 || true

test-common-ifx:
	@echo "=== Testing common_test.f90 with Intel ifx ==="
	@bash -c "source /opt/intel/oneapi/setvars.sh >/dev/null 2>&1 && $(FC_IFX) -c common_test.f90 2>&1" || true

test-common-nvhpc:
	@echo "=== Testing common_test.f90 with NVIDIA nvfortran ==="
	$(FC_NVHPC) -c common_test.f90 2>&1 || true

# OpenMP threadprivate tests
test-omp-custom:
	@echo "=== Testing reproducer.f90 with custom gfortran ==="
	@if [ -f ../../gcc-build/gcc/gfortran ]; then \
		$(FC_CUSTOM) -fopenmp -c reproducer.f90 2>&1 || true; \
	else \
		echo "Custom gfortran not built yet"; \
	fi

test-omp-system:
	@echo "=== Testing reproducer.f90 with system gfortran ==="
	$(FC_SYSTEM) -fopenmp -c reproducer.f90 2>&1 || true

test-omp-ifx:
	@echo "=== Testing reproducer.f90 with Intel ifx ==="
	@bash -c "source /opt/intel/oneapi/setvars.sh >/dev/null 2>&1 && $(FC_IFX) -fopenmp -c reproducer.f90 2>&1" || true

test-omp-nvhpc:
	@echo "=== Testing reproducer.f90 with NVIDIA nvfortran ==="
	$(FC_NVHPC) -Minfo=mp -c reproducer.f90 2>&1 || true

clean:
	rm -f *.x *.o *.mod *.smod

.PHONY: all test-simple test-common test-omp clean test-simple-custom test-simple-system test-simple-ifx test-simple-nvhpc test-common-custom test-common-system test-common-ifx test-common-nvhpc test-omp-custom test-omp-system test-omp-ifx test-omp-nvhpc