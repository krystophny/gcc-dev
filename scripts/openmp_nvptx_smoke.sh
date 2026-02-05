#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
prefix="${root_dir}/gcc-offload-build/install"

log_path="/tmp/openmp_nvptx_smoke_$(date +%F).log"

tmp_dir="$(mktemp -d /tmp/openmp_nvptx_smoke.XXXXXX)"
trap 'rm -rf "${tmp_dir}"' EXIT

cat >"${tmp_dir}/omp_target_smoke.f90" <<'EOF'
program omp_target_smoke
  integer :: i
  real :: a(1024)
  a = 1.0
  !$omp target teams distribute parallel do
  do i = 1, size(a)
    a(i) = a(i) + 1.0
  end do
  !$omp end target teams distribute parallel do
  print *, a(1)
end program omp_target_smoke
EOF

{
  echo "==== $(date -Is) ===="
  echo "compiler: ${prefix}/bin/gfortran"
  echo "tmp_dir: ${tmp_dir}"
  echo
  "${prefix}/bin/gfortran" -O2 -fopenmp "${tmp_dir}/omp_target_smoke.f90" \
    -o "${tmp_dir}/omp_target_smoke.out"
  echo
  echo "Run (mandatory offload)"
  LD_LIBRARY_PATH="${prefix}/lib64" OMP_TARGET_OFFLOAD=MANDATORY \
    "${tmp_dir}/omp_target_smoke.out"
} 2>&1 | tee "${log_path}"

if command -v rg >/dev/null 2>&1; then
  match_cmd=(rg -n '^[[:space:]]*2\.0' "${log_path}")
else
  match_cmd=(grep -nE '^[[:space:]]*2\.0' "${log_path}")
fi

if ! "${match_cmd[@]}" >/dev/null; then
  echo "Smoke test failed: expected output 2.0 in ${log_path}" >&2
  exit 1
fi

echo "OpenMP NVPTX smoke OK: ${log_path}"
