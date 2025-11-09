! PR96255: Test DO CONCURRENT with optional type specification
! F2018 allows:
!   do concurrent (integer :: i=1:10)
!     ...
!   end do

program looper
   implicit none

   ! Test 1: Simple do concurrent with type spec
   do concurrent (integer :: i=1:10)
     print *, "i =", i
   end do

   print *, "All done!"

end program looper
