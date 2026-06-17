#!/bin/bash
 make CROSS_COMPILE=riscv64-unknown-linux-gnu- PLATFORM=generic \
     FW_FDT_PATH=/eda/linux_on_fpga/dtbs/nexys4ddr.dtb \
     FW_JUMP_FDT_ADDR=0x82400000