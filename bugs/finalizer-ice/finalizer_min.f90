module m
  type :: node
     type(node), allocatable :: child(:)
   contains
     final :: finalize_node
  end type node
contains
  subroutine finalize_node(self)
    type(node), intent(inout) :: self
  end subroutine finalize_node
end module m

program test
  use m
  type(node) :: a, b
  allocate(a%child(1))
  b = a
end program test
