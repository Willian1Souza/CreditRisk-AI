"""
Ponto de entrada raiz para treinamento dos modelos de Machine Learning.
Delega a execução para o módulo src.train.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.train import executar_pipeline_treinamento

if __name__ == "__main__":
    executar_pipeline_treinamento()
