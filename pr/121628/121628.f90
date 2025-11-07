program minimal_bug
  implicit none
    
  type :: nested_t
     character(len=10)             :: name
     type(nested_t),   allocatable :: children(:)
  end type nested_t
    
  type(nested_t) :: a, b

  b%name = "root"
  allocate (b%children(1))
  b%children(1)%name = "child"
  allocate (b%children(1)%children(1))
  b%children(1)%children(1)%name = "grandchild"
    
  ! Repeated circular assignments trigger memory corruption
  print *, "1) a=b:"
  a = b
  print *, "Check allocation status after 1)"
  print *, "a:", allocated (a%children), allocated (a%children(1)%children)
  print *, "b:", allocated (b%children), allocated (b%children(1)%children)
  if (.not. allocated (a%children(1)%children)) stop 1
  if (.not. allocated (b%children(1)%children)) stop 11

! print *, "explicitly deallocate components of b"
! deallocate (b%children(1)%children); deallocate (b%children)

  print *, "2) b=a:"
  b = a  
  print *, "Check allocation status after 2)"
  print *, "a:", allocated (a%children), allocated (a%children(1)%children)
  print *, "b:", allocated (b%children), allocated (b%children(1)%children)
  if (.not. allocated (a%children(1)%children)) stop 2
  if (.not. allocated (b%children(1)%children)) stop 22

! print *, "explicitly deallocate components of a"
! deallocate (a%children(1)%children); deallocate (a%children)

  print *, "3) a=b:"
  a = b
  print *, "a:", allocated (a%children), allocated (a%children(1)%children)
  print *, "4) b=a:"
  b = a  
  print *, "b:", allocated (b%children), allocated (b%children(1)%children)
end program minimal_bug
