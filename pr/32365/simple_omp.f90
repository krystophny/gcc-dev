subroutine test
      implicit none
      integer :: a
      a = 1
!$omp threadprivate(a)
end subroutine test