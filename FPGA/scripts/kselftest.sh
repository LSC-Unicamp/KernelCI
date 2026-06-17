make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- TARGETS="size timers" kselftest-install

cd tools/testing/selftests/kselftest_install
tar -czvf kselftest.tar.gz *
sudo cp kselftest.tar.gz /srv/tftp/
sudo chmod 644 /srv/tftp/kselftest.tar.gz

mount -t debugfs none /sys/kernel/debug
cd /tmp

tftp -g -r kselftest.tar.gz 192.168.0.193
tar -xzvf kselftest.tar.gz