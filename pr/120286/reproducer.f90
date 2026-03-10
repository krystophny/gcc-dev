program main
  implicit none

  type foo_t
    integer :: dummy
  end type foo_t

  type fooPtr_t
    class(foo_t), pointer :: p
  end type fooPtr_t

  type fooPtrStack_t
    class(fooPtr_t), allocatable :: list(:)
  end type fooPtrStack_t

  type(fooPtrStack_t) :: x
  class(foo_t), pointer :: ptr
  integer :: it, n

  allocate (x%list(1))
  allocate (x%list(1)%p)
  x%list(1)%p%dummy = 7

  do it = 1, 4
!$omp parallel do default(none) private(n, ptr) shared(x)
    do n = 1, 1
      ptr => x%list(n)%p
    end do
!$omp end parallel do
  end do

  print '(a)', 'done'
end program main
