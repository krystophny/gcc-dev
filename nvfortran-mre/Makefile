# nvfortran 25.11 LLVM IR bug MRE
#
# Usage: make all
# (Requires libneo built with nvfortran at /home/ert/code/libneo/build-nvfortran)

FC = nvfortran

# Default paths - adjust as needed
LIBNEO_BUILD = /home/ert/code/libneo/build-nvfortran
MPI_MOD_PATH = /opt/nvidia/hpc_sdk/Linux_x86_64/25.11/comm_libs/13.0/hpcx/hpcx-2.25.1/ompi/lib

all: setup bug

setup:
	cp $(LIBNEO_BUILD)/*.mod .
	cp $(MPI_MOD_PATH)/mpi.mod .

bug:
	$(FC) -c test_header_only.f90

clean:
	rm -f *.mod *.o
