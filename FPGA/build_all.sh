#!/bin/bash

# Define o caminho do OpenSBI. Pode ser sobrescrito passando um argumento ao script.
OPENSBI_PATH=${1:-"/eda/linux_on_fpga/opensbi"}

# Definições de cores ANSI para o terminal
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
RESET='\033[0m'

echo -e "${BLUE}======================================================${RESET}"
echo -e "${BLUE}   Iniciando Compilação em Lote (Targets & Cores)     ${RESET}"
echo -e "${BLUE}======================================================${RESET}"
echo -e "${YELLOW}Caminho OpenSBI configurado para: ${OPENSBI_PATH}${RESET}\n"

# Arrays para contabilidade no final do script
SUCCESS_LIST=()
ERROR_LIST=()

# Itera sobre todos os diretórios no nível atual
for target_dir in */; do
    # Remove a barra (/) do final do nome do diretório
    target=${target_dir%/}

    # Verifica se o diretório é um target válido analisando a existência do YAML
    if [ -f "${target}/target_config.yaml" ]; then
        echo -e "${YELLOW}>> Encontrado Target: ${target}${RESET}"

        # Itera sobre os subdiretórios dentro do target
        for core_dir in "${target}"/*/; do
            core=$(basename "${core_dir}")

            # Verifica se é um core válido
            if [ -f "${target}/${core}/core_config.yaml" ]; then
                echo -e "\n${BLUE}------------------------------------------------------${RESET}"
                echo -e "${BLUE}[*] Iniciando Build: ${core} na placa ${target}${RESET}"
                echo -e "${BLUE}------------------------------------------------------${RESET}"

                # Executa o build_target.py
                if python3 build_target.py -n "${core}" -t "${target}" -s "${OPENSBI_PATH}"; then
                    echo -e "\n${GREEN}[SUCCESS] Compilação finalizada para ${target} / ${core}${RESET}"
                    
                    # Define o caminho do bitstream gerado pelo LiteX
                    # Exemplo: build/opensourcesdrlab_kintex7/gateware/opensourcesdrlab_kintex7.bin
                    BIN_FILE="build/${target}/gateware/${target}.bin"
                    DEST_DIR="${target}/${core}/"

                    # Verifica se o arquivo .bin realmente existe antes de copiar
                    if [ -f "${BIN_FILE}" ]; then
                        cp "${BIN_FILE}" "${DEST_DIR}"
                        echo -e "${GREEN}[SUCCESS] Bitstream (${target}.bin) copiado para ${DEST_DIR}${RESET}"
                        SUCCESS_LIST+=("${target}/${core}")
                    else
                        echo -e "${RED}[ERROR] Bitstream não encontrado no caminho esperado: ${BIN_FILE}${RESET}"
                        ERROR_LIST+=("${target}/${core} (Falta .bin)")
                    fi
                else
                    echo -e "\n${RED}[ERROR] Falha na compilação de ${target} / ${core}. Pulando para o próximo...${RESET}"
                    ERROR_LIST+=("${target}/${core} (Falha no Build)")
                fi
            fi
        done
    fi
done

# Resumo Final
echo -e "\n${BLUE}======================================================${RESET}"
echo -e "${BLUE}                  Resumo da Execução                  ${RESET}"
echo -e "${BLUE}======================================================${RESET}"

echo -e "${GREEN}Sucessos (${#SUCCESS_LIST[@]}):${RESET}"
for item in "${SUCCESS_LIST[@]}"; do
    echo -e "  - ${item}"
done

echo -e "\n${RED}Falhas (${#ERROR_LIST[@]}):${RESET}"
for item in "${ERROR_LIST[@]}"; do
    echo -e "  - ${item}"
done

echo -e "\n${BLUE}Processo concluído.${RESET}"
