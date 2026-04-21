! PR middle-end/95550 — execution test.
!
! Shared allocatable A created on the device with 'acc parallel create(A)',
! then used privately inside an 'acc loop private(A)'.  Same ICE site as
! PR93554; expected to be resolved by r16-8571-g010618b8dcb.
!
! Post-region the host-side A must be unchanged (create does not copy
! back).  We also exercise an analogous 'acc kernels' variant.

! { dg-do run }
!TODO { dg-prune-output {using 'vector_length \(32\)', ignoring 1} }

program pr95550
  implicit none
  integer, parameter :: n = 32
  integer, allocatable :: a(:)
  integer :: i, j

  allocate(a(n))
  do j = 1, n
     a(j) = 3 * j
  end do

  !$acc parallel create(a) num_gangs(1) num_workers(1) vector_length(1)
  !$acc loop seq private(a)
  do i = 1, n
     a(i) = 9 * i
  end do
  !$acc end parallel

  ! Host copy of 'a' must be untouched: create(...) does not copy back.
  do j = 1, n
     if (a(j) /= 3 * j) then
        write(0,*) "host a corrupted after parallel-create-private: j=", j, " got=", a(j)
        stop 21
     end if
  end do

  !$acc parallel create(a) num_gangs(4) num_workers(4) vector_length(1)
  !$acc loop worker private(a)
  do i = 1, n
     a(i) = 9 * i
  end do
  !$acc end parallel

  do j = 1, n
     if (a(j) /= 3 * j) stop 22
  end do

  !$acc parallel create(a) num_gangs(1) num_workers(1) vector_length(32)
  !$acc loop vector private(a)
  do i = 1, n
     a(i) = 9 * i
  end do
  !$acc end parallel

  do j = 1, n
     if (a(j) /= 3 * j) stop 23
  end do

  !$acc parallel create(a)
  !$acc loop gang private(a)
  do i = 1, n
     a(i) = 9 * i
  end do
  !$acc end parallel

  do j = 1, n
     if (a(j) /= 3 * j) stop 24
  end do

  !$acc kernels create(a)
  !$acc loop private(a)
  do i = 1, n
     a(i) = 9 * i
  end do
  !$acc end kernels

  do j = 1, n
     if (a(j) /= 3 * j) stop 25
  end do

  deallocate(a)
end program pr95550
