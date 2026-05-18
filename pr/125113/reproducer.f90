! PR fortran/125113 - segfault accessing remote image with coarray of
! derived type containing pointer component.
! Rewritten reduction from Neil Carlson's reported trigger.
program pr125113
  implicit none

  type :: box
    integer, pointer :: data(:) => null()
  end type

  integer, allocatable, target :: src(:)
  integer :: dest(2)
  integer :: i, first_gid, last_gid
  type(box), allocatable :: buffer[:]

  if (this_image() == 1) then
    src = [(i, i = 1, 2*num_images())]
  else
    allocate(src(0))
  end if

  first_gid = 1+2*(this_image()-1)
  last_gid  = 2*this_image()

  allocate(buffer[*])
  buffer%data => src

  sync all
  dest = buffer[1]%data(first_gid:last_gid)
  if (any(dest /= [first_gid, last_gid])) error stop
end program
