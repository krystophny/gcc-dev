! Minimal reproducer for GCC Bug 123280
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=123280
!
! acc_is_present fails for assumed-shape dummy argument mapped by caller
!
! Compile: gfortran -fopenacc -foffload=nvptx-none -o reproducer reproducer.f90
! Run: ./reproducer
!
! Expected: Both tests print "PASS"
! Actual (GCC): Test 2 prints "FAIL"
! Actual (nvfortran): Both tests print "PASS"

program mre
  use openacc
  implicit none

  real, allocatable :: arr(:)
  integer, parameter :: n = 100

  allocate(arr(n))
  arr = 1.0

  ! Map data to device
  !$acc enter data copyin(arr)

  ! Test 1: Direct check - PASS
  if (acc_is_present(arr)) then
    print *, "Test 1 (direct): PASS"
  else
    print *, "Test 1 (direct): FAIL"
    stop 1
  end if

  ! Test 2: Check via subroutine with assumed-shape - FAIL
  call check_present(arr)

  !$acc exit data delete(arr)

contains

  subroutine check_present(x)
    real, intent(in) :: x(:)  ! assumed-shape dummy argument

    ! This returns .false. even though the underlying data IS present
    if (acc_is_present(x)) then
      print *, "Test 2 (assumed-shape dummy): PASS"
    else
      print *, "Test 2 (assumed-shape dummy): FAIL"
      stop 2
    end if
  end subroutine check_present

end program mre
