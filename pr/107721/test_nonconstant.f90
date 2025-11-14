! Test non-constant expressions in array constructors with type-spec
program test_nonconstant
  implicit none
  integer :: i
  real :: r
  integer, dimension(2) :: iarr
  real, dimension(2) :: rarr

  ! Non-constant variable
  i = 2
  r = 3.5

  ! INTEGER constructor with non-constant REAL variable
  ! Should convert r to integer (3) then square it
  iarr = [integer :: i, nint(r)]
  print *, "Integer array:", iarr
  if (any(iarr /= [2, 4])) stop 1

  ! REAL constructor with non-constant INTEGER variable
  ! Should convert i to real (2.0) then square it
  rarr = [real :: i, nint(r)]
  print *, "Real array:", rarr
  if (any(abs(rarr - [2.0, 4.0]) > 0.001)) stop 2

  ! With parentheses around non-constant
  iarr = [integer :: (i), nint(r)]
  print *, "Integer with parens:", iarr
  if (any(iarr /= [2, 4])) stop 3

  ! Operations on non-constant constructor
  iarr(1:1) = [integer :: i] ** 2
  print *, "Non-constant squared:", iarr(1)
  if (iarr(1) /= 4) stop 4

  print *, "All non-constant tests passed!"
end program test_nonconstant
