# nvfortran 25.11 LLVM IR bug MRE
#
# Prerequisites: .mod files from a nvfortran libneo build
#   cp /path/to/libneo/build-nvfortran/*.mod .
#   cp /opt/nvidia/hpc_sdk/.../ompi/lib/mpi.mod .
#
# Then: make

FC = nvfortran

bug:
	$(FC) -c test_header_only.f90

clean:
	rm -f *.mod *.o
