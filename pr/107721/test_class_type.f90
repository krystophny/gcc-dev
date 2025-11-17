program test_class_type
  implicit none
  class(*), allocatable :: res(:)

  res = [integer :: ([1.0])] ** 2
  call verify_integer (res, 1)
  deallocate (res)

contains
  subroutine verify_integer (x, stopcode)
    class(*), intent(in) :: x(:)
    integer,  intent(in) :: stopcode
    select type (x)
    type is (integer)
       print *, "integer!"
    class default
       print *, "wrong type, not integer!"
       stop stopcode
    end select
  end subroutine verify_integer
end program test_class_type
