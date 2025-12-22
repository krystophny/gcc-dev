program mre
  use, intrinsic :: iso_fortran_env, only: dp => real64
  implicit none

  type :: container_t
    integer :: n
    real(dp), allocatable :: data(:)
  end type container_t

  type(container_t) :: c
  integer :: i

  c%n = 1000
  allocate(c%data(c%n))
  c%data = [(real(i, dp), i = 1, c%n)]

  print *, "Array size (bytes):", size(c%data) * 8

  !$acc enter data copyin(c%data)

  print *, "PASS"

  !$acc exit data delete(c%data)
end program mre
