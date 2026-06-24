import os
import sys
import yaml
import json
import argparse
import subprocess
import shutil

# Definições de cores ANSI para o terminal
COLOR_RED = '\033[91m'
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_RESET = '\033[0m'

CROSS_COMPILE_CMD = os.environ.get("CROSS_COMPILE", "riscv64-unknown-linux-gnu-")

LITEX_ENV_DIR = os.environ.get("LITEX_ENV_DIR", "/eda/litex/env")
LITEX_VENV_PYTHON = f"{LITEX_ENV_DIR}/bin/python"
LITEX_TARGETS_DIR = os.environ.get("LITEX_TARGETS_DIR", "/eda/litex/litex-boards/litex_boards/targets")

def print_msg(msg_type: str, msg: str) -> None:
    """Imprime mensagens coloridas de acordo com a severidade."""
    if msg_type == "info":
        print(f"\n{COLOR_BLUE}--- {msg} ---{COLOR_RESET}")
    elif msg_type == "success":
        print(f"{COLOR_GREEN}[SUCCESS] {msg}{COLOR_RESET}")
    elif msg_type == "warning":
        print(f"{COLOR_YELLOW}[WARNING] {msg}{COLOR_RESET}")
    elif msg_type == "error":
        print(f"\n{COLOR_RED}[ERROR] {msg}{COLOR_RESET}")
    elif msg_type == "cmd":
        print(f"{COLOR_BLUE}> {msg}{COLOR_RESET}")
    else:
        print(msg)

def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print_msg("warning", f"Arquivo de configuração '{config_path}' não encontrado. Usando defaults.")
        return {}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}

def run_command(cmd: list, cwd: str = None, env: dict = None) -> None:
    cmd_str = " ".join(cmd)
    print_msg("cmd", f"Executando: {cmd_str}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd, env=env)
    except subprocess.CalledProcessError as e:
        print_msg("error", f"Comando falhou. Código de saída: {e.returncode}")
        sys.exit(1)

def main(core: str, target: str, opensbi_path: str) -> None:
    core_dir = os.path.join(target, core)

    if not os.path.exists(target):
        print_msg("error", f"Diretório do target '{target}' não existe.")
        sys.exit(1)
    if not os.path.exists(core_dir):
        print_msg("error", f"Diretório do core '{core_dir}' não existe.")
        sys.exit(1)

    # 1. Carregar configurações (Target + Core)
    target_cfg = load_config(os.path.join(target, "target_config.yaml"))
    core_cfg = load_config(os.path.join(core_dir, "core_config.yaml"))

    # Preparar um ambiente Python limpo para o subprocesso
    custom_env = os.environ.copy()
    custom_env["PATH"] = f"{LITEX_ENV_DIR}/bin:{custom_env.get('PATH', '')}"
    custom_env["VIRTUAL_ENV"] = LITEX_ENV_DIR
    custom_env.pop("PYTHONHOME", None)

    # 2. Localizar o script da placa
    target_script = os.path.join(LITEX_TARGETS_DIR, f"{target}.py")
    if not os.path.exists(target_script):
        target_script = os.path.join(target, f"{target}.py")
        if not os.path.exists(target_script):
            print_msg("error", f"Script da placa '{target}.py' não encontrado.")
            sys.exit(1)

    # 3. Montar o comando do LiteX base
    litex_cmd = [
        LITEX_VENV_PYTHON, target_script,
        "--build",
        f"--cpu-type={core_cfg.get('cpu_type', core)}",
        f"--cpu-variant={core_cfg.get('cpu_variant', 'standard')}"
    ]

    # Processar flags do core (agora o cpu-count entra aqui de forma genérica)
    for flag in core_cfg.get('core_flags', []):
        litex_cmd.append(str(flag))

    # Processar flags do target
    if 'sys_clk_freq' in target_cfg:
        litex_cmd.append(f"--sys-clk-freq={str(target_cfg['sys_clk_freq'])}")

    for flag in target_cfg.get('target_flags', []):
        litex_cmd.append(str(flag))

    # 4. Executar o build do Hardware
    print_msg("info", f"Iniciando Build do Hardware: {target} com {core}")
    run_command(litex_cmd, env=custom_env)

    # 5. Localizar e mover CSRs
    build_dir = os.path.join("build", target)
    csr_json_src = os.path.join(build_dir, "csr.json")
    csr_csv_src = os.path.join(build_dir, "csr.csv")

    if not os.path.exists(csr_json_src):
        print_msg("error", f"Arquivo {csr_json_src} não encontrado.")
        sys.exit(1)

    shutil.copy(csr_json_src, os.path.join(core_dir, "csr.json"))
    shutil.copy(csr_csv_src, os.path.join(core_dir, "csr.csv"))
    print_msg("success", f"CSRs copiados para {core_dir}/")

    # 6. Gerar a Device Tree
    print_msg("info", "Gerando Device Tree e boot.json")
    dts_out = os.path.join(core_dir, "system.dts")
    boot_json_out = os.path.join(core_dir, "boot.json")

    dts_gen_cmd = [
        sys.executable, "dts_generator.py",
        "--json", os.path.join(core_dir, "csr.json"),
        "--dts", dts_out,
        "--boot-json", boot_json_out
    ]
    run_command(dts_gen_cmd, env=custom_env)

    # 7. Compilar o .dtb
    print_msg("info", "Compilando .dts para .dtb")
    dtb_out = os.path.join(core_dir, "system.dtb")
    dtc_cmd = ["dtc", "-I", "dts", "-O", "dtb", "-o", dtb_out, dts_out]
    run_command(dtc_cmd, env=custom_env)

    # 8. Tratar o OpenSBI
    try:
        with open(boot_json_out, 'r') as f:
            boot_data = json.load(f)
            dtb_addr = boot_data.get("Image", "0x80200000").replace("0x", "")
    except Exception:
        dtb_addr = "80200000"

    dtb_addr = "82F00000"  # Endereço fixo para o dtb, pode ser ajustado conforme necessário

    if opensbi_path and os.path.exists(opensbi_path):
        print_msg("info", f"Compilando OpenSBI a partir de {opensbi_path}")
        run_command(["make", "clean"], cwd=opensbi_path, env=custom_env)
        opensbi_cmd = [
            "make",
            CROSS_COMPILE_CMD,
            "PLATFORM=generic",
            f"FW_FDT_PATH={os.path.abspath(dtb_out)}",
            f"FW_JUMP_FDT_ADDR=0x{dtb_addr}"
        ]
        run_command(opensbi_cmd, cwd=opensbi_path, env=custom_env)
        
        fw_jump_src = os.path.join(opensbi_path, "build", "platform", "generic", "firmware", "fw_jump.bin")
        if os.path.exists(fw_jump_src):
            shutil.copy(fw_jump_src, os.path.join(core_dir, "fw_jump.bin"))
            print_msg("success", f"fw_jump.bin copiado para {core_dir}/")
    else:
        print_msg("success", "Build do SoC concluído! Artefatos gerados.")
        print_msg("info", "Para compilar o OpenSBI manualmente (se necessário):")
        print(f"make -C /caminho/opensbi CROSS_COMPILE=riscv64-unknown-linux-gnu- PLATFORM=generic \\")
        print(f"     FW_FDT_PATH={os.path.abspath(dtb_out)} FW_JUMP_FDT_ADDR=0x{dtb_addr}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", type=str, required=True)
    parser.add_argument("-t", "--target", type=str, required=True)
    parser.add_argument("-s", "--opensbi", type=str, required=False)

    args = parser.parse_args()
    main(core=args.name, target=args.target, opensbi_path=args.opensbi)