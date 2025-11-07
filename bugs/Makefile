GCC_BUILD_DIR = ../gcc-build
GCC_SRC_DIR = ../gcc

FC = $(GCC_BUILD_DIR)/gcc/gfortran
FFLAGS = -Wall -Wextra -std=f2018 -Wa,--noexecstack -B$(GCC_BUILD_DIR)/gcc \
         -L$(GCC_BUILD_DIR)/x86_64-pc-linux-gnu/libgfortran/.libs \
         -Wl,-rpath,$(GCC_BUILD_DIR)/x86_64-pc-linux-gnu/libgfortran/.libs \
         -Wl,-z,noexecstack

IFC = ifx
IFLAGS = -warn all -stand f18

INTEL_SETVARS = /opt/intel/oneapi/setvars.sh

BUG_DIRS = pr121628 90519
SOURCES = $(foreach dir,$(BUG_DIRS),$(wildcard $(dir)/*.f90))
TARGETS = $(SOURCES:.f90=.x)
INTEL_TARGETS = $(SOURCES:.f90=.intel.x)

.PHONY: all clean intel run run-intel rebuild-gcc $(BUG_DIRS)

all: $(TARGETS)

$(BUG_DIRS):
	@targets="$(wildcard $@/*.f90)"; \
	if [ -n "$$targets" ]; then \
	  $(MAKE) $(patsubst %.f90,%.x,$(wildcard $@/*.f90)); \
	fi

intel: $(INTEL_TARGETS)

run: $(TARGETS)
	@for exe in $(TARGETS); do \
		echo "Running $$exe..."; \
		./$$exe || echo "$$exe failed with exit code $$?"; \
		echo ""; \
	done

run-intel: $(INTEL_TARGETS)
	@bash -c "source $(INTEL_SETVARS) > /dev/null 2>&1 && \
	for exe in $(INTEL_TARGETS); do \
		echo \"Running \$$exe...\"; \
		./\$$exe || echo \"\$$exe failed with exit code \$$?\"; \
		echo \"\"; \
	done"

rebuild-gcc:
	@echo "Rebuilding gfortran in $(GCC_BUILD_DIR)..."
	$(MAKE) -C $(GCC_BUILD_DIR) -j$$(nproc)
	@echo "gfortran rebuild complete"

%.x: %.f90
	$(FC) $(FFLAGS) $< -o $@

%.intel.x: %.f90
	bash -c "source $(INTEL_SETVARS) && $(IFC) $(IFLAGS) $< -o $@"

clean:
	rm -f $(TARGETS) $(INTEL_TARGETS)
	find . -name '*.mod' -delete
