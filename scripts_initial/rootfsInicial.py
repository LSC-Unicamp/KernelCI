import subprocess
import os

def run_command(command):
    print(f"Exec: {command}")
    subprocess.run(command, shell=True, check=True)

def setup_rootfs(target_dir="/srv/nfs/visionfive-rootfs"):
    run_command("sudo apt update && sudo apt install -y qemu-user-static binfmt-support debootstrap")

    if not os.path.exists(target_dir):
        run_command(f"sudo mkdir -p {target_dir}")

    print("Debootstrap stage...")
    run_command(f"sudo debootstrap --arch=riscv64 --foreign trixie {target_dir}")

    run_command(f"sudo cp /usr/bin/qemu-riscv64-static {target_dir}/usr/bin/")

    print("Debootstrap final...")
    run_command(f"sudo chroot {target_dir} /debootstrap/debootstrap --second-stage")

if __name__ == "__main__":
    setup_rootfs()
