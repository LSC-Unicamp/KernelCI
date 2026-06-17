#!/usr/bin/env bash

set -euo pipefail

if ! command -v dtc >/dev/null 2>&1; then
    echo "Erro: dtc não encontrado."
    exit 1
fi

echo "Procurando arquivos system.dts..."

find . -type f -name "system.dts" | sort | while read -r dts; do

    dtb="${dts%.dts}.dtb"

    echo "Compilando:"
    echo "  $dts"
    echo "  -> $dtb"

    dtc \
        -I dts \
        -O dtb \
        -o "$dtb" \
        "$dts"

done

echo
echo "Todos os DTBs foram gerados com sucesso."