"""
Testes unitários e de integração para a análise e simulação de financiamento.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.financiamento import (
    AnalisadorFinanciamento,
    calcular_taxa_mensal,
    calcular_parcela_price,
    calcular_parcela_sac_inicial
)
from api.main import app
from api.schemas import FinanciamentoInput


def test_calculos_financeiros_basicos():
    # Taxa anual de 14.5% -> mensal ~1.134%
    i = calcular_taxa_mensal(14.5)
    assert 0.011 < i < 0.012

    # Parcela de 80.000 em 48 meses a ~1.134% a.m.
    pmt = calcular_parcela_price(80000, i, 48)
    assert 2100 < pmt < 2300

    # SAC: primeira parcela maior que a Price
    sac_ini = calcular_parcela_sac_inicial(80000, i, 48)
    assert sac_ini > pmt


def test_financiamento_aprovado_perfil_solido():
    analisador = AnalisadorFinanciamento()
    res = analisador.avaliar_financiamento(
        valor_financiado=100000,
        valor_entrada=30000,  # 30% de entrada
        salario=12000,
        idade=34,
        tipo_emprego="Servidor Público",
        estado_civil="Casado",
        comprovante_residencia=True,
        prazo_meses=48,
    )

    assert res["resultado_decisao"]["aprovado"] is True
    assert res["resultado_decisao"]["status_decisao"] == "Aprovado"
    assert res["financiamento"]["saldo_financiado"] == 70000.0
    assert res["financiamento"]["percentual_entrada"] == 30.0
    assert res["capacidade_pagamento"]["comprometimento_renda_pct"] <= 30.0
    assert res["checklist_politica_credito"]["comprovante_residencia"]["status"] == "APROVADO"


def test_financiamento_entrada_nula():
    analisador = AnalisadorFinanciamento()
    res = analisador.avaliar_financiamento(
        valor_financiado=60000,
        valor_entrada=None,  # Entrada nula (100% financiado)
        salario=9000,
        idade=29,
        tipo_emprego="CLT",
        tempo_emprego_meses=36,
        estado_civil="Solteiro",
        comprovante_residencia=True,
        prazo_meses=48,
    )

    assert res["financiamento"]["valor_entrada"] == 0.0
    assert res["financiamento"]["saldo_financiado"] == 60000.0
    assert res["financiamento"]["ltv_percentual"] == 100.0
    # Com renda suficiente (DTI ~18%), pode ser aprovado ou aprovado com condições
    assert res["resultado_decisao"]["aprovado"] is True


def test_financiamento_reprovado_por_renda_insuficiente():
    analisador = AnalisadorFinanciamento()
    res = analisador.avaliar_financiamento(
        valor_financiado=120000,
        valor_entrada=10000,
        salario=3500,  # Parcela será ~3000 -> DTI ~85%
        idade=40,
        tipo_emprego="Autônomo",
        estado_civil="Divorciado",
        comprovante_residencia=True,
        prazo_meses=48,
    )

    assert res["resultado_decisao"]["aprovado"] is False
    assert res["resultado_decisao"]["status_decisao"] == "Reprovado"
    assert len(res["resultado_decisao"]["motivos_reprovacao"]) > 0
    # Deve calcular cenários de viabilização
    assert "entrada_minima_para_aprovar" in res["viabilizacao_credito"]
    assert res["viabilizacao_credito"]["salario_minimo_necessario"] > 3500


def test_financiamento_pendente_sem_comprovante_residencia():
    analisador = AnalisadorFinanciamento()
    res = analisador.avaliar_financiamento(
        valor_financiado=50000,
        valor_entrada=15000,
        salario=10000,
        idade=28,
        tipo_emprego="CLT",
        estado_civil="Solteiro",
        comprovante_residencia=False,  # Sem comprovante
    )

    # Não deve ter aprovação limpa direta
    assert res["resultado_decisao"]["status_decisao"] in ("Aprovado com Condições", "Reprovado")
    assert res["checklist_politica_credito"]["comprovante_residencia"]["status"] == "PENDENTE"


def test_api_endpoint_financiamento():
    from api.main import analisar_financiamento_endpoint

    payload = FinanciamentoInput(
        valor_financiado=80000,
        valor_entrada=20000,
        salario=7500,
        idade=32,
        tipo_emprego="CLT",
        estado_civil="Casado",
        comprovante_residencia=True,
        prazo_meses=48
    )

    dados = analisar_financiamento_endpoint(payload)
    assert "resultado_decisao" in dados
    assert "financiamento" in dados
    assert "capacidade_pagamento" in dados
    assert dados["financiamento"]["saldo_financiado"] == 60000.0
    assert dados["resultado_decisao"]["status_decisao"] in ("Aprovado", "Aprovado com Condições")


if __name__ == "__main__":
    test_calculos_financeiros_basicos()
    test_financiamento_aprovado_perfil_solido()
    test_financiamento_entrada_nula()
    test_financiamento_reprovado_por_renda_insuficiente()
    test_financiamento_pendente_sem_comprovante_residencia()
    test_api_endpoint_financiamento()
    print(">>> TODOS OS TESTES DE FINANCIAMENTO PASSARAM COM SUCESSO! <<<")
