import os
import sys
import yaml
import json
import argparse
import subprocess
import shutil

# Definições de caminhos da infraestrutura
LITEX_VENV_PYTHON = os.environ.get("LITEX_VENV_PYTHON", "/eda/litex/litex_env/bin/python")
LITEX_TARGETS_DIR = os.environ.get("LITEX_TARGETS_DIR", "/eda/litex/litex-boards/litex_boards/targets")

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"Aviso: Arquivo de configuração '{config_path}' não encontrado. Usando defaults.")
        return {}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}

def run_command(cmd: list, cwd: str = None) -> None:
    cmd_str = " ".join(cmd)
    print(f"\nExecutando: {cmd_str}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"\nErro ao executar o comando. Código de saída: {e.returncode}")
        sys.exit(1)

def main(core: str, target: str, opensbi_path: str) -> None:
    core_dir = os.path.join(target, core)

    # Validações iniciais
    if not os.path.exists(target):
        print(f"Erro: Diretório do target '{target}' não existe.")
        sys.exit(1)
    if not os.path.exists(core_dir):
        print(f"Erro: Diretório do core '{core_dir}' não existe.")
        sys.exit(1)

    # 1. Carregar configurações (Target + Core)
    target_cfg_path = os.path.join(target, "target_config.yaml")
    core_cfg_path = os.path.join(core_dir, "core_config.yaml")

    target_cfg = load_config(target_cfg_path)
    core_cfg = load_config(core_cfg_path)

    if not target_cfg:
        print(f"Aviso: Nenhuma configuração de target ({target_cfg_path}) encontrada. Faltam parâmetros de hardware?")

    # 2. Localizar o script Python da placa
    target_script = os.path.join(LITEX_TARGETS_DIR, f"{target}.py")
    if not os.path.exists(target_script):
        # Fallback caso o script da placa esteja na pasta local do target em vez do diretório do LiteX
        target_script = os.path.join(target, f"{target}.py")
        if not os.path.exists(target_script):
            print(f"Erro: Script da placa '{target}.py' não encontrado em {LITEX_TARGETS_DIR} ou na pasta local.")
            sys.exit(1)

    # 3. Montar o comando do LiteX combinando as duas configs
    litex_cmd = [
        LITEX_VENV_PYTHON, target_script,
        "--build",
        f"--cpu-type={core_cfg.get('cpu_type', core)}",
        f"--cpu-variant={core_cfg.get('cpu_variant', 'standard')}",
        f"--cpu-count={str(core_cfg.get('cpu_count', 1))}"
    ]

    # Adiciona o clock definido no target
    if 'sys_clk_freq' in target_cfg:
        litex_cmd.append(f"--sys-clk-freq={str(target_cfg['sys_clk_freq'])}")

    # Adiciona as flags globais da placa (Ethernet, SDCard, IPs, etc)
    for flag in target_cfg.get('target_flags', []):
        litex_cmd.append(str(flag))

    # Adiciona flags específicas do core, se existirem
    for flag in core_cfg.get('core_flags', []):
        litex_cmd.append(str(flag))

    # 4. Executar o build do Hardware
    print(f"\n--- Iniciando Build do Hardware: {target} com {core} ---")
    run_command(litex_cmd)

    # 5. Localizar e mover os artefatos (CSRs)
    # O diretório padrão de build do LiteX costuma ser build/<target>/
    build_dir = os.path.join("build", target)
    csr_json_src = os.path.join(build_dir, "csr.json")
    csr_csv_src = os.path.join(build_dir, "csr.csv")

    if not os.path.exists(csr_json_src):
        print(f"\nErro: {csr_json_src} não encontrado após o build. O build falhou silenciosamente?")
        sys.exit(1)

    shutil.copy(csr_json_src, os.path.join(core_dir, "csr.json"))
    shutil.copy(csr_csv_src, os.path.join(core_dir, "csr.csv"))
    print(f"\nCSRs copiados para {core_dir}/")

    # 6. Gerar a Device Tree e boot.json (acionando dts_generator.py)
    print("\n--- Gerando Device Tree e boot.json ---")
    dts_out = os.path.join(core_dir, "system.dts")
    boot_json_out = os.path.join(core_dir, "boot.json")

    dts_gen_cmd = [
        sys.executable, "dts_generator.py",
        "--json", os.path.join(core_dir, "csr.json"),
        "--dts", dts_out,
        "--boot-json", boot_json_out
    ]
    run_command(dts_gen_cmd)

    # 7. Compilar o .dts para .dtb usando o utilitário dtc
    print("\n--- Compilando .dts para .dtb ---")
    dtb_out = os.path.join(core_dir, "system.dtb")
    dtc_cmd = [
        "dtc", "-I", "dts", "-O", "dtb", "-o", dtb_out, dts_out
    ]
    run_command(dtc_cmd)

    # 8. Tratar o OpenSBI
    try:
        with open(boot_json_out, 'r') as f:
            boot_data = json.load(f)
            # Pega o endereço base de onde o fw_jump deve pular (geralmente o endereço da Image do Kernel)
            dtb_addr = boot_data.get("Image", "0x80200000").replace("0x", "")
    except Exception:
        dtb_addr = "80200000"

    if opensbi_path and os.path.exists(opensbi_path):
        print(f"\n--- Compilando OpenSBI a partir de {opensbi_path} ---")
        opensbi_cmd = [
            "make",
            "CROSS_COMPILE=riscv64-unknown-linux-gnu-",
            "PLATFORM=generic",
            f"FW_FDT_PATH={os.path.abspath(dtb_out)}",
            f"FW_JUMP_FDT_ADDR=0x{dtb_addr}"
        ]
        run_command(opensbi_cmd, cwd=opensbi_path)
        
        # Copiar o binário gerado para a pasta do core
        fw_jump_src = os.path.join(opensbi_path, "build", "platform", "generic", "firmware", "fw_jump.bin")
        if os.path.exists(fw_jump_src):
            shutil.copy(fw_jump_src, os.path.join(core_dir, "fw_jump.bin"))
            print(f"✅ fw_jump.bin copiado para {core_dir}/")
    else:
        print("\nBuild concluído! Artefatos gerados.")
        print("Sugestão de comando para compilar o OpenSBI manualmente (se necessário):")
        print(f"make -C /caminho/para/opensbi CROSS_COMPILE=riscv64-unknown-linux-gnu- PLATFORM=generic \\")
        print(f"     FW_FDT_PATH={os.path.abspath(dtb_out)} \\")
        print(f"     FW_JUMP_FDT_ADDR=0x{dtb_addr}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestrador de Build de Targets FPGA para KernelCI")
    parser.add_argument("-n", "--name", type=str, required=True, help="Nome do Softcore (ex: vexiiriscv)")
    parser.add_argument("-t", "--target", type=str, required=True, help="Dispositivo/Placa FPGA (ex: opensourcesdrlab_kintex7)")
    parser.add_argument("-s", "--opensbi", type=str, required=False, help="Caminho absoluto para o diretório base do OpenSBI")

    args = parser.parse_args()
    main(core=args.name, target=args.target, opensbi_path=args.opensbi)