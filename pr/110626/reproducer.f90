! PR fortran/110626 - finalization sees a stale value in derived-type assignment.
!
! In a derived-type intrinsic assignment, a finalizable component that has a
! defined assignment is finalized twice: once by the whole-derived-type
! finalization of the lhs and once by the INTENT(OUT) argument of the defined
! assignment.  Both finalizations are required, but the second must see the
! value left by the first, as in ifx and flang.  Before the fix gfortran
! finalized a trivial copy of the old lhs the second time, so the final
! subroutine saw the stale old value instead, which breaks reference counting.
!
! The final subroutine sets the tag to -1, so the value the second finalization
! observes is visible.  Fails on unfixed trunk (stop 3), passes once fixed.
!
! Own work; not derived from the Bugzilla attachment.
module defasgn_m
  implicit none

  type :: inner_t
     integer :: tag = 0
   contains
     final :: inner_final
     procedure :: inner_copy
     generic :: assignment(=) => inner_copy
  end type

  type :: outer_t
     type(inner_t) :: part
  end type

  integer :: n_final = 0
  integer :: seen(4) = 0

contains

  subroutine inner_final (self)
    type(inner_t), intent(inout) :: self
    n_final = n_final + 1
    if (n_final <= size (seen)) seen(n_final) = self%tag
    self%tag = -1
  end subroutine

  subroutine inner_copy (lhs, rhs)
    class(inner_t), intent(out) :: lhs
    type(inner_t), intent(in) :: rhs
    lhs%tag = rhs%tag + 1
  end subroutine

end module

program defasgn_p
  use defasgn_m
  implicit none
  type(outer_t) :: ao, bo

  ao%part%tag = 7
  bo%part%tag = 42

  n_final = 0
  bo = ao

  print '(a,i0,a,i0,a,i0)', 'finals=', n_final, ' seen1=', seen(1), ' seen2=', seen(2)

  if (n_final /= 2)  stop 1   ! two finalizations of the old component
  if (seen(1) /= 42) stop 2   ! first sees the old value
  if (seen(2) /= -1) stop 3   ! second sees the value left by the first
  if (bo%part%tag /= 8) stop 4
  print *, 'OK'
end program
