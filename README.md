# Kernel CI RISC-V Lab project


## How to build rootfs image

```bash
cd rootfs_dir
sudo su
find . | cpio -H newc -o | gzip > ../initramfs.cpio.gz
```

## How to build kernel image

```bash
cd kernel_dir
export ARCH=riscv export 
CROSS_COMPILE=riscv64-linux-gnu- 
make k1_defconfig
```

Add rootfs image to kernel image in make menuconfig

```bash
make menuconfig
```

Then build kernel image

```bash
LOCALVERSION="" make -j$(nproc) Image.gz dtbs modules
```

## How to generate itb image

```bash
cd /srv/tftp
mkimage -f in.its out.itb
```