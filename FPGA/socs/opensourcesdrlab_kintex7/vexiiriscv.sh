python opensourcesdrlab_kintex7.py --build \
    --cpu-type=vexiiriscv  --cpu-variant=debian --cpu-count=2  \
    --sys-clk-freq 100e6 --with-ethernet --with-spi-sdcard --with-video-terminal --eth-dynamic-ip --remote-ip 192.168.0.1