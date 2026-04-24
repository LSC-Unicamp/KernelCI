# KernelCI RISC-V lab compose skeleton

- `dhcp-tftp/dnsmasq.conf`: interface, range, MACs e IPs.
- `dhcp-tftp/tftp/boards/*/*.cmd`: URLs, endereços de memória U-Boot, console e DTB.
- `ser2net/ser2net.yaml`: `/dev/ttyUSBx` e portas.
- `power/*.sh`: comandos reais de power control.
- `lava/devices/*.jinja2`: connection e hard_reset.

Subir:
```bash
docker compose up -d
```

Build local:
```bash
mkdir -p work
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git work/linux
docker compose exec builder build-kernel.sh
ln -sfn local/<BUILD_DIR> artifacts/current
```

LAVA UI:
- http://HOST:8000

Artifacts:
- http://HOST:8080/artifacts/
