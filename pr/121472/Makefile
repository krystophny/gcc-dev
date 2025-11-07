# Makefile for PR121472 reproducer testing
# Tests with multiple Fortran compilers

# Compiler paths
GFORTRAN_SYSTEM := gfortran
GFORTRAN_DEV := ../../gcc-build/gcc/gfortran -B ../../gcc-build/gcc
IFX := ifx
NVFORTRAN := /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran

# Source files
REPRODUCER := reproducer.f90
TESTSUITE := ../../gcc/gcc/testsuite/gfortran.dg/finalize_constructor_1.f90

# Test programs
TESTS := test_simple.f90 test_component.f90 test_impure.f90

# Flags
FFLAGS := -Wa,--noexecstack -Wl,-z,noexecstack

.PHONY: all clean test-system test-dev test-ifx test-nvfortran test-all

all: test-all

# Test with system gfortran (should ICE)
test-system:
	@echo "=== Testing with system gfortran (expected: ICE) ==="
	-$(GFORTRAN_SYSTEM) $(FFLAGS) $(REPRODUCER) -o reproducer.system.x 2>&1 | head -20
	@echo

# Test with dev gfortran (should work)
test-dev:
	@echo "=== Testing with dev gfortran (expected: PASS) ==="
	$(GFORTRAN_DEV) $(FFLAGS) $(REPRODUCER) -o reproducer.dev.x && ./reproducer.dev.x
	@echo

# Test with Intel ifx
test-ifx:
	@echo "=== Testing with Intel ifx (expected: PASS, 2 finalizations) ==="
	@if command -v $(IFX) >/dev/null 2>&1; then \
		. /opt/intel/oneapi/setvars.sh --force >/dev/null 2>&1 && \
		$(IFX) $(FFLAGS) $(TESTSUITE) -o test.ifx.x && ./test.ifx.x; \
	else \
		echo "Intel ifx not found"; \
	fi
	@echo

# Test with NVIDIA nvfortran
test-nvfortran:
	@echo "=== Testing with NVIDIA nvfortran (expected: PASS, 2 finalizations) ==="
	@if [ -f "$(NVFORTRAN)" ]; then \
		$(NVFORTRAN) $(FFLAGS) $(TESTSUITE) -o test.nvfortran.x && ./test.nvfortran.x; \
	else \
		echo "NVIDIA nvfortran not found at $(NVFORTRAN)"; \
	fi
	@echo

# Run all tests
test-all: test-system test-dev test-ifx test-nvfortran

# Clean build artifacts
clean:
	rm -f *.x *.o *.mod *.smod
