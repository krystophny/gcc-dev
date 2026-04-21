! PR fortran/93554 -- per-gang independence of whole-allocatable privates.
!
! Whole allocatable array marked private on a gang-partitioned
! !$acc parallel loop with num_gangs(4).  Each iteration populates
! its per-gang private buf, overwrites it, and reads the final
! contents back.  A miscompile that lets the relaxed CFG leak
! private storage between iterations on the same gang -- or across
! gangs -- scrambles the checksum.  The test also forces the
! per-gang finaliser to free buf at region exit (same code path as
! PR107227 / PR95550 at runtime).
!
! Kept gang-only deliberately: worker- and vector-level private for
! whole allocatables is a separate GCC/NVPTX implementation question
! unrelated to r16-8571.

! { dg-do run }

program pr93554_private_independence
  implicit none
  integer, parameter :: n = 128, m = 16
  integer :: res(n), expect(n), j, k
  integer, allocatable :: buf(:)

  allocate(buf(m))

  do j = 1, n
     expect(j) = 2*(m*m*j + m*(m + 1)/2)
  end do

  res = -1

  !$acc parallel loop gang private(buf) copy(res) num_gangs(4)
  do j = 1, n
     do k = 1, m
        buf(k) = j*m + k
     end do
     do k = 1, m
        buf(k) = 2*buf(k)
     end do
     res(j) = 0
     do k = 1, m
        res(j) = res(j) + buf(k)
     end do
  end do
  !$acc end parallel loop

  do j = 1, n
     if (res(j) /= expect(j)) stop 2
  end do

  deallocate(buf)
end program pr93554_private_independence
