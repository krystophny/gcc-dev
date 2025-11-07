! GCC PR82622: ICE with PDT allocation
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82622
!
! This reproducer triggers an ICE when allocating parameterized
! derived types with nested type parameters.
! Expected: Clean compilation and execution
! Older GCC: ICE in structure_alloc_comps at fortran/trans-array.c:8963
! Modern GCC: Should be fixed

program pr82622
    implicit none
    type t(a)
        integer, len :: a
    end type

    type t2(b)
        integer, len :: b
        type(t(1)) :: r(b)
    end type

    type(t2(:)), allocatable :: x
    allocate (t2(3) :: x)
end program
