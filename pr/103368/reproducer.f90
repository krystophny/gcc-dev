! GCC PR103368: ICE with class(*) in structure constructor
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=103368
!
! This reproducer triggers an ICE when passing a structure
! constructor with incompatible types to a subroutine.
! Expected: Clean compilation (code is valid)
! GCC 11-13: ICE in gimplify_expr at gimplify.c:15668
! GCC 14+: Should be fixed

program pr103368
    implicit none
    type t
    end type
    type t2
        class(*), allocatable :: a
    end type
    type(t) :: x
    call sub (t2(x))
contains
    subroutine sub(arg)
        type(t2), intent(in) :: arg
    end subroutine
end program
