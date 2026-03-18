! PR84779: ICE with -O1 -fdefault-integer-8 and ENTRY
! Compile: gfortran -O1 -fdefault-integer-8 reproducer.f90
function f1 (n)
  integer, intent(in) :: n
  integer :: f1, e1
  f1 = n
  return
entry e1 (n)
  e1 = n + 1
end function

program test
  integer :: f1, e1
  logical(8) :: r
  r = f1(0) == 0
  if (.not. r) stop 1
  r = e1(0) == 1
  if (.not. r) stop 2
end program
