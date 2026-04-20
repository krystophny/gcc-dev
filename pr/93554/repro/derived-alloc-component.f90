! PR fortran/93554
! Reproducer by gscfq@t-online.de, 2020-02-03 (Bugzilla comment #0).
! Compile with: gfortran -c -fopenacc derived-alloc-component.f90
!
! Pre-fix (before r16-8571-g010618b8dcb): ICE in expand_oacc_for at
! omp-expand.cc near "BRANCH_EDGE (entry_bb)->dest == exit_bb" assertion.
! Post-fix: compiles cleanly.

program p
   type t
      integer :: a
      integer, allocatable :: b(:)
   end type
   type(t) :: x
   integer :: i
   !$acc kernels
   !$acc loop private(x)
   do i = 0, 31
      x%a = 1
   end do
   !$acc end kernels
end
