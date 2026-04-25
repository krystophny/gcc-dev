#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

prefix="${root_dir}/gcc-offload-build/install"
build_root="${root_dir}/gcc-offload-build"
gcc_src="${root_dir}/gcc"

newlib_repo="${root_dir}/third_party/newlib-cygwin"
nvptx_tools_repo="${root_dir}/third_party/nvptx-tools"

sm_default="sm_89"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--clean] [--no-smoke] [--sm-default <sm_XX>]

Builds and installs:
  - nvptx-tools into ${prefix}/nvptx
  - GCC nvptx accelerator into ${prefix} (includes nvptx libgfortran)
  - Host GCC into ${prefix} with nvptx offload enabled

Notes:
  - Expects ${gcc_src} to be a GCC source checkout.
  - Clones third_party/newlib-cygwin and third_party/nvptx-tools if missing.
  - Uses an in-source symlink: ${gcc_src}/newlib -> third_party/newlib-cygwin/newlib
  - Logs are written under /tmp.

Options:
  --clean         Remove build directories under ${build_root} first.
  --no-smoke      Skip OpenACC/OpenMP offload smoke tests.
  --sm-default    Default nvptx arch for configure (default: ${sm_default}).
EOF
}

do_clean=0
do_smoke=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)
      do_clean=1
      shift
      ;;
    --no-smoke)
      do_smoke=0
      shift
      ;;
    --sm-default)
      sm_default="${2:?missing value for --sm-default}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "${gcc_src}" ]]; then
  echo "Missing GCC sources at ${gcc_src}" >&2
  exit 1
fi

mkdir -p "${root_dir}/third_party"
mkdir -p "${build_root}"

log() {
  local tag="$1"
  shift
  "$@" 2>&1 | tee "/tmp/${tag}_$(date +%F).log"
}

if [[ ! -d "${newlib_repo}/.git" ]]; then
  log gcc16_clone_newlib_cygwin \
    git clone --depth 1 git://sourceware.org/git/newlib-cygwin.git \
      "${newlib_repo}"
fi

if [[ ! -d "${nvptx_tools_repo}/.git" ]]; then
  log gcc16_clone_nvptx_tools \
    git clone --depth 1 git@github.com:SourceryTools/nvptx-tools.git \
      "${nvptx_tools_repo}"
fi

if [[ ! -x "${gcc_src}/contrib/download_prerequisites" ]]; then
  echo "Missing ${gcc_src}/contrib/download_prerequisites" >&2
  exit 1
fi

(cd "${gcc_src}" && log gcc16_download_prerequisites ./contrib/download_prerequisites)

rm -f "${gcc_src}/newlib"
ln -s "../third_party/newlib-cygwin/newlib" "${gcc_src}/newlib"

(cd "${nvptx_tools_repo}" && log gcc16_nvptx_tools_configure ./configure --prefix="${prefix}/nvptx")
(cd "${nvptx_tools_repo}" && log gcc16_nvptx_tools_make make -j"$(nproc)")
(cd "${nvptx_tools_repo}" && log gcc16_nvptx_tools_install make install)

mkdir -p "${prefix}/nvptx-none"
ln -snf "${prefix}/nvptx/nvptx-none/bin" "${prefix}/nvptx-none/bin"

accel_build="${build_root}/accel-nvptx"
host_build="${build_root}/host-gcc16"

if [[ "${do_clean}" == "1" ]]; then
  rm -rf "${accel_build}" "${host_build}"
fi

mkdir -p "${accel_build}" "${host_build}"

(cd "${accel_build}" && log gcc16_accel_nvptx_configure \
  ../../gcc/configure \
    --target=nvptx-none \
    --prefix="${prefix}" \
    --enable-as-accelerator-for=x86_64-pc-linux-gnu \
    --enable-languages=c,c++,fortran,lto \
    --disable-nls \
    --enable-checking=release \
    --with-newlib \
    --disable-sjlj-exceptions \
    --enable-newlib-io-long-long \
    --with-build-time-tools="${prefix}/nvptx/nvptx-none/bin" \
    --with-arch="${sm_default}" \
    --with-multilib-list="${sm_default}" \
    CFLAGS='-O2 -pipe' \
    CXXFLAGS='-O2 -pipe')

(cd "${accel_build}" && log gcc16_accel_nvptx_make make -j"$(nproc)")
(cd "${accel_build}" && log gcc16_accel_nvptx_install make install)

(cd "${host_build}" && log gcc16_host_configure \
  ../../gcc/configure \
    --prefix="${prefix}" \
    --enable-languages=c,c++,fortran,lto \
    --disable-multilib \
    --disable-nls \
    --enable-checking=release \
    --disable-bootstrap \
    --enable-offload-targets=nvptx-none \
    CFLAGS='-O2 -pipe' \
    CXXFLAGS='-O2 -pipe')

(cd "${host_build}" && log gcc16_host_make make -j"$(nproc)")
(cd "${host_build}" && log gcc16_host_install make install)

if [[ "${do_smoke}" == "1" ]]; then
  "${root_dir}/scripts/openacc-nvptx-smoke.sh"
  "${root_dir}/scripts/openmp-nvptx-smoke.sh"
fi
