from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    BASE_DIR / "models" / "best_credit_risk_model.joblib"
)

METRICS_PATH = (
    BASE_DIR / "models" / "metrics_summary.json"
)


from typing import Any, Union
import json


class CreditRiskPredictor:
    modelo: Any
    features: list[str]
    nome_modelo: str
    metricas: dict[str, Any]

    def __init__(self) -> None:
        self.modelo = joblib.load(MODEL_PATH)

        with open(METRICS_PATH, encoding="utf-8") as arquivo:
            metadata = json.load(arquivo)

        self.features = list(metadata["features_entrada"])
        self.nome_modelo = str(metadata["melhor_modelo"])
        self.metricas = dict(metadata.get("metricas", {}))

    def prever(self, dados_cliente: dict[str, Any]) -> dict[str, Any]:

        faltantes = set(self.features) - set(dados_cliente)
        extras = set(dados_cliente) - set(self.features)

        if faltantes or extras:
            raise ValueError(
                f"Features ausentes: {sorted(faltantes)}. "
                f"Features inesperadas: {sorted(extras)}"
            )

        cliente = pd.DataFrame(
            [dados_cliente],
            columns=self.features
        )

        probabilidade = float(
            self.modelo.predict_proba(cliente)[0][1]
        )

        return {
            "modelo": self.nome_modelo,
            "score_modelo": round(probabilidade, 4),
            "classe_predita": int(
                self.modelo.predict(cliente)[0]
            )
        }

    def prever_lote(self, lista_clientes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not lista_clientes:
            return []

        for i, dados in enumerate(lista_clientes):
            faltantes = set(self.features) - set(dados)
            extras = set(dados) - set(self.features)
            if faltantes or extras:
                raise ValueError(
                    f"Registro {i}: Features ausentes: {sorted(faltantes)}. "
                    f"Features inesperadas: {sorted(extras)}"
                )

        df_clientes = pd.DataFrame(lista_clientes, columns=self.features)
        probabilidades = self.modelo.predict_proba(df_clientes)[:, 1]
        predicoes = self.modelo.predict(df_clientes)

        resultados = []
        for prob, pred in zip(probabilidades, predicoes):
            resultados.append({
                "modelo": self.nome_modelo,
                "score_modelo": round(float(prob), 4),
                "classe_predita": int(pred)
            })
        return resultados