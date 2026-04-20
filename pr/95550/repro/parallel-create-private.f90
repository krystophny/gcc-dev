! PR middle-end/95550
! Reproducer by burnus@gcc.gnu.org, 2020-06-05 (Bugzilla comment #0).
! Compile with: gfortran -c -fopenacc parallel-create-private.f90
!
! Pre-fix: ICE in expand_oacc_for (same site as PR93554).
! Post-fix: compiles cleanly.

program main
  implicit none (type, external)
  integer :: j, i
  integer, allocatable :: A(:)

  A = [(3*j, j=1, 10)]

  !$acc parallel create(A)
    A(:) = [(-2*i, i = 1, size(A))]
    !$acc loop private(A)
    do i = 1, 10
      A(i) = 9*i
    end do
  !$acc end parallel
end
