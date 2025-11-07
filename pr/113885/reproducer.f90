! GCC PR113885: ICE in gimplify_expr with finalization
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=113885
!
! This reproducer triggers an ICE when using elemental functions
! with finalization on zero-component derived types.
! Expected: Clean compilation
! GCC 13.2.1-14.0: ICE in gimplify_expr at gimplify.cc:18658
! GCC 15+: Should be fixed

module pr113885_m
    implicit none
    type t
    contains
        final :: finalize
    end type t
contains
    subroutine finalize(x)
        type(t), intent(inout) :: x
    end subroutine

    impure elemental function elem(x)
        type(t), intent(in) :: x
        type(t) :: elem
    end function

    subroutine test1(x)
        type(t) :: x(:)
        x = elem(x)
    end subroutine
end module
