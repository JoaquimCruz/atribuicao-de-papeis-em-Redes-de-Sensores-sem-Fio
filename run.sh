#!/bin/bash

set -e


VENV_DIR="venv"

echo "=== Configurando o ambiente virtual para RSSF ==="


if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não está instalado no sistema." >&2
    exit 1
fi

# Cria o ambiente virtual se ele não existir
if [ ! -d "$VENV_DIR" ]; then
    echo "Criando ambiente virtual em '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
else
    echo "Ambiente virtual '$VENV_DIR' já existe."
fi

echo "Ativando o ambiente virtual..."
source "$VENV_DIR"/bin/activate

echo "Atualizando pip..."
pip install --upgrade pip

echo "Instalando dependências do requirements.txt..."
pip install -r requirements.txt

echo "=== Executando o script principal ==="
python main.py "$@"

echo "=== Execução concluída com sucesso! ==="
