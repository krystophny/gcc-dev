! OpenMP control: same structure as PR93554 with omp parallel do private.
! Used as a CFG reference -- OpenMP already accepts the finalization BBs
! (per PR93554 comment #2).

program p
   type t
      integer :: a
      integer, allocatable :: b(:)
   end type
   type(t) :: x
   integer :: i
   !$omp target
   !$omp parallel do private(x)
   do i = 0, 31
      x%a = 1
   end do
   !$omp end target
end
