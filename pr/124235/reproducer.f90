! { dg-do compile }
! PR fortran/124235 - ICE in ALLOCATE of sub-objects with recursive types
!
! Allocating a sub-object of an already-allocated array component
! of a derived type with recursive/mutually-referencing structure
! causes an ICE during tree lowering.

program pr124235
  implicit none

  type :: node_t
    integer, allocatable :: values(:)
    type(node_t), allocatable :: children(:)
    integer :: tag
  end type

  type :: tree_t
    type(node_t), allocatable :: roots(:)
  end type

  type(tree_t) :: forest

  allocate(forest%roots(4))
  allocate(forest%roots(1)%children(3))

end program
