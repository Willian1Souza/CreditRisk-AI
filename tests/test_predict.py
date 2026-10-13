import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para permitir execução direta do script
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from src.predict import CreditRiskPredictor
except ModuleNotFoundError:
    from predict import CreditRiskPredictor

predictor = CreditRiskPredictor()

cliente = {
    "SEX": 2,
    "EDUCATION": 2,
    "MARRIAGE": 1,
    "LIMIT_BAL": 50000,
    "AGE": 35,

    "PAY_0": 2,
    "PAY_2": 1,
    "PAY_3": 0,
    "PAY_4": 0,
    "PAY_5": 0,
    "PAY_6": 0,

    "BILL_AMT1": 30000,
    "BILL_AMT2": 28000,
    "BILL_AMT3": 25000,
    "BILL_AMT4": 23000,
    "BILL_AMT5": 20000,
    "BILL_AMT6": 18000,

    "PAY_AMT1": 2000,
    "PAY_AMT2": 3000,
    "PAY_AMT3": 2500,
    "PAY_AMT4": 2000,
    "PAY_AMT5": 1500,
    "PAY_AMT6": 1000,

    "MAX_ATRASO_6M": 2,
    "QTD_MESES_ATRASO": 2,
    "TAXA_UTILIZACAO_LIMITE": 0.60
}

resultado = predictor.prever(cliente)

print("Modelo:", resultado["modelo"])
print("Score:", resultado["score_modelo"])
print("Classe prevista:", resultado["classe_predita"])