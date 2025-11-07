! GCC PR122191: ICE with composite PDT result
! https://gcc.gnu.org/bugzilla/show_bug.cgi?id=122191
!
! This reproducer triggers an ICE when processing parameterized
! derived types with interface bodies and allocatable arrays.
! Expected: Clean compilation
! Older GCC: ICE in gimplify_var_or_parm_decl at gimplify.cc:3354
! Modern GCC: Should be fixed

module input_output_pair_m
    implicit none

    type input_output_pair_t(k)
        integer, kind :: k
    end type

    type mini_batch_t(k)
        integer, kind :: k = kind(1.)
        type(input_output_pair_t(k)), allocatable :: input_output_pairs_(:)
    end type

    interface
        module function default_real_construct()
            implicit none
            type(mini_batch_t) default_real_construct
        end function
    end interface
end module
