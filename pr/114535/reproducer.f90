! GCC PR114535: ICE with elemental finalizer
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=114535
!
! This reproducer triggers an ICE when using elemental finalizers
! across modules with unreferenced symbols.
! Expected: Clean compilation
! GCC 13-14: ICE in gfc_trans_call at fortran/trans-stmt.cc:400
! GCC 15+: Should be fixed

module iv
    implicit none
    type, public :: vs
    contains
        final :: destructor
    end type vs
contains
    elemental subroutine destructor(s)
        type(vs), intent(inout) :: s
    end subroutine
end module

module d
    implicit none
contains
    function en() result(dd)
        use :: iv
        type(vs) :: dd
        return
    end function
end module

module ni
    implicit none
contains
    subroutine iss()
        use :: d
        return
    end subroutine
end module
