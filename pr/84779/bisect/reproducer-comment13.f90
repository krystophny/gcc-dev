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
