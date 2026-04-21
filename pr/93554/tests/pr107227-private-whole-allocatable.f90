! PR libgomp/107227 — execution test.
!
! Whole allocatable array used with private clause on an OpenACC loop.
! Same ICE site as PR93554; expected to be resolved by
! r16-8571-g010618b8dcb.  Covers gang/worker/vector/seq and
! 'parallel loop' vs 'kernels loop'.

! { dg-do run }
!TODO { dg-prune-output {using 'vector_length \(32\)', ignoring 1} }

program pr107227
  implicit none
  integer, parameter :: n = 32
  integer :: res(n), i, expect(n)

  do i = 1, n
     expect(i) = 2 * i
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
    integer :: j
    real, allocatable :: arr(:)
    allocate(arr(n))
    res = -1
    !$acc parallel loop gang private(arr) copy(res)
    do j = 1, n
       arr(j) = 2.0 * real(j)
       res(j) = int(arr(j))
    end do
    !$acc end parallel loop
    call check(11, res)
    deallocate(arr)
  end subroutine gang_parallel

  subroutine worker_parallel()
    integer :: j
    real, allocatable :: arr(:)
    allocate(arr(n))
    res = -1
    !$acc parallel num_gangs(4) num_workers(4) vector_length(1) copy(res)
    !$acc loop worker private(arr)
    do j = 1, n
       arr(j) = 2.0 * real(j)
       res(j) = int(arr(j))
    end do
    !$acc end parallel
    call check(12, res)
    deallocate(arr)
  end subroutine worker_parallel

  subroutine vector_parallel()
    integer :: j
    real, allocatable :: arr(:)
    allocate(arr(n))
    res = -1
    !$acc parallel num_gangs(1) num_workers(1) vector_length(32) copy(res)
    !$acc loop vector private(arr)
    do j = 1, n
       arr(j) = 2.0 * real(j)
       res(j) = int(arr(j))
    end do
    !$acc end parallel
    call check(13, res)
    deallocate(arr)
  end subroutine vector_parallel

  subroutine seq_parallel()
    integer :: j
    real, allocatable :: arr(:)
    allocate(arr(n))
    res = -1
    !$acc parallel num_gangs(1) num_workers(1) vector_length(1) copy(res)
    !$acc loop seq private(arr)
    do j = 1, n
       arr(j) = 2.0 * real(j)
       res(j) = int(arr(j))
    end do
    !$acc end parallel
    call check(14, res)
    deallocate(arr)
  end subroutine seq_parallel

  subroutine gang_kernels()
    integer :: j
    real, allocatable :: arr(:)
    allocate(arr(n))
    res = -1
    !$acc kernels copy(res)
    !$acc loop private(arr)
    do j = 1, n
       arr(j) = 2.0 * real(j)
       res(j) = int(arr(j))
    end do
    !$acc end kernels
    call check(15, res)
    deallocate(arr)
  end subroutine gang_kernels

end program pr107227
