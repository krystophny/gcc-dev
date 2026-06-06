! Reproducer for GCC 17 trunk regression:
! c_loc on an array element is rejected as "C_FUNLOC shall be a procedure"
! when compiled with -fopenacc -foffload=nvptx-none against a module
! that uses ISO_C_BINDING and HDF5.
!
! The bug manifests inside a module that does:
!   use hdf5_tools    ! HDF5 Fortran module (brings in HID_T etc.)
!   use ISO_C_BINDING
! and then calls c_loc on an array element.
!
! The issue is that GCC 17 emits a spurious C_FUNLOC error message
! (instead of C_LOC) for a valid c_loc(array(i)) call.
!
! Compile command that fails:
!   gfortran -fopenacc -foffload=nvptx-none -std=f2008 -fcheck=bounds \
!            -fpreprocessed -c hdf5_tools_f2003.f90-pp.f90
!
! Simplified stand-alone reproducer (requires hdf5_tools module to trigger):
!
! From libneo/src/hdf5_tools/hdf5_tools_f2003.f90, subroutine h5_get_int8_1:
!
!   integer(kind=8), dimension(:), pointer   :: test
!   type(C_PTR)                              :: f_ptr
!   test => value
!   f_ptr = c_loc(test(1))    ! Error: to C_FUNLOC shall be a procedure
!
! Also triggered by c_loc(value(1)) where value is dimension(:),target.
!
! Workaround (not yet found; fixing target/pointer distinction did not help).
!
! Accepted:  GCC 16.1.1 20260430 (distro)
! Rejected:  GCC 17.0.0 20260604 (experimental, trunk cc58cf0d2f9b)

module c_loc_offload_reproducer
  use iso_c_binding
  implicit none
contains

  subroutine repro_1d(value)
    integer(kind=8), dimension(:), target, intent(inout) :: value
    integer(kind=8), dimension(:), pointer :: ptr
    type(c_ptr) :: cptr
    ptr => value
    cptr = c_loc(ptr(1))   ! triggers regression with hdf5 module in scope
  end subroutine

  subroutine repro_2d(value)
    integer(kind=8), dimension(:,:), target, intent(inout) :: value
    integer(kind=8), dimension(:,:), pointer :: ptr
    type(c_ptr) :: cptr
    ptr => value
    cptr = c_loc(ptr(1,1))
  end subroutine

end module c_loc_offload_reproducer
