#!/usr/bin/env bash
set -euo pipefail

prefix="/opt/gcc16"

cat > /tmp/openacc_nvptx_smoke.f90 <<'EOF'
program openacc_nvptx_smoke
  use, intrinsic :: iso_fortran_env, only: dp => real64
  implicit none

  integer :: i
  integer, parameter :: n = 1000000
  real(dp), allocatable :: a(:)

  allocate(a(n))
  a = 0.0_dp

  !$acc parallel loop copy(a)
  do i = 1, n
    a(i) = real(i, dp) * 2.0_dp
  end do
  !$acc end parallel loop

  if (abs(a(1) - 2.0_dp) > 0.0_dp) stop 1
  if (abs(a(n) - real(n, dp) * 2.0_dp) > 0.0_dp) stop 2
end program
EOF

set -o pipefail

"${prefix}/bin/gfortran" -O2 -fopenacc -foffload=nvptx-none \
  /tmp/openacc_nvptx_smoke.f90 -o /tmp/openacc_nvptx_smoke 2>&1 | \
  tee /tmp/openacc_nvptx_smoke_build_$(date +%F).log

LD_LIBRARY_PATH="${prefix}/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}" \
  GOMP_DEBUG=1 \
  /tmp/openacc_nvptx_smoke 2>&1 | \
  tee /tmp/openacc_nvptx_smoke_run_$(date +%F).log
