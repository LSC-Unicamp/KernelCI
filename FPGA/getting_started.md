# Bootando Linux em FPGAs utilizando LiteX

O boot de um softcore RISC-V em uma FPGA necessita de um SoC (*System on Chip*) mínimo, com recursos essenciais como controlador de memória, UART e, se possível, periféricos adicionais como controladores Ethernet. Construir um SoC capaz de entregar tais recursos do zero não é uma tarefa trivial; demanda um tempo considerável de desenvolvimento e verificação.

Por outro lado, integrar periféricos de terceiros a um núcleo softcore também apresenta desafios significativos, como problemas de compatibilidade, mapeamento de faixas de endereçamento em IOMMU e MMU, entre outros detalhes de arquitetura.

É neste cenário que o **LiteX** surge como uma ferramenta de grande utilidade. Ele permite integrar uma FPGA e um SoC a um softcore de maneira muito simples. Além de fornecer os periféricos e controladores, o LiteX auxilia com a geração de uma BIOS/Firmware, drivers, uma pré-*device tree*, síntese facilitada, entre outros recursos que aceleram o fluxo de trabalho.

## Instalando o ferramental

### Toolchains

FPGAs de fabricantes distintos necessitam de *toolchains* (cadeia de ferramentas) diferentes para a etapa de síntese e roteamento (transformar o código em hardware real).

* **AMD/Xilinx:** Utilizam o Vivado.
* **Intel/Altera:** Utilizam o Quartus.
* **Lattice:** Possuem excelente suporte com ferramentas *open source*, como a toolchain do Yosys, disponível no OSS CAD Suite.

> **Nota para iniciantes:** A instalação das toolchains proprietárias (Vivado, Quartus) costuma exigir a criação de contas nos sites dos fabricantes e o download de arquivos pesados. A configuração dessas ferramentas proprietárias ficará a cargo do leitor.

### OSS CAD Suite

O **OSS CAD Suite** é um conjunto de ferramentas *open source* para design de hardware. Ele inclui ferramentas para síntese, simulação, verificação e *build* para diversas FPGAs. O tutorial abaixo é baseado no repositório oficial do [OSS CAD Suite no GitHub](https://github.com/YosysHQ/oss-cad-suite-build).

1. Baixe o pacote de instalação do [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2025-05-07). Eu utilizei especificamente esta [versão](https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2025-05-07/oss-cad-suite-linux-x64-20250507.tgz). Caso haja uma versão mais recente disponível no dia em que você seguir este tutorial, recomendo verificar a seção de *releases* no GitHub para baixar a versão mais atualizada.
2. Crie uma pasta chamada **eda** (abreviação de *Electronic Design Automation*) no seu diretório *home* e descompacte o arquivo nela. Ele criará um diretório chamado **oss-cad-suite**.
3. Adicione o **oss-cad-suite** ao seu `PATH`, incluindo uma entrada no seu `.bashrc` ou `.zshrc`, como mostrado abaixo:

Esse passo a passo pode ser resumido nos seguintes comandos:

```bash
mkdir -p ~/eda
cd ~/eda
wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2025-05-07/oss-cad-suite-linux-x64-20250507.tgz
tar xvf oss-cad-suite-linux-x64-20250507.tgz

# Para usuários de Bash
echo "export PATH=\$PATH:$HOME/eda/oss-cad-suite/bin" >> ~/.bashrc
# Para usuários de Zsh
echo "export PATH=\$PATH:$HOME/eda/oss-cad-suite/bin" >> ~/.zshrc

rm oss-cad-suite-linux-x64-20250507.tgz
source ~/.bashrc # ou ~/.zshrc para recarregar as variáveis

```

#### Observações para macOS e Windows

* **macOS:** Certifique-se de baixar a versão correta do pacote, compatível com seu sistema. Para Macs com Apple Silicon (M1/M2/M3/M4), utilize a versão com o sufixo `darwin-arm64`. Para Macs com processadores Intel, use a versão `darwin-x64`.
* **Windows:** Recomenda-se fortemente utilizar o **WSL 2 (Windows Subsystem for Linux)** com uma distribuição como o Ubuntu para maior compatibilidade com essas ferramentas.

---

### LiteX

O LiteX é um *framework* robusto escrito em Python que facilita a criação e uso de cores e SoCs em FPGAs. Ele oferece suporte a uma vasta quantidade de placas e inclui uma rica biblioteca de IPs (módulos de hardware) e *cores open-source*.

#### Dependências do LiteX

O **LiteX** depende de ferramentas Python e do sistema de *build* **Meson**. Abaixo estão as instruções para instalação nos principais sistemas operacionais baseados em Linux e macOS.

##### Debian/Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv meson

```

##### Arch Linux

```bash
sudo pacman -Syu python python-pip meson

```

##### Fedora

```bash
sudo dnf install -y python3 python3-pip python3-virtualenv meson

```

##### macOS (via Homebrew)

```bash
brew install python3 meson

```

#### Instalando o LiteX

Para instalar o LiteX de forma isolada, utilizaremos um ambiente virtual (`venv`), conforme recomendado pela documentação oficial:

```bash
cd ~/eda
mkdir -p litex
cd litex
python3 -m venv litex_env
wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py
# Ative o ambiente virtual antes de instalar
source litex_env/bin/activate
python3 ./litex_setup.py --init --install --config=standard

# Criando um atalho para facilitar a ativação futura
echo 'alias get_litex="source $HOME/eda/litex/litex_env/bin/activate"' >> ~/.bashrc
echo 'alias get_litex="source $HOME/eda/litex/litex_env/bin/activate"' >> ~/.zshrc

```

A instalação pode levar alguns minutos, pois o script clona diversos repositórios essenciais para o funcionamento do framework. Sempre que for trabalhar no projeto, basta digitar `get_litex` no terminal para ativar o ambiente.

> Para aqueles que desejam se aprofundar nos fundamentos do LiteX, os desenvolvedores disponibilizam excelentes tutoriais práticos: [FPGA 101](https://github.com/litex-hub/fpga_101).

---

### Ajuste de permissões para acessar a USB sem ser root

Muitas vezes, a gravação do *bitstream* na FPGA via USB falha por falta de permissões do usuário padrão. Se você precisar acessar dispositivos JTAG/USB sem utilizar `sudo`, execute o script corretivo do openFPGALoader:

```bash
curl -sSL https://raw.githubusercontent.com/lushaylabs/openfpgaloader-ubuntufix/main/setup.sh | sh

```

*(Após executar isso, pode ser necessário desconectar e reconectar a placa USB, ou até mesmo reiniciar a sessão).*

---

### Compilador RISC-V

Para rodar Linux em nosso softcore, precisamos de uma *toolchain* (compilador cruzado) capaz de traduzir o código C/C++ para instruções da arquitetura RISC-V de 64 bits. O LiteX facilita isso baixando uma versão pré-compilada:

```bash
cd ~/eda/litex 
sudo python3 ./litex_setup.py --gcc=riscv

```

---

## Gerando o SoC

Dentro da estrutura instalada pelo LiteX, há um diretório chamado `litex-boards`. Este repositório concentra descrições de hardware e mapeamento de pinos para dezenas de FPGAs do mercado. Em `litex-boards/litex_boards/targets`, você encontra os *scripts* prontos para cada placa.

Neste tutorial, usaremos a **Open Source SDR Lab Kintex-7**. A escolha é baseada simplesmente no fato de ser a placa que possuo em laboratório e da qual realizei o porte para o LiteX, mas a lógica se aplica a **qualquer outra placa** suportada.

Ao rodar o arquivo alvo com a flag `--help` (`python opensourcesdrlab_kintex7.py --help`), diversas opções de customização do SoC aparecem. Nós construiremos um SoC utilizando o núcleo **Rocket** (um conhecido core RISC-V open-source desenvolvido pela UC Berkeley), configurado com 4 *cores* e com a pilha de rede habilitada.

Execute o comando de *build* (certifique-se de estar com o ambiente do LiteX ativado e dentro da pasta dos targets da placa):

```bash
python opensourcesdrlab_kintex7.py --build \
    --cpu-type rocket --cpu-variant linux --cpu-num-cores 4 --cpu-mem-width 2 \
    --sys-clk-freq 100e6 --with-ethernet --with-spi-sdcard --with-video-terminal \
    --eth-dynamic-ip --remote-ip 192.168.0.193

```

> **Atenção:** Substitua o `--remote-ip` para o endereço da sua máquina *host* (seu PC), que atuará como servidor TFTP durante o boot via rede. O uso de `--eth-dynamic-ip` nos permite configurar o IP do sistema dinamicamente na FPGA pelo LiteX term, mas você também pode forçar um IP estático usando `--eth-ip <ip>`.

Após o término do longo processo de síntese, você verá o surgimento de uma pasta `build` no diretório atual. Dentro dela, haverá uma estrutura como esta:

```bash
build/opensourcesdrlab_kintex7/
├── csr.csv
├── csr.json
├── gateware
├── litex.log
└── software

```

* **csr.csv / csr.json:** Possuem o mapeamento de endereços (*Control and Status Registers*) de todos os periféricos gerados no SoC. Eles servirão de base para a geração da *Device Tree* para o Linux.
* **gateware:** Contém toda a parte de hardware gerada (os arquivos `.v` em Verilog, o `.bit` final e os logs da ferramenta de síntese).
* **software:** Contém as bibliotecas do LiteX e o código gerado para a BIOS.

Para gravar o hardware sintetizado na placa, basta rodar:

```bash
python opensourcesdrlab_kintex7.py --load
# ou, se preferir gravar diretamente usando o openFPGALoader:
openFPGALoader -b opensourceSDRLabKintex7 build/opensourcesdrlab_kintex7/gateware/opensourcesdrlab_kintex7.bit

```

---

## Compilando a pilha de software

Para realizar o boot completo de um sistema operacional, precisaremos de quatro componentes em cadeia:

1. **Device Tree (DTS/DTB):** Um mapa legível por máquina dizendo ao kernel onde está cada hardware na FPGA.
2. **OpenSBI:** A interface de *firmware* de baixo nível padrão do RISC-V.
3. **Kernel Linux:** O núcleo do sistema operacional.
4. **Rootfs:** O sistema de arquivos (diretórios, bibliotecas e utilitários). Utilizaremos o Buildroot ou o BusyBox.

### Gerando a Device Tree

Para que o Linux saiba operar nosso hardware gerado sob demanda, precisamos converter os registros contidos no `csr.json` em um formato que o Linux entenda (um `.dts`). Para isso, utilize um script utilitário como o `dts_generator`:

```bash
python dts_generator.py \
    --json opensourcesdrlab_kintex7/rocket/csr.json \
    --dts opensourcesdrlab_kintex7/rocket/system.dts \
    --boot-json opensourcesdrlab_kintex7/rocket/boot.json

```

A saída trará algo parecido com:

```bash
Device Tree gerada com sucesso em: opensourcesdrlab_kintex7/rocket/system.dts
Configuração de boot gerada em:    opensourcesdrlab_kintex7/rocket/boot.json

Sugestão de comando para compilar o OpenSBI:
make CROSS_COMPILE=riscv64-unknown-linux-gnu- PLATFORM=generic \
     FW_FDT_PATH=/home/julio/Documents/kernel_ci/KernelCI/FPGA/opensourcesdrlab_kintex7/rocket/system.dtb \
     FW_JUMP_FDT_ADDR=0x82400000

```

Utilizaremos o `boot.json` para comandar o boot no terminal do LiteX, e o comando sugerido será útil para compilar o OpenSBI.

Antes de compilar o firmware, precisamos compilar o arquivo de texto `.dts` (Device Tree Source) em um binário `.dtb` (Device Tree Blob) usando o Device Tree Compiler (`dtc`):

```bash
# Certifique-se de estar no diretório correto onde o system.dts foi gerado
dtc -O dtb system.dts -o system.dtb

```

### OpenSBI

O OpenSBI fornece o ambiente de execução em modo de máquina (*Machine Mode*) exigido pela especificação RISC-V antes de delegar a execução ao Linux (*Supervisor Mode*).

```bash
git clone https://github.com/riscv-software-src/opensbi
cd opensbi

```

Utilize o comando sugerido no passo da *Device Tree* para compilar o firmware, adaptando os diretórios conforme necessário para o seu sistema:

```bash
make CROSS_COMPILE=riscv64-unknown-linux-gnu- PLATFORM=generic \
     FW_FDT_PATH=/home/julio/Documents/kernel_ci/KernelCI/FPGA/opensourcesdrlab_kintex7/rocket/system.dtb \
     FW_JUMP_FDT_ADDR=0x82400000

```

> **Atenção aos endereços:** O parâmetro `FW_JUMP_FDT_ADDR=0x82400000` define onde a Device Tree será carregada na RAM. Para sistemas de arquivo raiz (rootfs) muito grandes, pode ocorrer desse endereço colidir e ser subscrito, causando *Kernel Panics*. Se isso acontecer, você precisará afastar este endereço.

Após a compilação, o arquivo `fw_jump.bin` será gerado. Ele deve ser movido para o diretório raiz do seu servidor TFTP (geralmente `/srv/tftp/` ou `/tftpboot/`):

```bash
sudo cp build/platform/generic/firmware/fw_jump.bin /srv/tftp/

```

### Kernel Linux

Para garantir melhor compatibilidade de drivers e mapeamento com o ambiente gerado pelo LiteX, utilizaremos o *fork* do Linux mantido pelo projeto:

```bash
git clone https://github.com/litex-hub/linux -b litex-rebase
cd linux

```

O LiteX já fornece uma configuração padrão para o núcleo Rocket, o que simplifica drasticamente o processo:

```bash
make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- litex_rocket_defconfig

```

*(Nota: Essa configuração geralmente funciona bem para outros softcores RISC-V com pouca ou nenhuma modificação).*

Se desejar personalizar algum módulo (como adicionar drivers de rede específicos ou recursos ao kernel), use:

```bash
make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- menuconfig

```

Compile o kernel aproveitando todos os núcleos do seu computador:

```bash
make ARCH=riscv CROSS_COMPILE=riscv64-unknown-linux-gnu- -j$(nproc)

```

Assim como fizemos com o firmware, copie a imagem gerada do Kernel para o servidor TFTP:

```bash
cp arch/riscv/boot/Image /srv/tftp/

```

---

### Rootfs Opção 1: BusyBox (Gerando o initrd_bb)

O BusyBox fornece uma versão minimalista de vários utilitários padrão do Unix, ideal para testes de hardware focados e *boot* rápido.

Baixe e descompacte a versão (verifique no [site oficial](https://busybox.net/downloads/) se há alguma versão mais recente):

```bash
curl -O https://busybox.net/downloads/busybox-1.38.0.tar.bz2 
tar -xf busybox-1.38.0.tar.bz2
cd busybox-1.38.0

```

Configure e compile o BusyBox como binário estático (importante para não dependermos de bibliotecas externas complexas no início):

```bash
export CROSS_COMPILE=riscv64-unknown-linux-gnu-
make ARCH=riscv defconfig
make ARCH=riscv menuconfig
# No menuconfig, vá em Settings -> Build static binary (no shared libs) e marque esta opção. Salve e saia.

make ARCH=riscv -j$(nproc)
make ARCH=riscv install

```

O comando `install` criará uma pasta chamada `_install` dentro do diretório atual, contendo os binários essenciais. **Agora, precisamos transformar essa pasta em um sistema raiz viável (*initrd_bb*):**

1. Acesse o diretório `_install` e crie a estrutura de diretórios padrão do Linux:
```bash
cd _install
mkdir -p dev proc sys etc/init.d lib tmp mnt root

```


2. O kernel procurará por um arquivo chamado `init` para rodar assim que carregar. Crie este arquivo apontando para o *shell* e montando os diretórios virtuais do Linux:
```bash
cat << 'EOF' > init
#!/bin/sh
# Monta os diretórios do sistema
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

# Inicializa interfaces de rede (se necessário)
ifconfig lo up

echo "======================================"
echo " Bem-vindo ao Linux no LiteX (BusyBox) "
echo "======================================"

# Transfere a execução para o shell interativo
exec /bin/sh
EOF

```


3. Dê permissão de execução ao script:
```bash
chmod +x init

```


4. Empacote todo o diretório no formato `cpio` compactado com `gzip`. Este será o seu `initrd_bb`:
```bash
find . -print0 | cpio --null -ov --format=newc | gzip -9 > ../initrd_bb

```


5. Copie o arquivo finalizado para o servidor TFTP:
```bash
cp ../initrd_bb /srv/tftp/

```



---

### Rootfs Opção 2: Buildroot

Se você necessitar de um sistema mais completo (com bibliotecas, SSH, utilitários de rede complexos), o Buildroot é a melhor escolha.

```bash
git clone https://git.buildroot.net/buildroot
cd buildroot
make menuconfig

```

No menu de configuração, faça os seguintes ajustes:

* **Target Options:** RISCV, extensão G, 64-bit (específico para o Rocket; outros softcores podem ser 32-bit).
* **Target ABI:** `lp64d`.
* **Toolchain:** Mude para *Bootlin toolchains* e escolha a variante `riscv64-lp64d musl stable` (sempre prefira a mais recente compatível). Em *Toolchain origin*, selecione *Toolchain to be downloaded and installed*. Use opções de linkagem estática.

Compile o projeto (isso pode demorar bastante no primeiro acesso pois baixará toda a *toolchain* de compilação):

```bash
make -j$(nproc)

```

Após compilado, copie o arquivo de rootfs gerado para o servidor TFTP:

```bash
cp output/images/rootfs.cpio.gz /srv/tftp/

```

---

## Bootando o sistema

Se você for utilizar a opção do **BusyBox**, lembre-se de editar o arquivo `boot.json` gerado anteriormente, substituindo a referência do arquivo `rootfs.cpio.gz` para o `initrd_bb` que acabamos de criar.

### Boot pela Serial (Carregamento Lento)

Para bootar puxando os arquivos via cabo de comunicação serial:

```bash
cd /srv/tftp/
# Substitua pelo dispositivo serial gerado pela sua FPGA
litex_term /dev/ttyUSB1 --image=boot.json 

```

*(Nota: Essa opção é extremamente lenta em sistemas completos devido ao baixo baudrate da UART, mas serve em caso de ausência de rede).*

### Boot via Rede (Recomendado)

O boot via rede utilizando TFTP é consideravelmente mais rápido. Se o IP local e o remoto (host) da sua placa já estiverem configurados corretamente no SoC e roteador, muitas vezes o boot da rede (via PXE/TFTP) ocorrerá de forma automática.

Se não ocorrer automaticamente, entre no terminal do LiteX, interrompa o processo de boot (pressionando *Enter* na tela de BIOS do LiteX) e use os seguintes comandos:

```bash
litex_term /dev/ttyUSB1

# No prompt do LiteX:
# Configure o IP do servidor onde estão os arquivos
eth_remote_ip 192.168.0.193 

# Configure o IP da FPGA (verifique em seu roteador/DHCP um IP livre)
eth_local_ip 192.168.0.100  

# Aciona o comando de boot via rede
netboot

```

Se tudo ocorrer bem, o LiteX baixará os arquivos `fw_jump.bin`, `Image` e `initrd_bb`/`rootfs.cpio.gz` via TFTP para a RAM e você verá o *log* de *boot* do Linux surgindo em seu terminal até o shell!