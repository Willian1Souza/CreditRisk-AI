"""
Ponto de entrada raiz para Análise Exploratória e Validação de Dados (EDA).
Delega a execução para o módulo src.eda.
"""
import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.eda import executar_pipeline_completo

if __name__ == "__main__":
    executar_pipeline_completo()
