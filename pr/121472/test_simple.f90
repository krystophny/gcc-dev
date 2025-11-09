! Simplified from finalize_49.f90 - minimal constructor+finalizer test
module m
    implicit none
    type t
    contains
        final :: fin
    end type

    interface t
        module procedure ctor
    end interface
contains
    pure function ctor() result(res)
        type(t) :: res
    end function

    pure subroutine fin(this)
        type(t), intent(inout) :: this
    end subroutine
end module

program test
    use m
    implicit none
    type(t) :: p
    p = t()
end program
