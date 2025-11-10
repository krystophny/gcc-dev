subroutine test_common
      implicit none
      integer :: i
      i = 1
      common /myi/ i
end subroutine test_common