"""
Ponto de entrada raiz para treinamento dos modelos.
Delega a execução para o módulo src.train.
"""
from src.train import executar_pipeline_treinamento

if __name__ == "__main__":
    executar_pipeline_treinamento()
