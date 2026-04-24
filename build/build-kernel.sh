#!/usr/bin/env bash
set -euo pipefail
: "${KERNEL_DIR:=/work/linux}"
: "${OUT:=/work/out-riscv}"
: "${ARTIFACTS:=/artifacts/local/$(date -u +%Y%m%d-%H%M%S)}"
: "${ARCH:=riscv}"
: "${CROSS_COMPILE:=riscv64-linux-gnu-}"
mkdir -p "$OUT" "$ARTIFACTS"
cd "$KERNEL_DIR"
make O="$OUT" ARCH="$ARCH" CROSS_COMPILE="$CROSS_COMPILE" defconfig
make O="$OUT" ARCH="$ARCH" CROSS_COMPILE="$CROSS_COMPILE" -j"$(nproc)" Image dtbs modules
cp "$OUT/arch/riscv/boot/Image" "$ARTIFACTS/"
find "$OUT/arch/riscv/boot/dts" -name '*.dtb' -exec cp --parents {} "$ARTIFACTS/" \;
make O="$OUT" ARCH="$ARCH" CROSS_COMPILE="$CROSS_COMPILE" INSTALL_MOD_PATH="$ARTIFACTS/modules" modules_install
(cd "$ARTIFACTS" && tar -cJf modules.tar.xz modules && rm -rf modules)
echo "Artifacts em: $ARTIFACTS"
