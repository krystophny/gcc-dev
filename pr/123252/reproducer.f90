! OpenACC derived-type scalar component wrong on device.
!
! Bugzilla: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123252
!
! This reproducer maps only the allocatable array component, then reads a
! scalar component in a device kernel.  On affected GCC versions the device
! sees the scalar as false/garbage and computes the wrong result.

program pr123252
  use, intrinsic :: iso_fortran_env, only: dp => real64
  implicit none

  type :: container_t
    real(dp), allocatable :: arr(:)
    logical :: flag
    integer :: n
  end type container_t

  type(container_t) :: c
  real(dp), allocatable :: result(:)
  real(dp) :: diff
  integer :: i

  c%n = 100
  c%flag = .true.
  allocate (c%arr(c%n))
  do i = 1, c%n
    c%arr(i) = real(i, dp)
  end do

  !$acc enter data copyin(c%arr(1:c%n))

  allocate (result(c%n))
  result = 0.0_dp

  !$acc data copy(result)
  !$acc parallel loop present(c%arr)
  do i = 1, c%n
    if (c%flag) then
      result(i) = c%arr(i) * 2.0_dp
    else
      result(i) = c%arr(i)
    end if
  end do
  !$acc end parallel loop
  !$acc end data

  diff = maxval(abs(result - 2.0_dp * c%arr))
  if (diff > 1.0e-10_dp) then
    print *, "FAIL: max diff = ", diff
    stop 1
  end if

  print *, "PASS"

  !$acc exit data delete(c%arr)
end program pr123252
