#!/usr/bin/env bash

set -euo pipefail

ROOT=$(pwd)
TARGETS_DIR="${ROOT}/targets"

boards=(
    artya7
    nexys4ddr
    opensourcesdrlab_kintex7
)

cores=(
    blackparrot
    cva6
    naxriscv
    openc906
    rocket
    vexiiriscv
)

mkdir -p "${TARGETS_DIR}"

for board in "${boards[@]}"; do

    for core in "${cores[@]}"; do

        dst="${TARGETS_DIR}/${board}/${core}"

        mkdir -p "${dst}"

        #
        # generate_soc.sh
        #

        if [ -f "socs/${board}/${core}.sh" ]; then
            cp "socs/${board}/${core}.sh" \
               "${dst}/soc.sh"
            chmod +x "${dst}/soc.sh"
        else
            cat > "${dst}/soc.sh" <<EOF
#!/usr/bin/env bash

echo "TODO: generate ${board}/${core}"
EOF
            chmod +x "${dst}/soc.sh"
        fi

        #
        # dts
        #

        if [ -f "dtbs/${board}/${core}.dts" ]; then
            cp "dtbs/${board}/${core}.dts" \
               "${dst}/system.dts"
        else
            cat > "${dst}/system.dts" <<EOF
/dts-v1/;

/ {
    model = "${board}-${core}";
    compatible = "${board},${core}";
};
EOF
        fi

        #
        # boot.json
        #

        cat > "${dst}/boot.json" <<EOF
{
    "board": "${board}",
    "core": "${core}",
    "fw_jump": "fw_jump.bin",
    "dtb": "system.dtb"
}
EOF

        #
        # config.yaml
        #

        cat > "${dst}/config.yaml" <<EOF
board: ${board}
core: ${core}

soc_generator: soc.sh

device_tree:
  source: system.dts
  binary: system.dtb

firmware:
  opensbi: fw_jump.bin

boot:
  boot.json
EOF

        #
        # README
        #

        cat > "${dst}/README.md" <<EOF
# ${board} / ${core}

Arquivos deste target.

## Conteúdo

- soc.sh
- system.dts
- system.dtb (gerado)
- fw_jump.bin (gerado)
- boot.json
- config.yaml
EOF

    done

done

echo
echo "======================================"
echo "Estrutura criada em:"
echo
echo "    ${TARGETS_DIR}"
echo
echo "system.dtb e fw_jump.bin devem ser gerados posteriormente."
echo "======================================"
