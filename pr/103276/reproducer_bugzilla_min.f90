module repro
    implicit none

    type :: simple_t
        integer :: a
    end type simple_t

contains

    subroutine copyin_simple_1(var)
        type(simple_t), intent(inout) :: var
!$acc enter data copyin(var)
    end subroutine copyin_simple_1

    subroutine copyin_simple_2(var)
        type(simple_t), intent(inout) :: var
!$acc enter data copyin(var)
    end subroutine copyin_simple_2

end module repro

program main
    use repro, only: simple_t, copyin_simple_1, copyin_simple_2
    implicit none

    type(simple_t) :: v

    call copyin_simple_1(v)
    call copyin_simple_2(v)
end program main
