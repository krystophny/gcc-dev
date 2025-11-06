module m
  type :: t
     type(t), allocatable :: a
  contains
     final :: my_final
  end type t
contains
  subroutine my_final(self)
    type(t) :: self
  end subroutine my_final
end module m
