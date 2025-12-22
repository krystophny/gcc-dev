module types
    use, intrinsic :: iso_fortran_env, only: dp => real64
    implicit none

    type :: des_t
        real(dp) :: a
    end type des_t

contains

    subroutine copyin_simple(var)
        type(des_t), intent(inout) :: var
!$acc enter data copyin(var)
    end subroutine copyin_simple

end module types

program main
    use types, only: des_t, copyin_simple
    implicit none

    type(des_t) :: wdes1

!$acc enter data copyin(wdes1)
    call copyin_simple(wdes1)
end program main
