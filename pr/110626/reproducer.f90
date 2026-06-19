! PR fortran/110626 - duplicated finalization in derived-type assignment.
!
! A type with a FINAL subroutine and a defined assignment, used directly,
! is finalized the same number of times as when it is a component of an
! enclosing type assigned by intrinsic assignment.  Before the fix the
! component case finalizes the old value twice: once by the whole-struct
! finalization of the LHS and once more by the intent(out) temporary that
! carries the component's defined assignment.
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
  integer :: n_copy = 0

contains

  subroutine inner_final (self)
    type(inner_t), intent(inout) :: self
    n_final = n_final + 1
  end subroutine

  subroutine inner_copy (lhs, rhs)
    class(inner_t), intent(out) :: lhs
    type(inner_t), intent(in) :: rhs
    n_copy = n_copy + 1
    lhs%tag = rhs%tag
  end subroutine

end module

program defasgn_p
  use defasgn_m
  implicit none
  type(inner_t) :: ai, bi
  type(outer_t) :: ao, bo
  integer :: f_direct, c_direct, f_comp, c_comp

  ! Direct assignment of the finalizable type.
  ai%tag = 15
  n_final = 0; n_copy = 0
  bi = ai
  f_direct = n_final; c_direct = n_copy

  ! Same type as a component, assigned through the enclosing type.
  ao%part%tag = 15
  n_final = 0; n_copy = 0
  bo = ao
  f_comp = n_final; c_comp = n_copy

  print '(a,i0,a,i0)', 'direct: final=', f_direct, ' copy=', c_direct
  print '(a,i0,a,i0)', 'comp  : final=', f_comp,   ' copy=', c_comp

  if (c_comp /= c_direct) stop 1
  if (f_comp /= f_direct) stop 2
  print *, 'OK'
end program
