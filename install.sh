#!/bin/bash

# Define que o script deve parar se algum comando falhar
set -e

echo "Criando diretorio de trabalho /eda"
sudo mkdir -p /eda
sudo chown -R $USER:$USER /eda
cd /eda

echo "Identificando a distribuição do sistema..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "Não foi possível detectar a distribuição em /etc/os-release."
    exit 1
fi

echo "Distribuição detectada: $DISTRO"

echo "Instalando compiladores, toolchains, ferramentas de Kernel/U-Boot e TFTP..."
case $DISTRO in
    ubuntu|debian|pop)
        sudo apt update
        sudo apt install -y build-essential python3 python3-pip python3-venv python-is-python3 \
                            meson ninja-build git wget curl tar \
                            gcc-riscv64-unknown-elf picolibc-riscv64-unknown-elf \
                            gcc-riscv64-linux-gnu g++-riscv64-linux-gnu libc6-dev-riscv64-cross \
                            device-tree-compiler u-boot-tools tftpd-hpa \
                            bison flex libssl-dev bc lz4 zstd picocom
        
        # Diretório padrão do TFTP no Debian/Ubuntu
        TFTP_DIR="/srv/tftp"
        sudo systemctl enable tftpd-hpa || true
        ;;
    arch|manjaro|endeavouros)
        sudo pacman -Syu --noconfirm base-devel python python-pip python-virtualenv \
                                     meson ninja git wget curl tar \
                                     riscv64-elf-gcc riscv64-elf-newlib riscv64-elf-gdb \
                                     riscv64-linux-gnu-gcc riscv64-linux-gnu-binutils riscv64-linux-gnu-glibc \
                                     dtc uboot-tools tftp-hpa \
                                     bison flex openssl bc lz4 zstd picocom
        
        TFTP_DIR="/srv/tftp"
        sudo systemctl enable tftpd || true
        ;;
    fedora)
        sudo dnf update -y
        sudo dnf groupinstall -y "Development Tools" "C Development Tools and Libraries"
        sudo dnf install -y python3 python3-pip python3-virtualenv \
                            meson ninja-build git wget curl tar \
                            gcc-riscv64-linux-gnu \
                            dtc uboot-tools tftp-server \
                            bison flex openssl-devel bc lz4 zstd picocom
                            
        TFTP_DIR="/var/lib/tftpboot"
        sudo systemctl enable tftp || true
        ;;
    gentoo)
        sudo emerge --sync
        sudo emerge -av dev-lang/python dev-python/pip dev-build/meson dev-build/ninja \
                        dev-vcs/git net-misc/wget net-misc/curl app-arch/tar sys-devel/crossdev \
                        sys-apps/dtc dev-embedded/u-boot-tools net-ftp/tftp-hpa \
                        sys-devel/bison sys-devel/flex dev-libs/openssl sys-devel/bc \
                        app-arch/lz4 app-arch/zstd net-dialup/picocom
        
        echo "No Gentoo, configurando as toolchains RISC-V via crossdev..."
        echo "--> Compilando toolchain Bare-metal (elf)..."
        sudo crossdev -t riscv64-unknown-elf
        
        echo "--> Compilando toolchain Linux (linux-gnu)..."
        sudo crossdev -t riscv64-unknown-linux-gnu
        
        TFTP_DIR="/var/tftp"
        sudo rc-update add in.tftpd default || true
        ;;
    *)
        echo "Aviso: Distribuição '$DISTRO' não mapeada."
        echo "Por favor, instale manualmente as dependências."
        sleep 3
        TFTP_DIR="/srv/tftp"
        ;;
esac

echo "Configurando o diretório TFTP em $TFTP_DIR..."
sudo mkdir -p $TFTP_DIR
sudo chown -R nobody:nogroup $TFTP_DIR 2>/dev/null || sudo chown -R nobody:nobody $TFTP_DIR
sudo chmod -R 777 $TFTP_DIR

echo "Instalando OSS-CAD-Suite"
wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2025-05-07/oss-cad-suite-linux-x64-20250507.tgz
tar xvf oss-cad-suite-linux-x64-20250507.tgz

echo "Configurando PATH do OSS CAD Suite"
echo "export PATH=\$PATH:/eda/oss-cad-suite/bin" >> ~/.bashrc
echo "export PATH=\$PATH:/eda/oss-cad-suite/bin" >> ~/.zshrc

echo "Instalando Litex"
mkdir -p litex
cd litex
python3 -m venv litex_env
wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py

source litex_env/bin/activate
python3 ./litex_setup.py --init --install --config=standard
deactivate

echo 'alias get_litex="source /eda/litex/litex_env/bin/activate"' >> ~/.bashrc
echo 'alias get_litex="source /eda/litex/litex_env/bin/activate"' >> ~/.zshrc

if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO" == "pop" ]]; then
    echo "Aplicando fix do openFPGALoader para Ubuntu/Debian..."
    curl -sSL https://raw.githubusercontent.com/lushaylabs/openfpgaloader-ubuntufix/main/setup.sh | sh
fi

echo "Instalação concluída! Reinicie o seu terminal ou execute 'source ~/.bashrc' (ou .zshrc)."
echo "Servidor TFTP configurado com raiz em: $TFTP_DIR"
