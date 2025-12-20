program p
  integer :: a(2)

  !$omp parallel do linear(a)
  do i = 1, 8
    a = a + 1
  end do
end program p

