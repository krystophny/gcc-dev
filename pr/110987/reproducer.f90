! GCC PR110987: Segfault with finalization of temporary
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=110987
!
! This reproducer triggers a segfault when finalizing temporaries
! in inheritance scenarios with zero-component derived types.
! Expected: Clean compilation and execution
! GCC 13.2.0: Segmentation fault at runtime
! GCC 14+: Should be fixed

module pr110987_m
    implicit none
    type :: t1_pointer
        integer :: i
    end type

    type :: t1
        class(t1_pointer), allocatable :: next(:)
    contains
        final :: t1_destructor
    end type

    type, extends(t1) :: t3
    contains
        final :: t3_destructor
    end type
contains
    subroutine t1_destructor(this)
        type(t1), intent(inout) :: this
    end subroutine

    subroutine t3_destructor(this)
        type(t3), intent(inout) :: this
    end subroutine
end module

program test
    use pr110987_m
    implicit none
    type(t3) :: x3
    x3 = t3()
end program
