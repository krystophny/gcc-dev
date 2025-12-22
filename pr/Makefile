GCC_BUILD_DIR = /home/ert/code/gcc-dev/gcc-build
GCC_SRC_DIR = /home/ert/code/gcc-dev/gcc

LIBGOMP_MOD_DIR = $(GCC_BUILD_DIR)/x86_64-pc-linux-gnu/libgomp

FC_SYSTEM = gfortran
FC_DEV = $(GCC_BUILD_DIR)/gcc/gfortran
FC_INTEL = ifx

FFLAGS_SYSTEM = -Wall -Wextra -std=f2018 -Wa,--noexecstack -Wl,-z,noexecstack
FFLAGS_DEV = -Wall -Wextra -std=f2018 -Wa,--noexecstack \
             -B$(GCC_BUILD_DIR)/gcc \
             -I$(LIBGOMP_MOD_DIR) \
             -L$(GCC_BUILD_DIR)/x86_64-pc-linux-gnu/libgfortran/.libs \
             -Wl,-rpath,$(GCC_BUILD_DIR)/x86_64-pc-linux-gnu/libgfortran/.libs \
             -Wl,-z,noexecstack
FFLAGS_INTEL = -warn all -stand f18

INTEL_SETVARS = /opt/intel/oneapi/setvars.sh

PR_DIRS = 102430 103276 107721 121472 121475 121628 123252 32365 90519 92613 96255

COARRAY_PRS =

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
	@if [ -f "$(INTEL_SETVARS)" ]; then \
		bash -c "source $(INTEL_SETVARS) > /dev/null 2>&1 && $(MAKE) test-compiler FC=\"$(FC_INTEL)\" FFLAGS=\"$(FFLAGS_INTEL)\" SUFFIX=\"intel\""; \
	else \
		echo "Intel oneAPI setvars not found at $(INTEL_SETVARS) - SKIP"; \
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
		reproducer=$$pr/reproducer.f90; \
		if [ ! -f "$$reproducer" ]; then \
			reproducer=$$(ls $$pr/*.f90 2>/dev/null | head -1); \
		fi; \
		if [ -z "$$reproducer" ]; then \
			echo "  [SKIP] No reproducer found"; \
			continue; \
		fi; \
		if grep -qiE '^[[:space:]]*![$$]omp' "$$reproducer" || grep -q 'dg-options.*-fopenmp' "$$reproducer"; then \
			openmp_flag="-fopenmp"; \
		else \
			openmp_flag=""; \
		fi; \
		if grep -qiE '^[[:space:]]*![$$]acc' "$$reproducer" || grep -q 'dg-options.*-fopenacc' "$$reproducer"; then \
			openacc_flag="-fopenacc"; \
		else \
			openacc_flag=""; \
		fi; \
		if echo " $(COARRAY_PRS) " | grep -q " $$pr "; then \
			coarray_flag="-fcoarray=single"; \
		else \
			coarray_flag=""; \
		fi; \
		log=/tmp/test_$${pr}_$(SUFFIX).log; \
		if $(FC) $(FFLAGS) $$coarray_flag $$openmp_flag $$openacc_flag -c $$reproducer -o /tmp/test_$${pr}_$(SUFFIX).o > $$log 2>&1; then \
			echo "  [PASS] Compilation successful"; \
		else \
			exit_code=$$?; \
			expected_regex=""; \
			case "$(SUFFIX):$$pr" in \
				system:102430) expected_regex="internal compiler error" ;; \
				dev:102430) expected_regex="Error: Sorry" ;; \
				system:32365) expected_regex='Unexpected !\$$OMP THREADPRIVATE statement' ;; \
				dev:32365) expected_regex="cannot appear after executable statements" ;; \
			esac; \
			if [ -n "$$expected_regex" ] && grep -qE "$$expected_regex" "$$log"; then \
				echo "  [XFAIL] Expected diagnostic"; \
			elif grep -q "internal compiler error" "$$log"; then \
				echo "  [ICE] Internal compiler error"; \
			elif grep -qi "Error: Sorry" "$$log" || grep -qi "^Sorry," "$$log"; then \
				echo "  [SORRY] Feature not supported"; \
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

$(PR_DIRS):
	@$(MAKE) test-pr PR=$@

test-pr:
	@echo "=========================================="
	@echo "Testing PR$(PR)"
	@echo "=========================================="
	@reproducer=$(PR)/reproducer.f90; \
	if [ ! -f "$$reproducer" ]; then \
		reproducer=$$(ls $(PR)/*.f90 2>/dev/null | head -1); \
	fi; \
	if [ -z "$$reproducer" ]; then \
		echo "[SKIP] No reproducer found"; \
		exit 0; \
	fi; \
	if grep -qiE '^[[:space:]]*![$$]omp' "$$reproducer" || grep -q 'dg-options.*-fopenmp' "$$reproducer"; then \
		openmp_flag="-fopenmp"; \
	else \
		openmp_flag=""; \
	fi; \
	if grep -qiE '^[[:space:]]*![$$]acc' "$$reproducer" || grep -q 'dg-options.*-fopenacc' "$$reproducer"; then \
		openacc_flag="-fopenacc"; \
	else \
		openacc_flag=""; \
	fi; \
	if echo " $(COARRAY_PRS) " | grep -q " $(PR) "; then \
		coarray_flag="-fcoarray=single"; \
	else \
		coarray_flag=""; \
	fi; \
	expected_system_regex=""; \
	expected_dev_regex=""; \
	case "$(PR)" in \
		102430) expected_system_regex="internal compiler error"; expected_dev_regex="Error: Sorry" ;; \
		32365) expected_system_regex='Unexpected !\$$OMP THREADPRIVATE statement'; expected_dev_regex="cannot appear after executable statements" ;; \
	esac; \
	echo ""; \
	echo "System gfortran:"; \
	if $(FC_SYSTEM) $(FFLAGS_SYSTEM) $$coarray_flag $$openmp_flag $$openacc_flag -c $$reproducer -o /tmp/pr$(PR)_system.o > /tmp/pr$(PR)_system.log 2>&1; then \
		echo "  [PASS]"; \
	else \
		if [ -n "$$expected_system_regex" ] && grep -qE "$$expected_system_regex" /tmp/pr$(PR)_system.log; then \
			echo "  [XFAIL]"; \
		elif grep -q "internal compiler error" /tmp/pr$(PR)_system.log; then \
			echo "  [ICE]"; \
		elif grep -qi "Error: Sorry" /tmp/pr$(PR)_system.log || grep -qi "^Sorry," /tmp/pr$(PR)_system.log; then \
			echo "  [SORRY]"; \
		else \
			echo "  [FAIL]"; \
		fi; \
	fi; \
	echo ""; \
	echo "Dev gfortran:"; \
	if $(FC_DEV) $(FFLAGS_DEV) $$coarray_flag $$openmp_flag $$openacc_flag -c $$reproducer -o /tmp/pr$(PR)_dev.o > /tmp/pr$(PR)_dev.log 2>&1; then \
		echo "  [PASS]"; \
	else \
		if [ -n "$$expected_dev_regex" ] && grep -qE "$$expected_dev_regex" /tmp/pr$(PR)_dev.log; then \
			echo "  [XFAIL]"; \
		elif grep -q "internal compiler error" /tmp/pr$(PR)_dev.log; then \
			echo "  [ICE]"; \
		elif grep -qi "Error: Sorry" /tmp/pr$(PR)_dev.log || grep -qi "^Sorry," /tmp/pr$(PR)_dev.log; then \
			echo "  [SORRY]"; \
		else \
			echo "  [FAIL]"; \
		fi; \
	fi; \
	echo ""; \
	echo "Intel ifx:"; \
	if which ifx > /dev/null 2>&1; then \
		if ifx $(FFLAGS_INTEL) $$coarray_flag $$openmp_flag $$openacc_flag -c $$reproducer -o /tmp/pr$(PR)_intel.o > /tmp/pr$(PR)_intel.log 2>&1; then \
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
        $(PR_DIRS) test-pr
