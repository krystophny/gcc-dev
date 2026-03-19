#!/usr/bin/env bash
set -euo pipefail

# Hetzner Cloud aarch64 VM management for GCC testing.
# Requires: hcloud CLI, HCLOUD_TOKEN and SSH_AUTH_SOCK in environment.
#
# Usage: source ~/.secrets && scripts/hcloud-vm.sh <command>

VM_NAME="${HCLOUD_VM_NAME:-gcc-aarch64-test}"
VM_TYPE="${HCLOUD_VM_TYPE:-cax41}"    # 16 ARM cores, 32 GB RAM
VM_IMAGE="ubuntu-24.04"
VM_LOCATION="${HCLOUD_VM_LOCATION:-nbg1}"  # Nuremberg; override with hel1 if unavailable
SSH_KEY_NAME="ert-workstation"

# Ensure SSH agent is available for forwarding
: "${SSH_AUTH_SOCK:=${XDG_RUNTIME_DIR}/ssh-agent.socket}"
export SSH_AUTH_SOCK

usage() {
    cat <<EOF
Usage: $(basename "$0") <command> [args]

Commands:
  create             Create and provision the aarch64 VM
  destroy            Destroy the VM (immediate)
  ssh [cmd]          SSH into VM (with agent forwarding)
  ip                 Print VM IPv4 address
  status             Show VM status
  setup              Run provisioning on existing VM
  clone [commit]     Clone GCC at commit (default: master HEAD)
  bootstrap-lto      Configure + start LTO bootstrap in tmux
  build              Configure + build (debug, no bootstrap)
  test <name.f90>    Run a single gfortran dejagnu test
  check              Run full check-gfortran in tmux
  tail               Tail the bootstrap/check log

Environment:
  HCLOUD_TOKEN       Hetzner API token (source ~/.secrets)
  SSH_AUTH_SOCK      SSH agent socket (auto-detected from XDG_RUNTIME_DIR)
  HCLOUD_VM_NAME     Override VM name (default: gcc-aarch64-test)
  HCLOUD_VM_TYPE     Override VM type (default: cax41)
EOF
}

vm_ip() {
    hcloud server ip "$VM_NAME" 2>/dev/null
}

vm_ssh() {
    local ip
    ip="$(vm_ip)"
    ssh -A root@"${ip}" "$@"
}

wait_ssh() {
    local ip="$1"
    echo "Waiting for SSH on ${ip}..."
    for _ in $(seq 1 30); do
        if ssh -A -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
               -o BatchMode=yes root@"${ip}" true 2>/dev/null; then
            echo "SSH ready."
            return 0
        fi
        sleep 2
    done
    echo "ERROR: SSH not ready after 60s" >&2
    return 1
}

update_known_hosts() {
    local ip="$1"
    ssh-keygen -R "$ip" 2>/dev/null || true
    ssh-keyscan -t ed25519 "$ip" >> ~/.ssh/known_hosts 2>/dev/null
}

cmd_create() {
    if hcloud server describe "$VM_NAME" &>/dev/null; then
        echo "VM '$VM_NAME' already exists at $(vm_ip)"
        return 0
    fi

    echo "Creating ${VM_TYPE} (${VM_IMAGE}) in ${VM_LOCATION}..."
    hcloud server create \
        --name "$VM_NAME" \
        --type "$VM_TYPE" \
        --image "$VM_IMAGE" \
        --location "$VM_LOCATION" \
        --ssh-key "$SSH_KEY_NAME"

    local ip
    ip="$(vm_ip)"
    wait_ssh "$ip"
    update_known_hosts "$ip"
    cmd_setup
    echo "VM ready at ${ip}"
}

cmd_setup() {
    echo "Provisioning $(vm_ip)..."
    vm_ssh bash <<'PROVISION'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -qq \
    build-essential gcc g++ gfortran \
    libgmp-dev libmpfr-dev libmpc-dev \
    flex bison texinfo \
    git dejagnu \
    tmux htop

# Add GitHub to known_hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null

mkdir -p /root/gcc-dev
echo "Provisioning complete."
PROVISION
}

cmd_clone() {
    local commit="${1:-}"
    echo "Cloning GCC on $(vm_ip)..."
    vm_ssh bash <<CLONE
set -euo pipefail
cd /root/gcc-dev

if [ ! -d gcc ]; then
    git clone --depth=50 git://gcc.gnu.org/git/gcc.git gcc 2>&1 | tail -3
fi

cd gcc
git fetch origin master --depth=100
${commit:+git checkout ${commit}}
${commit:-git checkout FETCH_HEAD}
git log --oneline -3
CLONE
}

cmd_bootstrap_lto() {
    echo "Starting LTO bootstrap on $(vm_ip) in tmux..."
    vm_ssh bash <<'BOOTSTRAP'
set -euo pipefail
cd /root/gcc-dev

mkdir -p gcc-build-lto && cd gcc-build-lto
if [ ! -f Makefile ]; then
    ../gcc/configure \
        --enable-languages=fortran,c,c++,lto \
        --disable-multilib \
        --with-build-config=bootstrap-lto \
        --enable-valgrind-annotations \
        CFLAGS='-O2' CXXFLAGS='-O2' 2>&1 | tail -5
fi

tmux kill-session -t lto-build 2>/dev/null || true
tmux new-session -d -s lto-build \
    'cd /root/gcc-dev/gcc-build-lto && make -j$(nproc) bootstrap 2>&1 | tee /tmp/lto-bootstrap.log; echo "EXIT: $?" >> /tmp/lto-bootstrap.log'
echo "LTO bootstrap running in tmux session 'lto-build'."
echo "Monitor: scripts/hcloud-vm.sh tail"
BOOTSTRAP
}

cmd_build() {
    echo "Building GCC (debug) on $(vm_ip)..."
    vm_ssh bash <<'BUILD'
set -euo pipefail
cd /root/gcc-dev

mkdir -p gcc-build && cd gcc-build
if [ ! -f Makefile ]; then
    ../gcc/configure \
        --enable-languages=fortran \
        --disable-multilib \
        --disable-bootstrap \
        --enable-valgrind-annotations \
        CFLAGS='-Og -g' CXXFLAGS='-Og -g'
fi

echo "Building with $(nproc) cores..."
make -j$(nproc) 2>&1 | tail -5
echo "Build complete."
BUILD
}

cmd_test() {
    local test_name="${1:?Usage: $(basename "$0") test <test-name.f90>}"
    echo "Running test ${test_name} on $(vm_ip)..."
    vm_ssh bash <<TEST
set -euo pipefail

# Find the build directory (LTO bootstrap or debug)
if [ -d /root/gcc-dev/gcc-build-lto/gcc ]; then
    cd /root/gcc-dev/gcc-build-lto/gcc
elif [ -d /root/gcc-dev/gcc-build/gcc ]; then
    cd /root/gcc-dev/gcc-build/gcc
else
    echo "ERROR: No build directory found" >&2
    exit 1
fi

make check-gfortran RUNTESTFLAGS="dg.exp=${test_name}" 2>&1 | tail -20
echo "---"
grep -E "^(PASS|FAIL|XFAIL|XPASS|UNSUPPORTED):" \
    testsuite/gfortran/gfortran.sum 2>/dev/null | tail -20 || true
TEST
}

cmd_check() {
    echo "Running full check-gfortran on $(vm_ip) in tmux..."
    vm_ssh bash <<'CHECK'
set -euo pipefail

if [ -d /root/gcc-dev/gcc-build-lto/gcc ]; then
    cd /root/gcc-dev/gcc-build-lto/gcc
elif [ -d /root/gcc-dev/gcc-build/gcc ]; then
    cd /root/gcc-dev/gcc-build/gcc
else
    echo "ERROR: No build directory found" >&2
    exit 1
fi

tmux kill-session -t gcc-test 2>/dev/null || true
tmux new-session -d -s gcc-test \
    "make -j$(nproc) -k check-gfortran > /tmp/check-gfortran.log 2>&1; echo DONE"
echo "Test running in tmux session 'gcc-test'."
echo "Monitor: scripts/hcloud-vm.sh tail"
CHECK
}

cmd_tail() {
    vm_ssh 'tail -20 /tmp/lto-bootstrap.log 2>/dev/null || tail -20 /tmp/check-gfortran.log 2>/dev/null || echo "No log found."'
}

cmd_ssh() {
    if [ $# -gt 0 ]; then
        vm_ssh "$@"
    else
        vm_ssh
    fi
}

cmd_ip() {
    vm_ip
}

cmd_status() {
    hcloud server describe "$VM_NAME" 2>/dev/null || echo "No VM found."
}

cmd_destroy() {
    local ip
    ip="$(vm_ip 2>/dev/null)" || true
    echo "Destroying VM '${VM_NAME}'..."
    hcloud server delete "$VM_NAME" 2>/dev/null && echo "Destroyed." || echo "Not found."
    [ -n "${ip:-}" ] && ssh-keygen -R "$ip" 2>/dev/null || true
}

case "${1:-}" in
    create)        cmd_create ;;
    setup)         cmd_setup ;;
    clone)         shift; cmd_clone "${@:-}" ;;
    bootstrap-lto) cmd_bootstrap_lto ;;
    build)         cmd_build ;;
    test)          shift; cmd_test "$@" ;;
    check)         cmd_check ;;
    tail)          cmd_tail ;;
    ssh)           shift; cmd_ssh "$@" ;;
    ip)            cmd_ip ;;
    status)        cmd_status ;;
    destroy)       cmd_destroy ;;
    *)             usage; exit 1 ;;
esac
