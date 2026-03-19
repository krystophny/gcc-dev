! PR84779: mixed ENTRY results with -O1 -fdefault-integer-8
! Minimal reproducer from Bugzilla comment #13.
! Compile: gfortran -O1 -fdefault-integer-8 -c reproducer.f90
complex function f2 (a)
  implicit none
  integer :: a
  logical :: e2

  entry e2 (a)

  if (a > 0) then
    e2 = .true.
  else
    f2 = 45
  endif
end
