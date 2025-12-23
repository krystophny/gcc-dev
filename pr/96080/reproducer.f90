! PR 96080: OpenACC runtime library routines vs Fortran pointer semantics
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96080
!
! Tests acc_is_present behavior with Fortran pointers.
! The OpenACC spec is ambiguous about whether runtime routines should
! operate on the pointer object or dereference to the target.

program pr96080
  use openacc
  use iso_c_binding, only: c_loc, c_sizeof
  implicit none

  integer, dimension(:), allocatable, target :: array_target
  integer, dimension(:), pointer :: array_ptr

  integer :: i
  logical :: test_passed

  test_passed = .true.

  ! Initialize
  allocate(array_target(10))
  array_target = [(i, i=1,10)]
  array_ptr => array_target

  print *, "=== PR 96080: OpenACC pointer semantics ==="
  print *

  ! Test 1: Array target mapped, check via pointer
  print *, "Test 1: Map array target, check acc_is_present(array_ptr)"
  !$acc enter data copyin(array_target)
  if (acc_is_present(array_ptr)) then
    print *, "  PASS: pointer's target detected as present"
  else
    print *, "  FAIL: pointer's target NOT detected"
    test_passed = .false.
  end if
  !$acc exit data delete(array_target)
  print *

  ! Test 2: Map pointer directly via directive
  print *, "Test 2: Map array_ptr via directive, check acc_is_present(array_ptr)"
  !$acc enter data copyin(array_ptr)
  if (acc_is_present(array_ptr)) then
    print *, "  PASS: directly mapped pointer detected"
  else
    print *, "  FAIL: directly mapped pointer NOT detected"
    test_passed = .false.
  end if
  !$acc exit data delete(array_ptr)
  print *

  ! Test 3: Map target, then attach pointer
  print *, "Test 3: Map target + attach pointer, check acc_is_present(array_ptr)"
  !$acc enter data copyin(array_target)
  !$acc enter data attach(array_ptr)
  if (acc_is_present(array_ptr)) then
    print *, "  PASS: attached pointer detected as present"
  else
    print *, "  FAIL: attached pointer NOT detected"
    test_passed = .false.
  end if
  !$acc exit data detach(array_ptr)
  !$acc exit data delete(array_target)
  print *

  ! Test 4: Subroutine with pointer argument
  print *, "Test 4: Pass pointer to subroutine, check inside"
  !$acc enter data copyin(array_target)
  call check_pointer_in_sub(array_ptr)
  !$acc exit data delete(array_target)
  print *

  ! Test 5: Subroutine with assumed-shape (non-pointer) from pointer
  print *, "Test 5: Pass pointer as assumed-shape, check inside"
  !$acc enter data copyin(array_target)
  call check_assumed_shape(array_ptr)
  !$acc exit data delete(array_target)
  print *

  ! Summary
  print *, "=== Summary ==="
  if (test_passed) then
    print *, "All tests passed"
  else
    print *, "Some tests failed"
    stop 1
  end if

contains

  subroutine check_pointer_in_sub(p)
    integer, pointer, intent(in) :: p(:)

    if (acc_is_present(p)) then
      print *, "  PASS: pointer argument detected as present"
    else
      print *, "  FAIL: pointer argument NOT detected"
      test_passed = .false.
    end if
  end subroutine

  subroutine check_assumed_shape(x)
    integer, intent(in) :: x(:)

    ! This is the PR 123280 case - assumed-shape from pointer
    if (acc_is_present(x)) then
      print *, "  PASS: assumed-shape from pointer detected as present"
    else
      print *, "  FAIL: assumed-shape from pointer NOT detected"
      test_passed = .false.
    end if
  end subroutine

end program pr96080
