import sys
from pathlib import Path
import time
import requests
import uvicorn
import threading

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)

    base_url = "http://127.0.0.1:8001"

    print("--- TESTE 1: GET /health ---")
    r = requests.get(f"{base_url}/health")
    print(f"Status: {r.status_code}, Resposta: {r.json()}")
    assert r.status_code == 200
    assert r.json()["status"] == "online"

    print("\n--- TESTE 2: GET /model/info ---")
    r = requests.get(f"{base_url}/model/info")
    print(f"Status: {r.status_code}, Modelo: {r.json()['modelo']}, Total Features: {r.json()['total_features']}")
    assert r.status_code == 200
    assert r.json()["total_features"] == 26

    cliente_exemplo = {
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
        "PAY_AMT6": 1000
    }

    print("\n--- TESTE 3: POST /predict (Atributos Derivados Automáticos) ---")
    r = requests.post(f"{base_url}/predict", json=cliente_exemplo)
    print(f"Status: {r.status_code}, Resposta: {r.json()}")
    assert r.status_code == 200
    res = r.json()
    assert res["classe_predita"] in (0, 1)
    assert res["atributos_derivados"]["MAX_ATRASO_6M"] == 2
    assert res["atributos_derivados"]["QTD_MESES_ATRASO"] == 2
    assert res["atributos_derivados"]["TAXA_UTILIZACAO_LIMITE"] == 0.6

    print("\n--- TESTE 4: POST /predict (Com envelopamento {'dados': ...}) ---")
    r = requests.post(f"{base_url}/predict", json={"dados": cliente_exemplo})
    print(f"Status: {r.status_code}, Decisao: {r.json()['decisao']}")
    assert r.status_code == 200

    print("\n--- TESTE 5: POST /predict (Validação de Erro Categórico SEX=9) ---")
    cliente_invalido = dict(cliente_exemplo)
    cliente_invalido["SEX"] = 9
    r = requests.post(f"{base_url}/predict", json=cliente_invalido)
    print(f"Status: {r.status_code}, Erro: {r.json()}")
    assert r.status_code == 422

    print("\n--- TESTE 6: POST /predict (Validação de Atributo Derivado Inconsistente) ---")
    cliente_derivado_invalido = dict(cliente_exemplo)
    cliente_derivado_invalido["MAX_ATRASO_6M"] = 5
    r = requests.post(f"{base_url}/predict", json=cliente_derivado_invalido)
    print(f"Status: {r.status_code}, Erro: {r.json()}")
    assert r.status_code == 422

    print("\n--- TESTE 7: POST /predict/batch (Lote com múltiplos clientes) ---")
    lote = [cliente_exemplo, cliente_exemplo]
    r = requests.post(f"{base_url}/predict/batch", json=lote)
    print(f"Status: {r.status_code}, Resumo: {r.json()['resumo']}, Total: {r.json()['total_solicitados']}")
    assert r.status_code == 200
    assert r.json()["total_solicitados"] == 2
    assert len(r.json()["previsoes"]) == 2

    print("\n--- TESTE 8: POST /predict/batch (Lote envelopado {'clientes': [...]}) ---")
    r = requests.post(f"{base_url}/predict/batch", json={"clientes": lote})
    print(f"Status: {r.status_code}, Resumo: {r.json()['resumo']}")
    assert r.status_code == 200

    print("\n--- TESTE 9: POST /predict/batch (Lote com cliente inválido) ---")
    lote_com_erro = [cliente_exemplo, cliente_invalido]
    r = requests.post(f"{base_url}/predict/batch", json=lote_com_erro)
    print(f"Status: {r.status_code}, Erro: {r.json()}")
    assert r.status_code == 422

    print("\n>>> TODOS OS TESTES PASSARAM COM SUCESSO! <<<")
