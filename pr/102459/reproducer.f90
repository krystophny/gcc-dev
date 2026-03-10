program p
  type t
    integer :: a(2)
  end type
  type(t) :: x(8)

  !$omp task depend (iterator(j=1:8), out:x(j)%a)
  !$omp end task
end
