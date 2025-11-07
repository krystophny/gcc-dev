! GCC PR104684: Coarray ICE in verify_gimple
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=104684
!
! This reproducer triggers an ICE when using pointer assignments
! with coarrays and allocatable arrays in derived types.
! Expected: Clean compilation with -fcoarray=single
! GCC 12-15: ICE verify_gimple failed
! GCC 16+: Should be fixed

program pr104684
    implicit none
    type :: index_map
        integer, allocatable :: send_index(:)
    end type
    type(index_map) :: imap
contains
    subroutine sub(this)
        type(index_map), intent(inout), target :: this
        type :: box
            integer, pointer :: array(:)
        end type
        type(box), allocatable :: buffer[:]
        allocate(buffer[*])
        buffer%array => this%send_index
    end subroutine
end program
