import subprocess
import os

def finalize_deploy(rootfs_path="/srv/nfs/visionfive-rootfs", tftp_path="/srv/tftp"):
    arch = "riscv"
    cross_compile = "riscv64-linux-gnu-"
    kernel_version = "7.1.0-rc3-00362-g6916d5703ddf" # ISSO TEM Q MUDAR PRA CADA UM // THIS HAS TO CHANGE FOR EACH IMPLEMENTATION

    print("nfs install...")
    subprocess.run(f"sudo make ARCH={arch} CROSS_COMPILE={cross_compile} "
                   f"INSTALL_MOD_PATH={rootfs_path} modules_install", shell=True, check=True)

    print("initramfs config...")
    chroot_cmds = [
        "apt update",
        "apt install -y initramfs-tools klibc-utils",
        "sed -i 's/BOOT=local/BOOT=nfs/' /etc/initramfs-tools/initramfs.conf",
        "echo 'dwmac-starfive\nmotorcomm\nstmmac-platform\nstmmac' >> /etc/initramfs-tools/modules",
        f"update-initramfs -c -k {kernel_version}"
    ]
    
    for cmd in chroot_cmds:
        subprocess.run(f"sudo chroot {rootfs_path} /bin/bash -c \"{cmd}\"", shell=True, check=True)

    print("Copy to TFTP...")
    dtb_file = "arch/riscv/boot/dts/starfive/jh7110-starfive-visionfive-2-v1.3b.dtb"
    initrd_src = f"{rootfs_path}/boot/initrd.img-{kernel_version}"

    subprocess.run(f"sudo cp arch/riscv/boot/Image {tftp_path}/", shell=True, check=True)
    subprocess.run(f"sudo cp {dtb_file} {tftp_path}/", shell=True, check=True)
    subprocess.run(f"sudo cp {initrd_src} {tftp_path}/initrd.img", shell=True, check=True)

if __name__ == "__main__":
    finalize_deploy()
