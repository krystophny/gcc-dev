! Test ISO F2018 7.5.6.3 compliance for PR 121472
!
! ISO/IEC 1539-1:2018 Section 7.5.6.3 paragraph 3:
! "Finalization occurs ... (3) when an intrinsic assignment statement is
! executed and ... the variable is of a finalizable type, the variable is
! finalized after evaluation of expr and before the definition of the variable."
!
! For the statement: p = ip()
!
! Expected finalization count: 2
!   (1) Function result from ip() after assignment per 7.5.6.3(3)
!   (2) Variable p at end of program scope per 7.5.6.3(1)

module test_m
    implicit none
    integer :: constructor_count = 0
    integer :: finalizer_count = 0

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
        finalizer_count = finalizer_count + 1
    end subroutine

    function ipc() result(res)
        type(ip) :: res
        constructor_count = constructor_count + 1
    end function
end module

program test_iso_compliance
    use test_m
    implicit none
    type(ip) :: p

    p = ip()

    ! At this point we should have:
    ! - 1 constructor call (ip())
    ! - 1 finalization (function result after assignment per F2018 7.5.6.3)
    ! Note: variable 'p' will be finalized at end of scope

    print '(a,i0)', ' constructor: ', constructor_count
    print '(a,i0)', ' finalizer: ', finalizer_count

end program
! After program ends, 'p' is finalized, bringing total to 2 finalizations
