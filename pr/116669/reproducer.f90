! GCC PR116669: Crash on circular derived type component
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=116669
!
! This reproducer triggers a segfault when processing circular
! derived type definitions with indirect references.
! Expected: Clean compilation
! GCC 10-14.2: Segmentation fault
! GCC 15+: Should be fixed

module problem2_m
    implicit none

    type ast_expression_t
        type(ast_operation_call_t), allocatable :: op_call
    end type

    type ast_operation_call_t
        type(ast_expression_t), allocatable :: args(:)
    end type
end module
