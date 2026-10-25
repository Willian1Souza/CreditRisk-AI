from __future__ import annotations

from api.main import analyze, compare_scenarios, predict, predict_batch, predictor
from api.schemas import (
    AnaliseCompletaRequest,
    BatchClientesRequest,
    ClienteInput,
    SimuladorCenariosRequest,
)


CLIENTE_EXEMPLO = {
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
}


def test_credit_score_is_inverse_probability_on_a_0_to_1000_scale():
    assert predictor.calcular_score_credito(0)["score"] == 1000
    assert predictor.calcular_score_credito(0.25)["score"] == 750
    assert predictor.calcular_score_credito(1)["score"] == 0


def test_financial_diagnosis_does_not_invent_income():
    dados = {**CLIENTE_EXEMPLO, "MAX_ATRASO_6M": 2, "QTD_MESES_ATRASO": 2, "TAXA_UTILIZACAO_LIMITE": 0.6}
    diagnostico = predictor.gerar_diagnostico_financeiro(dados)

    assert diagnostico["comprometimento_renda"]["dti_percentual"] is None
    assert diagnostico["comprometimento_renda"]["renda_considerada"] is None


def test_predict_and_batch_include_credit_scores():
    single = predict(ClienteInput(**CLIENTE_EXEMPLO))
    batch = predict_batch(BatchClientesRequest(clientes=[ClienteInput(**CLIENTE_EXEMPLO)]))

    assert single.score_credito is not None
    assert 0 <= single.score_credito.score <= 1000
    assert 0 <= batch.previsoes[0].score_credito.score <= 1000


def test_complete_analysis_returns_diagnosis_and_shap_explanation():
    resultado = analyze(
        AnaliseCompletaRequest(
            cliente=ClienteInput(**CLIENTE_EXEMPLO),
            renda_mensal=4500,
        )
    )

    assert 0 <= resultado.score_credito.score <= 1000
    assert resultado.diagnostico_financeiro["comprometimento_renda"]["dti_percentual"] is not None
    assert resultado.explicabilidade_shap.top_fatores_risco is not None
    assert resultado.explicabilidade_shap.top_fatores_protecao is not None


def test_scenario_comparison_returns_both_predictions_and_deltas():
    cenario_simulado = {
        **CLIENTE_EXEMPLO,
        "PAY_0": 0,
        "PAY_2": 0,
        "BILL_AMT1": 10000,
    }

    resultado = compare_scenarios(
        SimuladorCenariosRequest(
            cenario_base=ClienteInput(**CLIENTE_EXEMPLO),
            cenario_simulado=ClienteInput(**cenario_simulado),
            renda_base=4500,
            renda_simulada=4500,
        )
    )

    assert resultado.cenario_base.score_credito.score >= 0
    assert resultado.cenario_simulado.score_credito.score >= 0
    assert isinstance(resultado.comparativo.delta_score, int)
