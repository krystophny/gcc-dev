subroutine s(x, res)
  integer :: x(..)
  integer, allocatable :: res(:)

  call t(x)

contains

  subroutine t(y)
    integer, contiguous :: y(..)

    select rank (y)
      rank (1)
        res = 2 * y
    end select
  end subroutine t
end subroutine s

program p
  integer :: x(4) = [42, 84, 126, 168]
  integer :: u(4, 4)
  integer, allocatable :: z(:)

  u = reshape ([x, 4 * x, 16 * x, 64 * x], [4, 4])

  call s(x(1:4:2), z)
  print *, z

  call s(u(1, :), z)
  print *, z
end program p
