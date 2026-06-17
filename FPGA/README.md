# FPGA Targets

Este diretório contém todos os alvos (**targets**) suportados para execução do Linux em plataformas LiteX, organizados pela combinação de **FPGA + core RISC-V**.

Cada combinação representa um sistema independente, contendo todos os arquivos necessários para geração do SoC, descrição do hardware e configuração de boot.

## Estrutura

```text
FPGA/
├── artya7/
│   ├── rocket/
│   ├── cva6/
│   ├── blackparrot/
│   └── ...
│
├── nexys4ddr/
│   ├── rocket/
│   └── ...
│
├── opensourcesdrlab_kintex7/
│   ├── rocket/
│   └── ...
│
├── build_dtbs.sh
└── scripts/
```

Cada diretório `<board>/<core>/` representa um target específico.

Por exemplo:

```text
artya7/rocket/
├── boot.json
├── config.yaml
├── README.md
├── soc.sh
└── system.dts
```

## Arquivos

### `soc.sh`

Script responsável pela geração do SoC LiteX para aquela combinação de FPGA e processador.

Este script normalmente invoca o gerador do LiteX e produz o bitstream correspondente.

---

### `system.dts`

Device Tree Source correspondente ao hardware gerado.

Este arquivo descreve CPUs, memória, barramentos e periféricos presentes no sistema.

---

### `system.dtb`

Versão compilada do Device Tree.

É gerada a partir de `system.dts` utilizando o Device Tree Compiler (`dtc`) e não deve ser editada manualmente.

Para gerar todos os DTBs execute:

```bash
./build_dtbs.sh
```

---

### `boot.json`

Arquivo de configuração utilizado durante o processo de boot.

Seu conteúdo pode variar dependendo do método de carregamento adotado.

---

### `config.yaml`

Arquivo de metadados do target.

Contém informações sobre a plataforma e pode ser utilizado por scripts de automação ou integração com o KernelCI.

---

### `README.md`

Documentação específica daquele target.

Pode conter informações sobre limitações, configuração da FPGA, estado de funcionamento ou observações relevantes.

---

## Scripts auxiliares

A pasta `scripts/` contém utilitários utilizados durante o desenvolvimento.

| Script               | Descrição                                     |
| -------------------- | --------------------------------------------- |
| `clone.sh`           | Clona dependências necessárias ao projeto     |
| `generate_fwjump.sh` | Gera imagens OpenSBI (`fw_jump.bin`)          |
| `kselftest.sh`       | Executa testes do Linux Kernel Selftests      |
| `network.sh`         | Configuração de rede para execução dos testes |

## Adicionando um novo target

Para adicionar uma nova combinação de FPGA e processador, crie um novo diretório seguindo o padrão:

```text
<board>/<core>/
```

contendo, no mínimo:

```text
soc.sh
system.dts
boot.json
config.yaml
README.md
```

Após criar ou modificar um `system.dts`, gere o respectivo `system.dtb` executando:

```bash
./build_dtbs.sh
```

## Filosofia da organização

A organização deste diretório é baseada no conceito de **target**.

Cada combinação de **placa FPGA + core RISC-V** é tratada como uma plataforma independente, reunindo em um único local todos os arquivos necessários para síntese, boot e execução do Linux.

Essa abordagem facilita a manutenção, reduz a dispersão dos artefatos e simplifica a automação para ambientes de integração contínua, como o KernelCI.
