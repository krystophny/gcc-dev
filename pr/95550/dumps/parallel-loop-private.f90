! PR middle-end/95550
! Reproducer by tetra2005@gmail.com, 2021-09-28 (Bugzilla comment #2).
! Compile with: gfortran -ffree-form -ffree-line-length-none -O2 \
!     -fopenacc -c parallel-loop-private.f90
!
! Pre-fix: ICE in expand_oacc_for.
! Post-fix: compiles cleanly.

  SUBROUTINE FOO()
    INTEGER :: I
    COMPLEX(8), ALLOCATABLE :: GWORK(:)
    ALLOCATE(GWORK(512))
  !$ACC PARALLEL LOOP PRIVATE(GWORK)
    DO I = 1,512
      GWORK(I) = 0
    ENDDO
  END SUBROUTINE
