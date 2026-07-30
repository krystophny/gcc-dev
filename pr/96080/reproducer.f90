program pr96080_pointer_runtime
  use openacc
  implicit none

  integer, target :: field(23)
  integer, pointer :: alias(:)
  integer :: i

  do i = 1, size(field)
    field(i) = 5 * i + 2
  end do
  alias => field

  !$acc enter data copyin(field)

  if (.not. acc_is_present(alias)) stop 1

  field = -1
  call acc_update_self(alias)
  do i = 1, size(field)
    if (field(i) /= 5 * i + 2) stop 2
  end do

  do i = 1, size(field)
    field(i) = 100 - 3 * i
  end do
  call acc_update_device(alias)
  field = -2
  call acc_update_self(alias)
  do i = 1, size(field)
    if (field(i) /= 100 - 3 * i) stop 3
  end do

  !$acc exit data delete(field)
end program pr96080_pointer_runtime
