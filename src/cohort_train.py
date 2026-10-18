"""Treina um modelo de risco agregado para coortes de crédito brasileiras."""

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_PATHS = (
    BASE_DIR / "Inadimplencia_Coorte_2024_4o_trimestre.xlsx",
    BASE_DIR / "Inadimplencia_Coorte_2025_1o_trimestre.xlsx",
)
MODEL_PATH = BASE_DIR / "models" / "cohort_delinquency_forecast.joblib"
METRICS_PATH = BASE_DIR / "models" / "cohort_delinquency_metrics.json"
MACROECONOMIC_WORKBOOK = "202609_Tabelas_de_estatisticas_monetarias_e_de_credito.xlsx"
CUTOFF_TARGET_DATE = pd.Timestamp("2024-12-31")

GROUP_COLUMNS = [
    "Coorte",
    "Tipo_de_Cliente",
    "Modalidade",
    "Faixa_de_Prazo_da_Operacao",
]
DATE_COLUMN = "Data_Base_de_Acompanhamento"
TARGET_COUNT_COLUMN = "Qtd_Atraso_90_dias"
DENOMINATOR_COLUMN = "Qtd_Operacoes_Coorte"

NUMERIC_FEATURES = [
    "Qtd_Atraso_30_dias",
    "Volume_Atraso_30_dias",
    "Qtd_Atraso_60_dias",
    "Volume_Atraso_60_dias",
    "Qtd_Atraso_90_dias",
    "Volume_Atraso_90_dias",
    "Qtd_Prejuizo_Acumulado",
    "Volume_Prejuizo_Acumulado",
    "Qtd_Operacoes_Excluidas_Atraso_90_E_H_Acumulado",
    "Volume_Operacoes_Excluidas_Atraso_90_E_H_Acumulado",
    DENOMINATOR_COLUMN,
    "Valor_Operacoes_Coorte",
    "idade_coorte_meses",
    "mes_acompanhamento",
]
CATEGORICAL_FEATURES = [
    "Tipo_de_Cliente",
    "Modalidade",
    "Faixa_de_Prazo_da_Operacao",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
REQUIRED_COLUMNS = set(
    GROUP_COLUMNS
    + [DATE_COLUMN, TARGET_COUNT_COLUMN]
    + NUMERIC_FEATURES[:12]
)
TARGET_COLUMN = "taxa_atraso_90d_proximo_mes"
SAMPLE_WEIGHT_COLUMN = "peso_operacoes"
TARGET_DATE_COLUMN = "data_alvo"


def carregar_dados_coorte(
    caminhos: tuple[Path, ...] = INPUT_PATHS,
) -> pd.DataFrame:
    """Lê e valida os arquivos mensais de coortes."""
    frames: list[pd.DataFrame] = []
    for caminho in caminhos:
        if not caminho.is_file():
            raise FileNotFoundError(f"Arquivo de coorte não encontrado: {caminho}")
        frame = pd.read_excel(caminho, engine="openpyxl")
        frame["arquivo_origem"] = caminho.name
        frames.append(frame)

    dados = pd.concat(frames, ignore_index=True)
    colunas_ausentes = REQUIRED_COLUMNS - set(dados.columns)
    if colunas_ausentes:
        raise ValueError(
            "Colunas obrigatórias ausentes nos arquivos de coorte: "
            f"{sorted(colunas_ausentes)}"
        )

    colunas_modelo = sorted(REQUIRED_COLUMNS)
    if dados[colunas_modelo].isna().any().any():
        raise ValueError("Os arquivos de coorte contêm valores nulos nos campos obrigatórios.")

    dados[DATE_COLUMN] = pd.to_datetime(dados[DATE_COLUMN], errors="raise")
    dados["Coorte"] = pd.to_datetime(dados["Coorte"], errors="raise")

    chave_snapshot = GROUP_COLUMNS + [DATE_COLUMN]
    if dados.duplicated(chave_snapshot).any():
        raise ValueError(
            "Há mais de uma observação para a mesma coorte, segmento e data-base."
        )

    if (dados[DENOMINATOR_COLUMN] <= 0).any():
        raise ValueError("O denominador Qtd_Operacoes_Coorte deve ser positivo.")

    colunas_contagem = [
        "Qtd_Atraso_30_dias",
        "Qtd_Atraso_60_dias",
        TARGET_COUNT_COLUMN,
        "Qtd_Prejuizo_Acumulado",
        "Qtd_Operacoes_Excluidas_Atraso_90_E_H_Acumulado",
        DENOMINATOR_COLUMN,
    ]
    if (dados[colunas_contagem] < 0).any().any():
        raise ValueError("As contagens dos arquivos de coorte não podem ser negativas.")
    if (dados[TARGET_COUNT_COLUMN] > dados[DENOMINATOR_COLUMN]).any():
        raise ValueError(
            "Há contagens de atraso de 90 dias maiores que o total de operações da coorte."
        )

    return dados


def construir_amostras_supervisionadas(dados: pd.DataFrame) -> pd.DataFrame:
    """Cria pares de snapshots mensais para prever atraso de 90 dias no mês seguinte."""
    dados_ordenados = dados.sort_values(GROUP_COLUMNS + [DATE_COLUMN]).copy()
    agrupados = dados_ordenados.groupby(GROUP_COLUMNS, sort=False)
    data_futura = agrupados[DATE_COLUMN].shift(-1)
    atraso_90_futuro = agrupados[TARGET_COUNT_COLUMN].shift(-1)
    proximo_mes = dados_ordenados[DATE_COLUMN] + pd.offsets.MonthEnd(1)

    pares = dados_ordenados.loc[
        data_futura.eq(proximo_mes) & dados_ordenados[DENOMINATOR_COLUMN].gt(0)
    ].copy()
    if pares.empty:
        raise ValueError(
            "Não há snapshots mensais consecutivos para formar alvos de treinamento."
        )

    pares[TARGET_COLUMN] = (
        atraso_90_futuro.loc[pares.index] / pares[DENOMINATOR_COLUMN]
    )
    pares[TARGET_DATE_COLUMN] = data_futura.loc[pares.index]
    pares[SAMPLE_WEIGHT_COLUMN] = pares[DENOMINATOR_COLUMN].astype(float)
    pares["idade_coorte_meses"] = (
        (pares[DATE_COLUMN].dt.year - pares["Coorte"].dt.year) * 12
        + pares[DATE_COLUMN].dt.month
        - pares["Coorte"].dt.month
    )
    pares["mes_acompanhamento"] = pares[DATE_COLUMN].dt.month

    if not pares[TARGET_COLUMN].between(0, 1).all():
        raise ValueError(
            "A taxa futura de atraso excede o intervalo esperado de 0 a 1."
        )
    return pares.reset_index(drop=True)


def _calcular_metricas(
    y_true: pd.Series,
    y_pred: np.ndarray,
    pesos: pd.Series,
) -> dict[str, float]:
    return {
        "MAE_ponderado": float(mean_absolute_error(y_true, y_pred, sample_weight=pesos)),
        "RMSE_ponderado": float(
            np.sqrt(mean_squared_error(y_true, y_pred, sample_weight=pesos))
        ),
        "R2_ponderado": float(r2_score(y_true, y_pred, sample_weight=pesos)),
        "MAE_por_segmento": float(mean_absolute_error(y_true, y_pred)),
    }


def treinar_e_avaliar(dados: pd.DataFrame) -> dict[str, Any]:
    """Treina no histórico e avalia em datas-alvo posteriores ao corte temporal."""
    amostras = construir_amostras_supervisionadas(dados)
    treino = amostras[TARGET_DATE_COLUMN] <= CUTOFF_TARGET_DATE
    teste = amostras[TARGET_DATE_COLUMN] > CUTOFF_TARGET_DATE
    if not treino.any() or not teste.any():
        raise ValueError(
            "A divisão temporal exige amostras-alvo antes e depois de "
            f"{CUTOFF_TARGET_DATE.date()}."
        )

    colunas_categoricas = CATEGORICAL_FEATURES
    colunas_numericas = NUMERIC_FEATURES
    preprocessor = ColumnTransformer(
        transformers=[
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), colunas_categoricas),
            ("numericas", "passthrough", colunas_numericas),
        ]
    )
    modelo = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=250,
                    max_features=0.8,
                    min_samples_leaf=4,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    X = amostras[FEATURE_COLUMNS]
    y = amostras[TARGET_COLUMN]
    pesos = amostras[SAMPLE_WEIGHT_COLUMN]
    modelo.fit(
        X.loc[treino],
        y.loc[treino],
        regressor__sample_weight=pesos.loc[treino],
    )
    previsoes = modelo.predict(X.loc[teste])
    previsao_baseline = (
        amostras.loc[teste, "Qtd_Atraso_90_dias"]
        / amostras.loc[teste, DENOMINATOR_COLUMN]
    ).to_numpy()

    datas_alvo = amostras.loc[teste, TARGET_DATE_COLUMN]
    metricas = {
        "objetivo": (
            "Prever a contagem de operações com atraso de 90 dias no mês seguinte, "
            "normalizada pelo número de operações conhecido na data da previsão."
        ),
        "corte_temporal": str(CUTOFF_TARGET_DATE.date()),
        "linhas_treino": int(treino.sum()),
        "linhas_teste": int(teste.sum()),
        "datas_alvo_treino": sorted(
            amostras.loc[treino, TARGET_DATE_COLUMN].dt.strftime("%Y-%m-%d").unique().tolist()
        ),
        "datas_alvo_teste": sorted(datas_alvo.dt.strftime("%Y-%m-%d").unique().tolist()),
        "metricas_modelo": _calcular_metricas(
            y.loc[teste], previsoes, pesos.loc[teste]
        ),
        "metricas_baseline_mes_anterior": _calcular_metricas(
            y.loc[teste], previsao_baseline, pesos.loc[teste]
        ),
        "modelo_supera_baseline_mae_ponderado": bool(
            mean_absolute_error(y.loc[teste], previsoes, sample_weight=pesos.loc[teste])
            < mean_absolute_error(
                y.loc[teste], previsao_baseline, sample_weight=pesos.loc[teste]
            )
        ),
        "artefato_aprovado_para_uso": bool(
            mean_absolute_error(y.loc[teste], previsoes, sample_weight=pesos.loc[teste])
            < mean_absolute_error(
                y.loc[teste], previsao_baseline, sample_weight=pesos.loc[teste]
            )
        ),
        "features": FEATURE_COLUMNS,
        "fontes_coorte": [caminho.name for caminho in INPUT_PATHS],
        "fontes_contextuais_nao_integradas": {
            MACROECONOMIC_WORKBOOK: (
                "Indicadores macroeconômicos agregados não foram unidos às coortes: "
                "há somente dois meses-alvo no treino, insuficientes para avaliar "
                "com segurança o efeito temporal desses indicadores."
            )
        },
        "observacao": (
            "Modelo agregado de carteira; não é compatível com a API de risco "
            "individual de cartão de crédito."
        ),
    }
    return {"modelo": modelo, "metricas": metricas}


def executar_pipeline_treinamento_coorte() -> dict[str, Any]:
    """Treina, avalia e salva os artefatos exclusivos das coortes."""
    dados = carregar_dados_coorte()
    resultado = treinar_e_avaliar(dados)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    aprovado = resultado["metricas"]["artefato_aprovado_para_uso"]
    if aprovado:
        joblib.dump(resultado["modelo"], MODEL_PATH)
    with METRICS_PATH.open("w", encoding="utf-8") as arquivo:
        json.dump(resultado["metricas"], arquivo, indent=2, ensure_ascii=False)

    metricas_modelo = resultado["metricas"]["metricas_modelo"]
    metricas_baseline = resultado["metricas"]["metricas_baseline_mes_anterior"]
    if aprovado:
        print(f"Modelo agregado aprovado e salvo em: {MODEL_PATH}")
    else:
        print(
            "Candidato não salvo: o baseline do mês anterior teve menor "
            "MAE ponderado na avaliação temporal."
        )
    print(f"Métricas salvas em: {METRICS_PATH}")
    print(
        "MAE ponderado: "
        f"modelo={metricas_modelo['MAE_ponderado']:.6f}, "
        f"baseline={metricas_baseline['MAE_ponderado']:.6f}"
    )
    return resultado


if __name__ == "__main__":
    executar_pipeline_treinamento_coorte()
