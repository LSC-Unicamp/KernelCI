import json
import argparse
import os

def generate_dts(json_path, output_dts, output_boot_json):
    with open(json_path, 'r') as f:
        data = json.load(f)

    bases = data.get("csr_bases", {})
    constants = data.get("constants", {})
    memories = data.get("memories", {})

    clk_freq = constants.get("config_clock_frequency", 100000000)
    cpu_count = constants.get("config_cpu_count", 1)
    
    isa = "rv64imafdcZicsr_Zifencei_Zihpm_Xrocket"
    mmu = constants.get("config_cpu_mmu", "sv39")
    
    uart_base = bases.get("uart", 0)
    timer_base = bases.get("timer0", 0)
    ethmac_base = bases.get("ethmac", 0)
    ethphy_base = bases.get("ethphy", 0)
    spisdcard_base = bases.get("spisdcard", 0)
    ctrl_base = bases.get("ctrl", 0)
    
    main_ram_base = memories.get("main_ram", {}).get("base", 0x80000000)
    main_ram_size = memories.get("main_ram", {}).get("size", 0x40000000)
    clint_base = memories.get("clint", {}).get("base", 0x2000000)
    clint_size = memories.get("clint", {}).get("size", 0x10000)
    plic_base = memories.get("plic", {}).get("base", 0xc000000)
    plic_size = memories.get("plic", {}).get("size", 0x4000000)
    ethmac_buf = memories.get("ethmac", {}).get("base", 0x30000000)

    uart_irq = constants.get("uart_interrupt", 0) + 1
    timer_irq = constants.get("timer0_interrupt", 1) + 1
    ethmac_irq = constants.get("ethmac_interrupt", 2) + 1

    ident = constants.get("config_identifier", "Open Source SDR LAB")
    model_name = ident.split(" 202")[0] + " Rocket"

    # ==========================================
    # CÁLCULO DE ENDEREÇOS DE BOOT (OFFSETS)
    # ==========================================
    opensbi_addr = main_ram_base
    kernel_addr  = main_ram_base + 0x00200000
    initrd_addr  = main_ram_base + 0x02000000
    dtb_addr     = main_ram_base + 0x02400000

    boot_config = {
        "fw_jump.bin": f"0x{opensbi_addr:08x}",
        "Image": f"0x{kernel_addr:08x}",
        "rootfs.cpio.gz": f"0x{initrd_addr:08x}"
    }

    # Salva o boot.json
    with open(output_boot_json, "w") as f:
        json.dump(boot_config, f, indent=4)

    # ==========================================
    # GERAÇÃO DA DEVICE TREE (DTS)
    # ==========================================
    lines = [
        "/dts-v1/;",
        "",
        "/ {",
        "\t#address-cells = <1>;",
        "\t#size-cells = <1>;",
        f'\tcompatible = "freechips,rocketchip-unknown-dev";',
        f'\tmodel = "{model_name}";',
        "\tchosen {",
        f'\t\tbootargs = "console=liteuart earlycon=liteuart,0x{uart_base:x} swiotlb=noforce rootwait root=/dev/ram0";',
        f"\t\tlinux,initrd-start = <0x{initrd_addr:08x}>;",
        f"\t\tlinux,initrd-end   = <0x{initrd_addr + 0x800000:08x}>; /* Ajuste manual depois se o cpio for maior que 8MB */",
        "\t};",
        "\tL13: cpus {",
        "\t\t#address-cells = <1>;",
        "\t\t#size-cells = <0>;",
        "\t\ttimebase-frequency = <1000000>;"
    ]

    clint_irqs = []
    plic_irqs = []
    debug_irqs = []

    for i in range(cpu_count):
        l_intc = (i * 10) + 4  
        l_cpu = (i * 10) + 6
        
        lines.extend([
            f"\t\tL{l_cpu}: cpu@{i} {{",
            f"\t\t\tclock-frequency = <{clk_freq}>;",
            f'\t\t\tcompatible = "sifive,rocket0", "riscv";',
            f'\t\t\td-cache-block-size = <{constants.get("config_cpu_dcache_block_size", 64)}>;',
            f'\t\t\td-cache-sets = <{constants.get("config_cpu_dcache_ways", 64)}>;',
            f'\t\t\td-cache-size = <{constants.get("config_cpu_dcache_size", 16384)}>;',
            f'\t\t\td-tlb-sets = <{constants.get("config_cpu_dtlb_ways", 1)}>;',
            f'\t\t\td-tlb-size = <{constants.get("config_cpu_dtlb_size", 32)}>;',
            f'\t\t\tdevice_type = "cpu";',
            f'\t\t\thardware-exec-breakpoint-count = <1>;',
            f'\t\t\ti-cache-block-size = <{constants.get("config_cpu_icache_block_size", 64)}>;',
            f'\t\t\ti-cache-sets = <{constants.get("config_cpu_icache_ways", 64)}>;',
            f'\t\t\ti-cache-size = <{constants.get("config_cpu_icache_size", 16384)}>;',
            f'\t\t\ti-tlb-sets = <{constants.get("config_cpu_itlb_ways", 1)}>;',
            f'\t\t\ti-tlb-size = <{constants.get("config_cpu_itlb_size", 32)}>;',
            f'\t\t\tmmu-type = "riscv,{mmu}";',
            f"\t\t\tnext-level-cache = <&L8>;",
            f"\t\t\treg = <0x{i:x}>;",
            f'\t\t\triscv,isa = "{isa}";',
            f"\t\t\triscv,pmpgranularity = <4>;",
            f"\t\t\triscv,pmpregions = <8>;",
            f'\t\t\tstatus = "okay";',
            f"\t\t\ttlb-split;",
            f"\t\t\tL{l_intc}: interrupt-controller {{",
            f"\t\t\t\t#interrupt-cells = <1>;",
            f'\t\t\t\tcompatible = "riscv,cpu-intc";',
            f"\t\t\t\tinterrupt-controller;",
            f"\t\t\t}};",
            f"\t\t}};"
        ])
        clint_irqs.append(f"&L{l_intc} 3 &L{l_intc} 7")
        plic_irqs.append(f"&L{l_intc} 11 &L{l_intc} 9")
        debug_irqs.append(f"&L{l_intc} 0xFFFF")

    lines.extend([
        "\t};",
        f"\tL8: memory@{main_ram_base:x} {{",
        f'\t\tdevice_type = "memory";',
        f"\t\treg = <0x{main_ram_base:x} 0x{main_ram_size:x}>;",
        "\t};",
        "\tclocks {",
        "\t\tsys_clk: litex_sys_clk {",
        "\t\t\t#clock-cells = <0>;",
        f'\t\t\tcompatible = "fixed-clock";',
        f"\t\t\tclock-frequency = <{clk_freq}>;",
        "\t\t};",
        "\t};",
        "\tL12: soc {",
        "\t\t#address-cells = <1>;",
        "\t\t#size-cells = <1>;",
        f'\t\tcompatible = "freechips,rocketchip-unknown-soc", "simple-bus";',
        "\t\tranges;",
        f"\t\tL2: clint@{clint_base:x} {{",
        f'\t\t\tcompatible = "riscv,clint0";',
        f"\t\t\tinterrupts-extended = <{' '.join(clint_irqs)}>;",
        f"\t\t\treg = <0x{clint_base:x} 0x{clint_size:x}>;",
        f'\t\t\treg-names = "control";',
        "\t\t};",
        "\t\tL3: debug-controller@0 {",
        f'\t\t\tcompatible = "sifive,debug-013", "riscv,debug-013";',
        f"\t\t\tinterrupts-extended = <{' '.join(debug_irqs)}>;",
        "\t\t\treg = <0x0 0x1000>;",
        f'\t\t\treg-names = "control";',
        "\t\t};",
        "\t\tL0: error-device@3000 {",
        f'\t\t\tcompatible = "sifive,error0";',
        "\t\t\treg = <0x3000 0x1000>;",
        "\t\t};",
        "\t\tL7: external-interrupts {",
        "\t\t\tinterrupt-parent = <&L1>;",
        "\t\t\tinterrupts = <1 2 3 4 5 6 7 8>;",
        "\t\t};",
        f"\t\tL1: interrupt-controller@{plic_base:x} {{",
        "\t\t\t#interrupt-cells = <1>;",
        f'\t\t\tcompatible = "riscv,plic0";',
        "\t\t\tinterrupt-controller;",
        f"\t\t\tinterrupts-extended = <{' '.join(plic_irqs)}>;",
        f"\t\t\treg = <0x{plic_base:x} 0x{plic_size:x}>;",
        f'\t\t\treg-names = "control";',
        "\t\t\triscv,max-priority = <7>;",
        "\t\t\triscv,ndev = <8>;",
        "\t\t};",
        "\t\tL10: rom@10000 {",
        f'\t\t\tcompatible = "sifive,rom0";',
        "\t\t\treg = <0x10000 0x10000>;",
        f'\t\t\treg-names = "mem";',
        "\t\t};",
        f"\t\tsoc_ctrl0: soc_controller@{ctrl_base:x} {{",
        f'\t\t\tcompatible = "litex,soc-controller";',
        f"\t\t\treg = <0x{ctrl_base:x} 0xc>;",
        "\t\t};",
        f"\t\tliteuart0: serial@{uart_base:x} {{",
        f'\t\t\tcompatible = "litex,liteuart";',
        f"\t\t\treg = <0x{uart_base:x} 0x100>;",
        "\t\t\tinterrupt-parent = <&L1>;",
        f"\t\t\tinterrupts = <{uart_irq}>;",
        "\t\t};"
    ])

    if ethmac_base:
        lines.extend([
            f"\t\tmac0: mac@{ethmac_base:x} {{",
            f'\t\t\tcompatible = "litex,liteeth";',
            f"\t\t\treg = <0x{ethmac_base:x} 0x100>,",
            f"\t\t\t\t<0x{ethphy_base:x} 0x100>,",
            f"\t\t\t\t<0x{ethmac_buf:x} 0x2000>;",
            f'\t\t\treg-names = "mac", "mdio", "buffer";',
            f'\t\t\tlitex,rx-slots = <{constants.get("ethmac_rx_slots", 2)}>;',
            f'\t\t\tlitex,tx-slots = <{constants.get("ethmac_tx_slots", 2)}>;',
            f'\t\t\tlitex,slot-size = <0x{constants.get("ethmac_slot_size", 2048):x}>;',
            "\t\t\tinterrupt-parent = <&L1>;",
            f"\t\t\tinterrupts = <{ethmac_irq}>;",
            "\t\t};"
        ])

    if spisdcard_base:
        lines.extend([
            f"\t\tspisdcard0: spisdcard@{spisdcard_base:x} {{",
            f'\t\t\tcompatible = "litex,spisdcard";',
            f"\t\t\treg = <0x{spisdcard_base:x} 0x100>;",
            f'\t\t\treg-names = "core";',
            "\t\t\tclocks = <&sys_clk>;",
            "\t\t};"
        ])

    if timer_base:
        lines.extend([
            f"\t\ttimer@{timer_base:x} {{",
            f'\t\t\tcompatible = "litex,timer";',
            f"\t\t\treg = <0x{timer_base:x} 0x20>;",
            "\t\t\tclocks = <&sys_clk>;",
            "\t\t\tinterrupt-parent = <&L1>;",
            f"\t\t\tinterrupts = <{timer_irq}>;",
            "\t\t};"
        ])

    lines.extend([
        "\t};",
        "};"
    ])

    with open(output_dts, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Extrai o caminho absoluto do .dtb que será gerado a partir do .dts
    dtb_path = os.path.abspath(output_dts.replace('.dts', '.dtb'))

    print(f"\nDevice Tree gerada com sucesso em: {output_dts}")
    print(f"Configuração de boot gerada em:    {output_boot_json}\n")
    
    print("Sugestão de comando para compilar o OpenSBI:")
    print(f"make CROSS_COMPILE=riscv64-unknown-linux-gnu- PLATFORM=generic \\")
    print(f"     FW_FDT_PATH={dtb_path} \\")
    print(f"     FW_JUMP_FDT_ADDR=0x{dtb_addr:08x}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera system.dts e boot.json a partir do csr.json do LiteX.")
    parser.add_argument("--json", required=True, help="Caminho para o csr.json")
    parser.add_argument("--dts", default="system.dts", help="Caminho de saída para o system.dts")
    parser.add_argument("--boot-json", default="boot.json", help="Caminho de saída para o boot.json")
    args = parser.parse_args()
    
    generate_dts(args.json, args.dts, args.boot_json)
