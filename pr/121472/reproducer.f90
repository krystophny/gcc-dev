! GCC PR121472: ICE in gimplify_expr with constructor
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=121472
!
! This reproducer triggers an ICE when using a derived type with
! a final subroutine and a constructor interface.
! Expected: Clean compilation
! GCC 16.0: ICE in gimplify_expr at gimplify.cc:20810
! Status: UNCONFIRMED

module pr121472_m
    implicit none
    type r
    end type

    type ip
        type(r) :: r_member
    contains
        final :: ipd
    end type

    interface ip
        module procedure ipc
    end interface
contains
    subroutine ipd(this)
        type(ip), intent(inout) :: this
    end subroutine

    function ipc() result(res)
        type(ip) :: res
    end function
end module

program test
    use pr121472_m
    implicit none
    type(ip) :: p
    p = ip()
end program
