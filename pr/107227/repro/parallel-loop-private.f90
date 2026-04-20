! PR libgomp/107227
! Reproducer by shb@gatech.edu, 2022-10-12 (Bugzilla comment #0).
! Compile with: gfortran -fopenacc -c parallel-loop-private.f90
!
! Pre-fix: ICE in expand_oacc_for (same site as PR93554).
! Post-fix: compiles cleanly.

program main
integer :: i
real, allocatable :: arr(:)
allocate(arr(10))
!$acc parallel loop private(arr)
do i=1,10
    arr=1.0
end do
end
