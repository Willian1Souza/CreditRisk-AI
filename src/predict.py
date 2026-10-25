from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Union

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "models" / "best_credit_risk_model.joblib"
METRICS_PATH = BASE_DIR / "models" / "metrics_summary.json"

MAPA_NOMES_FEATURES: dict[str, tuple[str, str]] = {
    "num__PAY_0": ("Atraso Recente (Setembro)", "Histórico de pagamento da última fatura"),
    "num__PAY_2": ("Atraso em Agosto", "Histórico de pagamento há 2 meses"),
    "num__PAY_3": ("Atraso em Julho", "Histórico de pagamento há 3 meses"),
    "num__PAY_4": ("Atraso em Junho", "Histórico de pagamento há 4 meses"),
    "num__PAY_5": ("Atraso em Maio", "Histórico de pagamento há 5 meses"),
    "num__PAY_6": ("Atraso em Abril", "Histórico de pagamento há 6 meses"),
    "num__MAX_ATRASO_6M": ("Pior Atraso em 6 Meses", "Máximo de meses em atraso nos últimos 6 meses"),
    "num__QTD_MESES_ATRASO": ("Frequência de Atrasos", "Quantidade de meses com atraso no período"),
    "num__TAXA_UTILIZACAO_LIMITE": ("Uso do Limite de Crédito", "Percentual utilizado do limite total"),
    "num__LIMIT_BAL": ("Limite Total do Cartão", "Valor total de limite concedido"),
    "num__AGE": ("Idade do Titular", "Faixa etária do titular"),
    "num__BILL_AMT1": ("Fatura Recente (Setembro)", "Valor da última fatura"),
    "num__BILL_AMT2": ("Fatura de Agosto", "Valor da fatura de 2 meses atrás"),
    "num__BILL_AMT3": ("Fatura de Julho", "Valor da fatura de 3 meses atrás"),
    "num__BILL_AMT4": ("Fatura de Junho", "Valor da fatura de 4 meses atrás"),
    "num__BILL_AMT5": ("Fatura de Maio", "Valor da fatura de 5 meses atrás"),
    "num__BILL_AMT6": ("Fatura de Abril", "Valor da fatura de 6 meses atrás"),
    "num__PAY_AMT1": ("Pagamento em Setembro", "Valor pago na última fatura"),
    "num__PAY_AMT2": ("Pagamento em Agosto", "Valor pago na fatura anterior"),
    "num__PAY_AMT3": ("Pagamento em Julho", "Valor pago há 3 meses"),
    "num__PAY_AMT4": ("Pagamento em Junho", "Valor pago há 4 meses"),
    "num__PAY_AMT5": ("Pagamento em Maio", "Valor pago há 5 meses"),
    "num__PAY_AMT6": ("Pagamento em Abril", "Valor pago há 6 meses"),
    "cat__SEX_2": ("Gênero (Feminino)", "Gênero do titular"),
    "cat__EDUCATION_2": ("Escolaridade (Universidade)", "Nível superior de instrução"),
    "cat__EDUCATION_3": ("Escolaridade (Ensino Médio)", "Nível médio de instrução"),
    "cat__EDUCATION_4": ("Escolaridade (Outros)", "Outras escolaridades"),
    "cat__MARRIAGE_2": ("Estado Civil (Solteiro)", "Estado civil solteiro"),
    "cat__MARRIAGE_3": ("Estado Civil (Outros)", "Outro estado civil"),
}


class CreditRiskPredictor:
    modelo: Any
    features: list[str]
    nome_modelo: str
    metricas: dict[str, Any]
    _explainer: Any
    _preprocessor: Any
    _classifier: Any

    def __init__(self) -> None:
        self.modelo = joblib.load(MODEL_PATH)

        with open(METRICS_PATH, encoding="utf-8") as arquivo:
            metadata = json.load(arquivo)

        self.features = list(metadata["features_entrada"])
        self.nome_modelo = str(metadata["melhor_modelo"])
        self.metricas = dict(metadata.get("metricas", {}))
        self._explainer = None

        if hasattr(self.modelo, "named_steps"):
            self._preprocessor = self.modelo.named_steps.get("preprocessor")
            self._classifier = self.modelo.named_steps.get("classifier")
        else:
            self._preprocessor = None
            self._classifier = self.modelo

    def _garantir_explainer(self) -> None:
        if self._explainer is None:
            import shap
            if self._classifier is not None:
                self._explainer = shap.TreeExplainer(self._classifier)
            else:
                self._explainer = shap.Explainer(self.modelo)

    def prever(self, dados_cliente: dict[str, Any]) -> dict[str, Any]:
        faltantes = set(self.features) - set(dados_cliente)
        extras = set(dados_cliente) - set(self.features)

        if faltantes or extras:
            raise ValueError(
                f"Features ausentes: {sorted(faltantes)}. "
                f"Features inesperadas: {sorted(extras)}"
            )

        cliente = pd.DataFrame([dados_cliente], columns=self.features)
        probabilidade = float(self.modelo.predict_proba(cliente)[0][1])

        return {
            "modelo": self.nome_modelo,
            "score_modelo": round(probabilidade, 4),
            "classe_predita": int(self.modelo.predict(cliente)[0]),
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
                "classe_predita": int(pred),
            })
        return resultados

    # =========================================================================
    # 1. SCORE DE RISCO DE CRÉDITO (0 a 1000)
    # =========================================================================
    def calcular_score_credito(self, probabilidade: float) -> dict[str, Any]:
        """
        Inverte linearmente a probabilidade prevista: 0 para probabilidade 1 e 1000 para 0.
        A pontuação é própria deste modelo e não equivale a score de birô.
        """
        prob_clamped = max(0.0, min(1.0, float(probabilidade)))
        score = int(round((1.0 - prob_clamped) * 1000))
        score = max(0, min(1000, score))

        if score >= 800:
            faixa = "Excelente"
            rating = "A"
            cor = "#059669"  # emerald-600
            nivel = "Muito Baixo Risco"
            descricao = "A menor probabilidade estimada de inadimplência corresponde a esta faixa de score."
        elif score >= 650:
            faixa = "Bom"
            rating = "B"
            cor = "#10b981"  # emerald-500
            nivel = "Baixo Risco"
            descricao = "A probabilidade estimada de inadimplência corresponde a uma faixa de risco relativamente baixa."
        elif score >= 500:
            faixa = "Regular"
            rating = "C"
            cor = "#f59e0b"  # amber-500
            nivel = "Risco Moderado"
            descricao = "A probabilidade estimada de inadimplência corresponde a uma faixa intermediária de risco."
        elif score >= 350:
            faixa = "Ruim"
            rating = "D"
            cor = "#f97316"  # orange-500
            nivel = "Alto Risco"
            descricao = "A probabilidade estimada de inadimplência corresponde a uma faixa elevada de risco."
        else:
            faixa = "Crítico"
            rating = "E"
            cor = "#e11d48"  # rose-600
            nivel = "Risco Severo"
            descricao = "A probabilidade estimada de inadimplência corresponde à faixa mais alta de risco."

        return {
            "score": score,
            "faixa": faixa,
            "rating": rating,
            "cor": cor,
            "nivel_risco": nivel,
            "descricao": descricao,
            "probabilidade_inadimplencia": f"{prob_clamped * 100:.2f}%",
            "percentual_seguranca": f"{(1.0 - prob_clamped) * 100:.2f}%",
        }

    # =========================================================================
    # 2. DIAGNÓSTICO FINANCEIRO PESSOAL
    # =========================================================================
    def gerar_diagnostico_financeiro(
        self,
        dados_cliente: dict[str, Any],
        renda_mensal: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Analisa endividamento, utilização do limite de crédito e comprometimento da renda.
        Gera métricas detalhadas de estresse financeiro e recomendações personalizadas.
        """
        limit_bal = float(dados_cliente.get("LIMIT_BAL", 10000))
        bill1 = float(dados_cliente.get("BILL_AMT1", 0))
        bill2 = float(dados_cliente.get("BILL_AMT2", 0))
        pay1 = float(dados_cliente.get("PAY_AMT1", 0))

        # 1. Utilização de Limite
        taxa_util = float(dados_cliente.get("TAXA_UTILIZACAO_LIMITE", bill1 / max(1.0, limit_bal)))
        pct_util = round(taxa_util * 100.0, 1)

        if pct_util <= 30.0:
            status_util = "Excelente"
            cor_util = "emerald"
            msg_util = f"Uso prudente do limite ({pct_util}%). A utilização abaixo de 30% é uma referência comum de gestão do limite."
        elif pct_util <= 60.0:
            status_util = "Moderado"
            cor_util = "blue"
            msg_util = f"Utilização em {pct_util}%. Nível aceitável, mas evite acumular novas faturas."
        elif pct_util <= 85.0:
            status_util = "Alerta"
            cor_util = "amber"
            msg_util = f"Utilização elevada ({pct_util}%). Alto consumo do limite sinaliza aperto de liquidez."
        else:
            status_util = "Crítico"
            cor_util = "rose"
            msg_util = f"Limite quase esgotado ({pct_util}%). Forte correlação estatística com risco de atraso."

        # 2. Comprometimento de Renda (DTI)
        renda = float(renda_mensal) if renda_mensal is not None and renda_mensal > 0 else None
        saldo_fatura = max(0.0, bill1)
        dti = round((saldo_fatura / renda) * 100.0, 1) if renda is not None else None

        if dti is None:
            status_dti = "Não informado"
            cor_dti = "gray"
            msg_dti = "Informe a renda mensal para calcular o comprometimento da renda."
        elif dti <= 20.0:
            status_dti = "Excelente"
            cor_dti = "emerald"
            msg_dti = f"A fatura consome {dti}% da renda. Ampla margem de segurança financeira."
        elif dti <= 30.0:
            status_dti = "Saudável"
            cor_dti = "blue"
            msg_dti = f"Fatura consome {dti}% da renda, dentro do teto prudencial bancário (30%)."
        elif dti <= 35.0:
            status_dti = "Atenção"
            cor_dti = "amber"
            msg_dti = f"Comprometimento de {dti}% na faixa de tolerância. Margem vulnerável a imprevistos."
        else:
            status_dti = "Crítico"
            cor_dti = "rose"
            msg_dti = f"Superendividamento: fatura compromete {dti}% da renda (limite máximo seguro é 30%)."

        # 3. Índice de Cobertura de Fatura
        saldo_fatura_anterior = max(0.0, bill2)
        if saldo_fatura_anterior > 0:
            pct_cobertura = round((pay1 / saldo_fatura_anterior) * 100.0, 1)
        else:
            pct_cobertura = 100.0

        if pct_cobertura >= 100.0:
            status_cobertura = "Pagamento Integral"
            rotativo = False
            msg_cobertura = "O pagamento informado cobre o valor da fatura anterior nesta estimativa."
        elif pct_cobertura >= 50.0:
            status_cobertura = "Pagamento Parcial"
            rotativo = True
            msg_cobertura = f"Pagou {pct_cobertura}% da fatura anterior. Saldo rolado no rotativo (juros caros)."
        else:
            status_cobertura = "Pagamento Mínimo ou Insuficiente"
            rotativo = True
            msg_cobertura = f"Pagamento de apenas {pct_cobertura}%. Risco agudo de endividamento em bola de neve."

        # 4. Tendência das Faturas
        faturas_recentes = [float(dados_cliente.get(f"BILL_AMT{i}", 0)) for i in range(1, 4)]
        faturas_anteriores = [float(dados_cliente.get(f"BILL_AMT{i}", 0)) for i in range(4, 7)]
        media_recente = sum(faturas_recentes) / 3.0
        media_anterior = sum(faturas_anteriores) / 3.0

        if media_recente > media_anterior * 1.15:
            tendencia = "Em Expansão"
            msg_tendencia = "Saldo devedor médio aumentou nos últimos 3 meses."
        elif media_recente < media_anterior * 0.85:
            tendencia = "Em Redução"
            msg_tendencia = "Endividamento em queda progressiva nos últimos meses (ótimo sinal!)."
        else:
            tendencia = "Estável"
            msg_tendencia = "Saldo devedor mantido em patamar estável no período."

        # 5. Nível de Estresse Financeiro (0 a 100)
        pontos_estresse = 0
        if pct_util > 80: pontos_estresse += 35
        elif pct_util > 50: pontos_estresse += 20
        elif pct_util > 30: pontos_estresse += 10

        if dti is not None:
            if dti > 35: pontos_estresse += 35
            elif dti > 30: pontos_estresse += 20
            elif dti > 20: pontos_estresse += 10

        max_atraso = int(dados_cliente.get("MAX_ATRASO_6M", 0))
        if max_atraso >= 2: pontos_estresse += 30
        elif max_atraso == 1: pontos_estresse += 15

        if rotativo: pontos_estresse += 15
        estresse_score = min(100, pontos_estresse)

        # 6. Recomendações personalizadas
        recomendacoes = []
        if pct_util > 40.0:
            alvo_30 = round(limit_bal * 0.30, 2)
            reducao_necessaria = round(max(0.0, bill1 - alvo_30), 2)
            recomendacoes.append(
                f"Reduza o saldo da fatura em R$ {reducao_necessaria:,.2f} para manter a utilização abaixo de 30% do limite."
            )
        if rotativo:
            recomendacoes.append(
                "Evite o crédito rotativo sempre que possível: suas taxas costumam ser elevadas. Confira as condições do emissor."
            )
        if max_atraso > 0:
            recomendacoes.append(
                "Mantenha pagamentos rigorosamente em dia por pelo menos 3 a 6 meses consecutivos para recuperar o histórico positivo."
            )
        if dti is not None and dti > 30.0:
            recomendacoes.append(
                "O comprometimento de renda está acima de 30%. Considere renegociar dívidas mais caras ou estender prazos."
            )
        if not recomendacoes:
            recomendacoes.append(
                "Mantenha os pagamentos em dia e monitore o uso do limite para preservar sua saúde financeira."
            )

        return {
            "utilizacao_limite": {
                "percentual": pct_util,
                "limite_total": limit_bal,
                "fatura_atual": bill1,
                "status": status_util,
                "cor": cor_util,
                "mensagem": msg_util,
            },
            "comprometimento_renda": {
                "dti_percentual": dti,
                "renda_considerada": renda,
                "status": status_dti,
                "cor": cor_dti,
                "mensagem": msg_dti,
            },
            "cobertura_pagamento": {
                "percentual_coberto": pct_cobertura,
                "status": status_cobertura,
                "uso_rotativo": rotativo,
                "mensagem": msg_cobertura,
            },
            "tendencia_divida": {
                "tendencia": tendencia,
                "media_recente": round(media_recente, 2),
                "media_anterior": round(media_anterior, 2),
                "mensagem": msg_tendencia,
            },
            "estresse_financeiro": {
                "indice": estresse_score,
                "nivel": "Baixo" if estresse_score < 35 else ("Moderado" if estresse_score < 70 else "Crítico"),
                "cor": "#059669" if estresse_score < 35 else ("#f59e0b" if estresse_score < 70 else "#e11d48"),
            },
            "recomendacoes": recomendacoes,
        }

    # =========================================================================
    # 3. EXPLICABILIDADE COM SHAP (TreeExplainer)
    # =========================================================================
    def explicar_predicao_shap(
        self,
        dados_cliente: dict[str, Any],
        top_n: int = 6,
    ) -> dict[str, Any]:
        """
        Calcula os valores SHAP exatos para a predição via TreeExplainer no modelo Random Forest.
        Revela quais variáveis mais aumentaram ou diminuíram a probabilidade de inadimplência.
        """
        if top_n < 1:
            raise ValueError("'top_n' deve ser maior que zero.")
        faltantes = set(self.features) - set(dados_cliente)
        extras = set(dados_cliente) - set(self.features)
        if faltantes or extras:
            raise ValueError(
                f"Features ausentes: {sorted(faltantes)}. "
                f"Features inesperadas: {sorted(extras)}"
            )

        self._garantir_explainer()
        cliente_df = pd.DataFrame([dados_cliente], columns=self.features)
        if self._preprocessor is not None:
            X_trans = self._preprocessor.transform(cliente_df)
            feature_names = self._preprocessor.get_feature_names_out()
        else:
            X_trans = cliente_df
            feature_names = np.asarray(self.features)

        shap_values = self._explainer.shap_values(X_trans)
        if isinstance(shap_values, list):
            shap_classe_default = np.asarray(
                shap_values[1] if len(shap_values) > 1 else shap_values[0]
            )[0]
        else:
            shap_array = np.asarray(shap_values)
            if shap_array.ndim == 3:
                shap_classe_default = shap_array[0, :, 1]
            elif shap_array.ndim == 2:
                shap_classe_default = shap_array[0]
            else:
                raise ValueError(
                    f"Formato de valores SHAP não suportado: {shap_array.shape}."
                )

        if len(feature_names) != len(shap_classe_default):
            raise ValueError(
                "O número de valores SHAP não corresponde às features transformadas."
            )

        valor_base_array = np.asarray(self._explainer.expected_value).reshape(-1)
        valor_base = float(
            valor_base_array[1] if len(valor_base_array) > 1 else valor_base_array[0]
        )

        fatores = []
        for name, val in zip(feature_names, shap_classe_default):
            val_float = float(val)
            info_nome, desc = MAPA_NOMES_FEATURES.get(name, (name, name))
            fatores.append({
                "feature_codigo": name,
                "nome": info_nome,
                "descricao": desc,
                "impacto": round(val_float, 4),
                "direcao": "Aumenta Risco" if val_float > 0 else "Protege / Reduz Risco",
                "tipo": "negativo" if val_float > 0 else "positivo",
                "impacto_score_pontos": int(round(-val_float * 1000)),
            })

        fatores_ordenados = sorted(fatores, key=lambda x: abs(x["impacto"]), reverse=True)
        fatores_que_aumentam_risco = [f for f in fatores_ordenados if f["impacto"] > 0][:top_n]
        fatores_que_reduzem_risco = [f for f in fatores_ordenados if f["impacto"] < 0][:top_n]

        return {
            "valor_base_modelo": round(valor_base, 4),
            "score_base_modelo": int(round((1.0 - valor_base) * 1000)),
            "top_fatores_risco": fatores_que_aumentam_risco,
            "top_fatores_protecao": fatores_que_reduzem_risco,
            "todos_fatores": fatores_ordenados[:top_n * 2],
        }

    # =========================================================================
    # 4. SIMULADOR DE CENÁRIOS COM IA
    # =========================================================================
    def simular_cenarios(
        self,
        cenario_base: dict[str, Any],
        cenario_simulado: dict[str, Any],
        renda_base: Optional[float] = None,
        renda_simulada: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Executa predição, cálculo de score e diagnóstico para dois cenários e compara os deltas.
        """
        res_base = self.prever(cenario_base)
        score_base = self.calcular_score_credito(res_base["score_modelo"])
        diag_base = self.gerar_diagnostico_financeiro(cenario_base, renda_base)

        res_sim = self.prever(cenario_simulado)
        score_sim = self.calcular_score_credito(res_sim["score_modelo"])
        diag_sim = self.gerar_diagnostico_financeiro(cenario_simulado, renda_simulada)

        delta_score = score_sim["score"] - score_base["score"]
        delta_prob = round((res_sim["score_modelo"] - res_base["score_modelo"]) * 100.0, 2)
        delta_util = round(diag_sim["utilizacao_limite"]["percentual"] - diag_base["utilizacao_limite"]["percentual"], 1)

        if delta_score > 50:
            impacto_geral = "Melhoria Expressiva"
            resumo = f"O cenário simulado aumenta seu score em {delta_score} pontos; a probabilidade prevista de inadimplência varia {delta_prob:+.2f} pontos percentuais."
        elif delta_score > 0:
            impacto_geral = "Melhoria Leve"
            resumo = f"O cenário traz um ganho de {delta_score} pontos no score; a probabilidade prevista de inadimplência varia {delta_prob:+.2f} pontos percentuais."
        elif delta_score == 0:
            impacto_geral = "Sem Alteração"
            resumo = f"As alterações mantiveram a pontuação; a probabilidade prevista de inadimplência varia {delta_prob:+.2f} pontos percentuais."
        else:
            impacto_geral = "Piora de Risco"
            resumo = f"Atenção: o cenário reduz seu score em {abs(delta_score)} pontos; a probabilidade prevista de inadimplência varia {delta_prob:+.2f} pontos percentuais."

        return {
            "cenario_base": {
                "previsao": res_base,
                "score_credito": score_base,
                "diagnostico": diag_base,
            },
            "cenario_simulado": {
                "previsao": res_sim,
                "score_credito": score_sim,
                "diagnostico": diag_sim,
            },
            "comparativo": {
                "delta_score": delta_score,
                "delta_probabilidade_pct": delta_prob,
                "delta_utilizacao_pct": delta_util,
                "impacto_geral": impacto_geral,
                "resumo": resumo,
                "mudou_rating": score_base["rating"] != score_sim["rating"],
                "rating_anterior": score_base["rating"],
                "rating_novo": score_sim["rating"],
            },
        }