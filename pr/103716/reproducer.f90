! GCC PR103716: ICE with character len inquiry
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103716
!
! This reproducer triggers an ICE when using len inquiry on
! assumed-length character arrays.
! Expected: Clean compilation
! GCC 11-13: ICE in gimplify_expr at gimplify.c:15964
! GCC 14+: Should be fixed

function f(x) result(res)
    implicit none
    character(*) :: x(3)
    integer :: res
    res = g(x%len)
contains
    function g(n)
        integer :: n
        integer :: g
        g = n
    end function
end function
