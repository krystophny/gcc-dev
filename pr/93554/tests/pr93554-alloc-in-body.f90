! PR fortran/93554 -- runtime free-edge stress.
!
! The companion compile-time regression test (pr93554.f90 under
! gcc/testsuite/gfortran.dg/goacc/) only exercises the CFG edge on the
! pass dump.  This test exits the OpenACC region with the allocatable
! component still allocated, which forces the per-thread finalisation
! inserted by the Fortran front end to run at region exit.  Before
! r16-8571-g010618b8dcb this ICE'd in expand_oacc_for; afterwards the
! finalisation-free edge must execute for every thread and produce
! correct results.  On NVPTX the call surfaces in GOMP_DEBUG=1 as
! __nvptx_free.

! { dg-do run }

program pr93554_alloc_in_body
  implicit none
  integer, parameter :: n = 128
  integer :: res(n), expect(n), j
  type :: t
     integer :: a
     integer, allocatable :: b(:)
  end type
  type(t) :: x

  do j = 1, n
     expect(j) = 3*j + 7
  end do

  res = -1

  !$acc parallel loop gang worker vector private(x) copy(res) &
  !$acc&              num_gangs(4) num_workers(4) vector_length(8)
  do j = 1, n
     if (.not. allocated(x%b)) allocate(x%b(8))
     x%b    = 0
     x%b(1) = j
     x%b(5) = 2*j + 7
     res(j) = x%b(1) + x%b(5)
  end do
  !$acc end parallel loop

  do j = 1, n
     if (res(j) /= expect(j)) stop 1
  end do
end program pr93554_alloc_in_body
