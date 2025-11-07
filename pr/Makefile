GCC_BUILD_DIR = /home/ert/code/gcc-dev/gcc-build
GCC_SRC_DIR = /home/ert/code/gcc-dev/gcc

FC_SYSTEM = gfortran
FC_DEV = $(GCC_BUILD_DIR)/gcc/gfortran
FC_INTEL = ifx

FFLAGS_SYSTEM = -Wall -Wextra -std=f2018 -Wa,--noexecstack -Wl,-z,noexecstack
FFLAGS_DEV = -Wall -Wextra -std=f2018 -Wa,--noexecstack \
             -B$(GCC_BUILD_DIR)/gcc \
             -L$(GCC_BUILD_DIR)/x86_64-pc-linux-gnu/libgfortran/.libs \
             -Wl,-rpath,$(GCC_BUILD_DIR)/x86_64-pc-linux-gnu/libgfortran/.libs \
             -Wl,-z,noexecstack
FFLAGS_INTEL = -warn all -stand f18

INTEL_SETVARS = /opt/intel/oneapi/setvars.sh

PR_DIRS = 90519 121628 113885 114535 110987 82622 116669 85002 104684 103716 103368 121472 122191

COARRAY_PRS = 85002 104684

all: test-dev

help:
	@echo "GCC Fortran Bug Reproducer Test Suite"
	@echo ""
	@echo "Available targets:"
	@echo "  make all           - Same as test-dev"
	@echo "  make test-system   - Test all reproducers with system gfortran"
	@echo "  make test-dev      - Test all reproducers with dev gfortran"
	@echo "  make test-ifx      - Test all reproducers with Intel ifx"
	@echo "  make test-all      - Test with all three compilers"
	@echo "  make clean         - Clean all built files"
	@echo "  make <PR-number>   - Test specific PR (e.g., make 90519)"
	@echo "  make summary       - Print test results summary"
	@echo ""
	@echo "PR directories: $(PR_DIRS)"
	@echo ""
	@echo "Note: PRs $(COARRAY_PRS) require -fcoarray=single"

test-system:
	@echo "=========================================="
	@echo "Testing with System gfortran"
	@echo "=========================================="
	@$(MAKE) test-compiler FC="$(FC_SYSTEM)" FFLAGS="$(FFLAGS_SYSTEM)" SUFFIX="system"

test-dev:
	@echo "=========================================="
	@echo "Testing with Dev gfortran"
	@echo "=========================================="
	@$(MAKE) test-compiler FC="$(FC_DEV)" FFLAGS="$(FFLAGS_DEV)" SUFFIX="dev"

test-ifx:
	@echo "=========================================="
	@echo "Testing with Intel ifx"
	@echo "=========================================="
	@if which ifx > /dev/null 2>&1; then \
		$(MAKE) test-compiler FC="$(FC_INTEL)" FFLAGS="$(FFLAGS_INTEL)" SUFFIX="intel"; \
	else \
		echo "Intel ifx not found - SKIP"; \
	fi

test-all:
	@$(MAKE) test-system
	@echo ""
	@$(MAKE) test-dev
	@echo ""
	@$(MAKE) test-ifx

test-compiler:
	@for pr in $(PR_DIRS); do \
		echo ""; \
		echo "Testing PR$$pr..."; \
		reproducer=$$(ls $$pr/*.f90 2>/dev/null | head -1); \
		if [ -z "$$reproducer" ]; then \
			echo "  [SKIP] No reproducer found"; \
			continue; \
		fi; \
		if echo " $(COARRAY_PRS) " | grep -q " $$pr "; then \
			coarray_flag="-fcoarray=single"; \
		else \
			coarray_flag=""; \
		fi; \
		if $(FC) $(FFLAGS) $$coarray_flag -c $$reproducer -o /tmp/test_$$pr_$(SUFFIX).o > /tmp/test_$$pr_$(SUFFIX).log 2>&1; then \
			echo "  [PASS] Compilation successful"; \
		else \
			exit_code=$$?; \
			if grep -q "internal compiler error" /tmp/test_$$pr_$(SUFFIX).log; then \
				echo "  [ICE] Internal compiler error"; \
			else \
				echo "  [FAIL] Compilation failed (exit code: $$exit_code)"; \
			fi; \
		fi; \
	done

summary:
	@echo "=========================================="
	@echo "Bug Reproducer Summary"
	@echo "=========================================="
	@echo ""
	@echo "Total PRs: $(words $(PR_DIRS))"
	@echo ""
	@for pr in $(PR_DIRS); do \
		reproducer=$$(ls $$pr/*.f90 2>/dev/null | head -1); \
		readme=$$(ls $$pr/README.md 2>/dev/null); \
		if [ -n "$$reproducer" ]; then \
			status=$$(grep -m1 "^**Status:**" $$pr/README.md 2>/dev/null | cut -d' ' -f2- || echo "UNKNOWN"); \
			title=$$(grep -m1 "^**Title:**" $$pr/README.md 2>/dev/null | cut -d' ' -f2- || echo "No title"); \
			echo "PR$$pr: $$status"; \
			echo "  $$title"; \
			echo ""; \
		fi; \
	done

90519:
	@$(MAKE) test-pr PR=90519

121628:
	@$(MAKE) test-pr PR=121628

113885:
	@$(MAKE) test-pr PR=113885

114535:
	@$(MAKE) test-pr PR=114535

110987:
	@$(MAKE) test-pr PR=110987

82622:
	@$(MAKE) test-pr PR=82622

116669:
	@$(MAKE) test-pr PR=116669

85002:
	@$(MAKE) test-pr PR=85002 COARRAY="-fcoarray=single"

104684:
	@$(MAKE) test-pr PR=104684 COARRAY="-fcoarray=single"

103716:
	@$(MAKE) test-pr PR=103716

103368:
	@$(MAKE) test-pr PR=103368

121472:
	@$(MAKE) test-pr PR=121472

122191:
	@$(MAKE) test-pr PR=122191

test-pr:
	@echo "=========================================="
	@echo "Testing PR$(PR)"
	@echo "=========================================="
	@reproducer=$$(ls $(PR)/*.f90 2>/dev/null | head -1); \
	if [ -z "$$reproducer" ]; then \
		echo "[SKIP] No reproducer found"; \
		exit 0; \
	fi; \
	echo ""; \
	echo "System gfortran:"; \
	if $(FC_SYSTEM) $(FFLAGS_SYSTEM) $(COARRAY) -c $$reproducer -o /tmp/pr$(PR)_system.o > /tmp/pr$(PR)_system.log 2>&1; then \
		echo "  [PASS]"; \
	else \
		if grep -q "internal compiler error" /tmp/pr$(PR)_system.log; then \
			echo "  [ICE]"; \
		else \
			echo "  [FAIL]"; \
		fi; \
	fi; \
	echo ""; \
	echo "Dev gfortran:"; \
	if $(FC_DEV) $(FFLAGS_DEV) $(COARRAY) -c $$reproducer -o /tmp/pr$(PR)_dev.o > /tmp/pr$(PR)_dev.log 2>&1; then \
		echo "  [PASS]"; \
	else \
		if grep -q "internal compiler error" /tmp/pr$(PR)_dev.log; then \
			echo "  [ICE]"; \
		else \
			echo "  [FAIL]"; \
		fi; \
	fi; \
	echo ""; \
	echo "Intel ifx:"; \
	if which ifx > /dev/null 2>&1; then \
		if ifx $(FFLAGS_INTEL) $(COARRAY) -c $$reproducer -o /tmp/pr$(PR)_intel.o > /tmp/pr$(PR)_intel.log 2>&1; then \
			echo "  [PASS]"; \
		else \
			echo "  [FAIL]"; \
		fi; \
	else \
		echo "  [SKIP] Not installed"; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	@rm -f /tmp/test_*.o /tmp/test_*.x /tmp/test_*.log
	@rm -f /tmp/pr*_system.o /tmp/pr*_dev.o /tmp/pr*_intel.o
	@rm -f /tmp/pr*_system.log /tmp/pr*_dev.log /tmp/pr*_intel.log
	@find . -name '*.mod' -delete
	@echo "Clean complete"

.PHONY: all help test-system test-dev test-ifx test-all test-compiler summary clean \
        90519 121628 113885 114535 110987 82622 116669 85002 104684 103716 103368 121472 122191 test-pr
