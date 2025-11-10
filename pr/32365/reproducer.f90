subroutine test
      use omp_lib
      implicit none
      integer, parameter :: NT = 4
      integer :: a
      save
      a = 1
!$omp threadprivate(a)
end subroutine test