# Makefile for PR96255 - DO CONCURRENT with optional type specification
# Tests with multiple Fortran compilers

# Compiler paths
GFORTRAN_SYSTEM := gfortran
GFORTRAN_DEV := ../../gcc-build/gcc/gfortran -B ../../gcc-build/gcc
FLANG := /usr/bin/flang-new
IFX := /opt/intel/oneapi/compiler/2025.2/bin/ifx
NVFORTRAN := /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran
LFORTRAN := lfortran

# Source files
REPRODUCER := looper.f90

# Flags
FFLAGS := -Wa,--noexecstack -Wl,-z,noexecstack

.PHONY: all clean test-system test-dev test-flang test-ifx test-nvfortran test-lfortran test-all

all: test-all

# Test with system gfortran (expected: syntax error before patch)
test-system:
	@echo "=== Testing with system gfortran ==="
	-$(GFORTRAN_SYSTEM) $(FFLAGS) $(REPRODUCER) -o looper.system.x && ./looper.system.x
	@echo

# Test with dev gfortran (expected: work after patch)
test-dev:
	@echo "=== Testing with dev gfortran ==="
	$(GFORTRAN_DEV) $(FFLAGS) $(REPRODUCER) -o looper.dev.x && ./looper.dev.x
	@echo

# Test with LLVM flang
test-flang:
	@echo "=== Testing with LLVM flang ==="
	@if [ -f "$(FLANG)" ]; then \
		$(FLANG) $(REPRODUCER) -o looper.flang.x && ./looper.flang.x; \
	else \
		echo "LLVM flang not found at $(FLANG)"; \
	fi
	@echo

# Test with Intel ifx
test-ifx:
	@echo "=== Testing with Intel ifx ==="
	@if [ -f "$(IFX)" ]; then \
		bash -c "source /opt/intel/oneapi/setvars.sh --force >/dev/null 2>&1 && $(IFX) $(REPRODUCER) -o looper.ifx.x && ./looper.ifx.x"; \
	else \
		echo "Intel ifx not found at $(IFX)"; \
	fi
	@echo

# Test with NVIDIA nvfortran
test-nvfortran:
	@echo "=== Testing with NVIDIA nvfortran ==="
	@if [ -f "$(NVFORTRAN)" ]; then \
		$(NVFORTRAN) $(REPRODUCER) -o looper.nvfortran.x && ./looper.nvfortran.x; \
	else \
		echo "NVIDIA nvfortran not found at $(NVFORTRAN)"; \
	fi
	@echo

# Test with LFortran
test-lfortran:
	@echo "=== Testing with LFortran ==="
	@if command -v $(LFORTRAN) >/dev/null 2>&1; then \
		$(LFORTRAN) $(REPRODUCER) -o looper.lfortran.x && ./looper.lfortran.x; \
	else \
		echo "LFortran not found"; \
	fi
	@echo

# Run all tests
test-all: test-system test-dev test-flang test-ifx test-nvfortran test-lfortran

# Clean build artifacts
clean:
	rm -f *.x *.o *.mod *.smod
