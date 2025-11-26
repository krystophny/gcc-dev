FC_CUSTOM = ../../gcc-build/gcc/gfortran -B ../../gcc-build/gcc
FC_SYSTEM = /usr/bin/gfortran
FC_FLANG  = /usr/bin/flang-new
FC_IFX    = /opt/intel/oneapi/compiler/2025.2/bin/ifx
FC_NVHPC  = /opt/nvidia/hpc_sdk/Linux_x86_64/25.9/compilers/bin/nvfortran
FC_LFORT  = lfortran

FFLAGS = -Wa,--noexecstack -Wl,-z,noexecstack

all: test-custom test-system test-flang test-ifx test-nvhpc test-lfortran

test-custom:
	$(FC_CUSTOM) $(FFLAGS) reproducer.f90 -o reproducer.custom.x

test-system:
	$(FC_SYSTEM) $(FFLAGS) reproducer.f90 -o reproducer.system.x

test-flang:
	$(FC_FLANG) reproducer.f90 -o reproducer.flang.x

test-ifx:
	bash -c "source /opt/intel/oneapi/setvars.sh && $(FC_IFX) reproducer.f90 -o reproducer.ifx.x"

test-nvhpc:
	$(FC_NVHPC) reproducer.f90 -o reproducer.nvfortran.x

test-lfortran:
	@if command -v $(FC_LFORT) >/dev/null 2>&1; then \
		$(FC_LFORT) reproducer.f90 -o reproducer.lfortran.x; \
	else \
		echo "LFortran not found, skipping"; \
	fi

run: all
	@echo "=== Custom gfortran (with fix) ==="
	-./reproducer.custom.x && echo "PASS" || echo "FAIL (exit $$?)"
	@echo ""
	@echo "=== System gfortran (15.2.1, unfixed) ==="
	-./reproducer.system.x && echo "PASS" || echo "FAIL (exit $$?)"
	@echo ""
	@echo "=== Flang ==="
	-./reproducer.flang.x && echo "PASS" || echo "FAIL (exit $$?)"
	@echo ""
	@echo "=== Intel ifx ==="
	-./reproducer.ifx.x && echo "PASS" || echo "FAIL (exit $$?)"
	@echo ""
	@echo "=== NVIDIA nvfortran ==="
	-./reproducer.nvfortran.x && echo "PASS" || echo "FAIL (exit $$?)"
	@echo ""
	@if command -v $(FC_LFORT) >/dev/null 2>&1; then \
		echo "=== LFortran ==="; \
		./reproducer.lfortran.x && echo "PASS" || echo "FAIL (exit $$?)"; \
	fi

clean:
	rm -f *.x *.o *.mod *.smod
