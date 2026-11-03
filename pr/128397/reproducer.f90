module m
  implicit none
contains
  subroutine matcher (n)
    integer, intent(in) :: n
    real :: oracle(n)
    logical :: candidates(size (oracle))
    print *, 'expected extents: 3 3; actual:', size (oracle), size (candidates)
    if (size (candidates) /= 3) error stop 'wrong extent'
  contains
    logical function assigned ()
      assigned = candidates(1)
    end function
  end subroutine
end module

program p
  use m
  call matcher (3)
end program
