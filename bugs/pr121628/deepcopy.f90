program deepcopy
  use, intrinsic :: iso_fortran_env, only: dp => real64
  implicit none

  type :: nested_t
     character(len=10)             :: name
     real(dp),         allocatable :: values(:)
     type(nested_t),   allocatable :: children(:)
  end type nested_t

  type(nested_t) :: a, b

  print *, "Building nested structure in b..."
  b%name = "root"
  allocate (b%values(3))
  b%values = [1.0d0, 2.0d0, 3.0d0]
  allocate (b%children(2))
  b%children(1)%name = "child1"
  allocate (b%children(1)%values(2))
  b%children(1)%values = [10.0d0, 20.0d0]
  b%children(2)%name = "child2"
  allocate (b%children(2)%values(3))
  b%children(2)%values = [100.0d0, 200.0d0, 300.0d0]
  allocate (b%children(1)%children(1))
  b%children(1)%children(1)%name = "grandchild"
  allocate (b%children(1)%children(1)%values(1))
  b%children(1)%children(1)%values(1) = 999.0d0

  print *, "Deep copy: a = b"
  a = b

  print *, "Verify allocations after copy..."
  if (.not. allocated(a%values)) error stop "a%values not allocated"
  if (.not. allocated(a%children)) error stop "a%children not allocated"
  if (.not. allocated(a%children(1)%values)) error stop "a%children(1)%values not allocated"
  if (.not. allocated(a%children(2)%values)) error stop "a%children(2)%values not allocated"
  if (.not. allocated(a%children(1)%children)) error stop "a%children(1)%children not allocated"
  if (.not. allocated(a%children(1)%children(1)%values)) &
      error stop "a%children(1)%children(1)%values not allocated"

  print *, "Verify data integrity..."
  if (a%name /= "root") error stop "a%name incorrect"
  if (any(abs(a%values - [1.0d0, 2.0d0, 3.0d0]) > 1.0d-12)) &
      error stop "a%values incorrect"
  if (a%children(1)%name /= "child1") error stop "a%children(1)%name incorrect"
  if (any(abs(a%children(1)%values - [10.0d0, 20.0d0]) > 1.0d-12)) &
      error stop "a%children(1)%values incorrect"
  if (a%children(2)%name /= "child2") error stop "a%children(2)%name incorrect"
  if (any(abs(a%children(2)%values - [100.0d0, 200.0d0, 300.0d0]) > 1.0d-12)) &
      error stop "a%children(2)%values incorrect"
  if (a%children(1)%children(1)%name /= "grandchild") &
      error stop "a%children(1)%children(1)%name incorrect"
  if (abs(a%children(1)%children(1)%values(1) - 999.0d0) > 1.0d-12) &
      error stop "a%children(1)%children(1)%values incorrect"

  print *, "Verify deep copy (modify a, check b unchanged)..."
  a%values(1) = -1.0d0
  a%children(1)%values(1) = -10.0d0
  a%children(1)%children(1)%values(1) = -999.0d0

  if (abs(b%values(1) - 1.0d0) > 1.0d-12) &
      error stop "SHALLOW COPY: b%values(1) was modified when a was changed"
  if (abs(b%children(1)%values(1) - 10.0d0) > 1.0d-12) &
      error stop "SHALLOW COPY: b%children(1)%values(1) was modified when a was changed"
  if (abs(b%children(1)%children(1)%values(1) - 999.0d0) > 1.0d-12) &
      error stop "SHALLOW COPY: b%children(1)%children(1)%values(1) was modified when a was changed"

  print *, "All checks passed!"

end program deepcopy
