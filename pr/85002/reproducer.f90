! GCC PR85002: Coarray ICE in fold_ternary_loc
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=85002
!
! This reproducer triggers an ICE when using coarrays with
! allocatable components in derived types.
! Expected: Clean compilation with -fcoarray=single
! GCC 12-15: ICE in fold_ternary_loc at fold-const.c:11360
! GCC 16+: Should be fixed

program pr85002
    implicit none
    type t2
        integer, allocatable :: b(:)
    end type
    type(t2) :: y[*]
    y = t2([123])
end program
