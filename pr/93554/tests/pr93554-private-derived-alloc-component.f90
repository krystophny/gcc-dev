! PR fortran/93554 — execution test.
!
! Exercises "private(x)" on an OpenACC loop where x is a derived type
! with an allocatable component.  Four subroutines cover the four
! partitioning levels (gang, worker, vector, seq) that 'acc loop' may
! carry, in both the 'parallel loop' and 'kernels loop' forms.
!
! Before r16-8571-g010618b8dcb this ICE'd in expand_oacc_for at
! omp-expand.cc; afterwards it compiles and is expected to execute
! correctly: the private copy of 'x' must not leak results into the
! loop-body arithmetic performed through the shared output array.

! { dg-do run }

program pr93554
  implicit none
  integer, parameter :: n = 32
  integer :: res(n), i, expect(n)

  do i = 1, n
     expect(i) = 10 + i
  end do

  call gang_parallel()
  call worker_parallel()
  call vector_parallel()
  call seq_parallel()
  call gang_kernels()

contains

  subroutine check(tag, res_)
    integer, intent(in) :: tag
    integer, intent(in) :: res_(n)
    integer :: j
    do j = 1, n
       if (res_(j) /= expect(j)) then
          write(0,*) "tag=", tag, " j=", j, " got=", res_(j), " want=", expect(j)
          stop tag
       end if
    end do
  end subroutine check

  subroutine gang_parallel()
    type :: t
       integer :: a
       integer, allocatable :: b(:)
    end type
    type(t) :: x
    integer :: j
    res = -1
    !$acc parallel loop gang private(x) copy(res)
    do j = 1, n
       x%a = 10 + j
       res(j) = x%a
    end do
    !$acc end parallel loop
    call check(1, res)
  end subroutine gang_parallel

  subroutine worker_parallel()
    type :: t
       integer :: a
       integer, allocatable :: b(:)
    end type
    type(t) :: x
    integer :: j
    res = -1
    !$acc parallel num_gangs(4) num_workers(4) vector_length(1) copy(res)
    !$acc loop worker private(x)
    do j = 1, n
       x%a = 10 + j
       res(j) = x%a
    end do
    !$acc end parallel
    call check(2, res)
  end subroutine worker_parallel

  subroutine vector_parallel()
    type :: t
       integer :: a
       integer, allocatable :: b(:)
    end type
    type(t) :: x
    integer :: j
    res = -1
    !$acc parallel num_gangs(1) num_workers(1) vector_length(32) copy(res)
    !$acc loop vector private(x)
    do j = 1, n
       x%a = 10 + j
       res(j) = x%a
    end do
    !$acc end parallel
    call check(3, res)
  end subroutine vector_parallel

  subroutine seq_parallel()
    type :: t
       integer :: a
       integer, allocatable :: b(:)
    end type
    type(t) :: x
    integer :: j
    res = -1
    !$acc parallel num_gangs(1) num_workers(1) vector_length(1) copy(res)
    !$acc loop seq private(x)
    do j = 1, n
       x%a = 10 + j
       res(j) = x%a
    end do
    !$acc end parallel
    call check(4, res)
  end subroutine seq_parallel

  subroutine gang_kernels()
    type :: t
       integer :: a
       integer, allocatable :: b(:)
    end type
    type(t) :: x
    integer :: j
    res = -1
    !$acc kernels copy(res)
    !$acc loop private(x)
    do j = 1, n
       x%a = 10 + j
       res(j) = x%a
    end do
    !$acc end kernels
    call check(5, res)
  end subroutine gang_kernels

end program pr93554
