import subprocess
import multiprocessing

def configure_and_make():
    arch = "riscv"
    cross_compile = "riscv64-linux-gnu-"
    nproc = multiprocessing.cpu_count()

    # Módulos específicos para VisionFive 2 JH7110
    configs = [
        "CONFIG_NET_VENDOR_STMICRO", "CONFIG_STMMAC_ETH", "CONFIG_STMMAC_PLATFORM",
        "CONFIG_DWMAC_STARFIVE", "CONFIG_MOTORCOMM_PHY", "CONFIG_CLK_STARFIVE_JH7110_SYS",
        "CONFIG_CLK_STARFIVE_JH7110_AON", "CONFIG_CLK_STARFIVE_JH7110_STG",
        "CONFIG_RESET_STARFIVE_JH7110", "CONFIG_PINCTRL_STARFIVE_JH7110"
    ]

    print("Configurando o Kernel...")
    # Gera o .config inicial
    subprocess.run(f"make ARCH={arch} CROSS_COMPILE={cross_compile} olddefconfig", shell=True, check=True)

    # Habilita as flags via script de config do kernel
    for cfg in configs:
        subprocess.run(f"./scripts/config --enable {cfg}", shell=True, check=True)

    print(f"Iniciando compilação com {nproc} threads...")
    subprocess.run(f"make ARCH={arch} CROSS_COMPILE={cross_compile} -j{nproc} Image", shell=True, check=True)
    subprocess.run(f"make ARCH={arch} CROSS_COMPILE={cross_compile} -j{nproc} dtbs", shell=True, check=True)

if __name__ == "__main__":
    configure_and_make()
