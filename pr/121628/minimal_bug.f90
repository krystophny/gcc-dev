program minimal_bug
  implicit none

  type :: nested_t
     type(nested_t), allocatable :: children(:)
     type(nested_t), allocatable :: relatives(:)
  end type nested_t

  type(nested_t) :: a

end program minimal_bug
