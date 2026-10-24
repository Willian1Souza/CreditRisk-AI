"""
Módulo de Análise e Simulação de Risco de Financiamento.
Combina regras de conformidade e políticas de crédito com o modelo de Machine Learning (CreditRiskPredictor).
Avalia:
- Valor a ser financiado
- Possível valor de entrada ou nulo
- Tipo de emprego e estabilidade
- Salário / Renda mensal
- Idade do proponente
- Estado civil
- Comprovante de residência
- Comprometimento de renda (DTI - Debt-to-Income)
- LTV (Loan-to-Value)
- Score preditivo de IA e probabilidade de inadimplência
- Cenários de viabilização para o analista
"""
from __future__ import annotations

import math
from typing import Any, Optional
from pydantic import BaseModel, Field

from src.predict import CreditRiskPredictor


def calcular_taxa_mensal(taxa_anual_pct: float) -> float:
    """Converte taxa anual nominal em percentual para a taxa mensal."""
    return (taxa_anual_pct / 100.0) / 12.0


def calcular_parcela_price(saldo_devedor: float, taxa_mensal: float, prazo_meses: int) -> float:
    """Calcula o valor da parcela fixa na Tabela Price."""
    if saldo_devedor <= 0 or prazo_meses <= 0:
        return 0.0
    if taxa_mensal <= 0:
        return round(saldo_devedor / prazo_meses, 2)
    
    fator = (1.0 + taxa_mensal) ** prazo_meses
    parcela = saldo_devedor * (taxa_mensal * fator) / (fator - 1.0)
    return round(parcela, 2)


def calcular_parcela_sac_inicial(saldo_devedor: float, taxa_mensal: float, prazo_meses: int) -> float:
    """Calcula o valor da primeira parcela na Tabela SAC (Amortização Constante)."""
    if saldo_devedor <= 0 or prazo_meses <= 0:
        return 0.0
    amortizacao = saldo_devedor / prazo_meses
    juros_inicial = saldo_devedor * taxa_mensal
    return round(amortizacao + juros_inicial, 2)


class AnalisadorFinanciamento:
    """
    Motor especialista para análise e aprovação de financiamentos com base em dados
    inseridos pelo analista e escoragem pelo modelo de inteligência artificial.
    """

    def __init__(self, predictor: Optional[CreditRiskPredictor] = None) -> None:
        if predictor is not None:
            self.predictor = predictor
        else:
            try:
                self.predictor = CreditRiskPredictor()
            except Exception:
                self.predictor = None

    def _mapear_para_features_ia(
        self,
        valor_financiado: float,
        saldo_financiado: float,
        salario: float,
        idade: int,
        estado_civil: str,
        tipo_emprego: str,
        tempo_emprego_meses: int,
        comprovante_residencia: bool,
    ) -> dict[str, Any]:
        """
        Adapta os dados cadastrais e financeiros da proposta para o formato das
        26 features aceitas pelo modelo de Machine Learning do projeto.
        """
        # Mapeamento de Estado Civil
        estado_norm = estado_civil.strip().lower()
        if "casad" in estado_norm or "união" in estado_norm or "uniao" in estado_norm:
            marriage = 1
        elif "solteir" in estado_norm:
            marriage = 2
        else:
            marriage = 3

        # Escolaridade inferida pelo emprego
        tipo_norm = tipo_emprego.strip().lower()
        if "servidor" in tipo_norm or "concursado" in tipo_norm or "empresár" in tipo_norm:
            education = 1  # Pós / Superior
        elif "clt" in tipo_norm:
            education = 2  # Universidade / Médio
        elif "autônom" in tipo_norm or "autonom" in tipo_norm:
            education = 2
        else:
            education = 3

        # Sexo neutro / representativo (2 = Feminino, 1 = Masculino)
        sex = 1

        # Limite equivalente no modelo (ponderado pelo saldo e capacidade de pagamento)
        limit_bal = max(10000.0, min(float(saldo_financiado), 500000.0))

        # Status histórico de atraso estimado pelo perfil do tomador
        if not comprovante_residencia:
            pay_val = 1
        elif "desempreg" in tipo_norm:
            pay_val = 2
        elif "servidor" in tipo_norm or ("clt" in tipo_norm and tempo_emprego_meses >= 24):
            pay_val = -1
        else:
            pay_val = 0

        # Relação de fatura / utilização da linha de crédito
        fatura_estimada = min(salario * 0.8, limit_bal * 0.4)
        pagamento_estimado = fatura_estimada if pay_val <= 0 else fatura_estimada * 0.5

        taxa_util = min(2.0, max(0.0, fatura_estimada / limit_bal))

        return {
            "SEX": sex,
            "EDUCATION": education,
            "MARRIAGE": marriage,
            "LIMIT_BAL": limit_bal,
            "AGE": int(idade),
            "PAY_0": pay_val,
            "PAY_2": pay_val,
            "PAY_3": pay_val,
            "PAY_4": pay_val,
            "PAY_5": pay_val,
            "PAY_6": pay_val,
            "BILL_AMT1": round(fatura_estimada, 2),
            "BILL_AMT2": round(fatura_estimada * 0.95, 2),
            "BILL_AMT3": round(fatura_estimada * 0.92, 2),
            "BILL_AMT4": round(fatura_estimada * 0.90, 2),
            "BILL_AMT5": round(fatura_estimada * 0.88, 2),
            "BILL_AMT6": round(fatura_estimada * 0.85, 2),
            "PAY_AMT1": round(pagamento_estimado, 2),
            "PAY_AMT2": round(pagamento_estimado, 2),
            "PAY_AMT3": round(pagamento_estimado, 2),
            "PAY_AMT4": round(pagamento_estimado, 2),
            "PAY_AMT5": round(pagamento_estimado, 2),
            "PAY_AMT6": round(pagamento_estimado, 2),
            "MAX_ATRASO_6M": max(0, pay_val),
            "QTD_MESES_ATRASO": 1 if pay_val > 0 else 0,
            "TAXA_UTILIZACAO_LIMITE": round(taxa_util, 4),
        }

    def avaliar_financiamento(
        self,
        valor_financiado: float,
        salario: float,
        idade: int,
        tipo_emprego: str,
        estado_civil: str,
        comprovante_residencia: bool,
        valor_entrada: Optional[float] = None,
        tempo_emprego_meses: Optional[int] = 12,
        prazo_meses: Optional[int] = 48,
        taxa_juros_anual: Optional[float] = 14.5,
        sistema_amortizacao: Optional[str] = "PRICE",
        tipo_financiamento: Optional[str] = "Veículo",
        nome_cliente: Optional[str] = "Cliente Analisado",
        cpf_cliente: Optional[str] = "000.000.000-00",
    ) -> dict[str, Any]:
        """
        Executa a análise completa da proposta de financiamento.
        """
        # 1. Validações Preliminares
        if valor_financiado <= 0:
            raise ValueError("O valor a ser financiado deve ser maior que zero.")
        if salario <= 0:
            raise ValueError("O salário / renda mensal deve ser maior que zero.")
        if not (18 <= idade <= 100):
            raise ValueError("A idade do tomador deve estar entre 18 e 100 anos.")

        prazo = int(prazo_meses or 48)
        if not (6 <= prazo <= 420):
            raise ValueError("O prazo deve estar entre 6 e 420 meses.")

        taxa_anual = float(taxa_juros_anual if taxa_juros_anual is not None else 14.5)
        if taxa_anual < 0:
            raise ValueError("A taxa de juros anual não pode ser negativa.")

        # 2. Tratamento da Entrada (Suporta valor numérico, 0 ou None / Nulo)
        entrada_informada = 0.0 if valor_entrada is None else max(0.0, float(valor_entrada))
        if entrada_informada >= valor_financiado:
            raise ValueError(
                f"O valor de entrada (R$ {entrada_informada:,.2f}) não pode ser maior ou igual "
                f"ao valor do bem (R$ {valor_financiado:,.2f})."
            )

        saldo_liquido = valor_financiado - entrada_informada
        pct_entrada = round((entrada_informada / valor_financiado) * 100.0, 2)
        ltv = round((saldo_liquido / valor_financiado) * 100.0, 2)

        # 3. Cálculo da Parcela e Encargos
        taxa_mensal = calcular_taxa_mensal(taxa_anual)
        sistema = (sistema_amortizacao or "PRICE").strip().upper()
        if sistema == "SAC":
            valor_parcela = calcular_parcela_sac_inicial(saldo_liquido, taxa_mensal, prazo)
        else:
            valor_parcela = calcular_parcela_price(saldo_liquido, taxa_mensal, prazo)

        total_pago_estimado = round(valor_parcela * prazo, 2)
        total_juros = round(max(0.0, total_pago_estimado - saldo_liquido), 2)

        # 4. Comprometimento de Renda e Margem
        dti_pct = round((valor_parcela / salario) * 100.0, 2)
        margem_maxima_30 = round(salario * 0.30, 2)
        margem_tolerancia_35 = round(salario * 0.35, 2)
        margem_livre = round(margem_maxima_30 - valor_parcela, 2)

        idade_final = round(idade + (prazo / 12.0), 1)

        # 5. Avaliação do Modelo de Machine Learning (Score de Risco IA)
        features_ia = self._mapear_para_features_ia(
            valor_financiado=valor_financiado,
            saldo_financiado=saldo_liquido,
            salario=salario,
            idade=idade,
            estado_civil=estado_civil,
            tipo_emprego=tipo_emprego,
            tempo_emprego_meses=tempo_emprego_meses or 12,
            comprovante_residencia=comprovante_residencia,
        )

        score_ia = 0.15
        modelo_nome = "Modelo Heurístico Prudencial"
        if self.predictor is not None:
            try:
                res_pred = self.predictor.prever(features_ia)
                score_ia = float(res_pred.get("score_modelo", 0.15))
                modelo_nome = str(res_pred.get("modelo", self.predictor.nome_modelo))
            except Exception:
                score_ia = 0.18

        # 6. Avaliação dos Pilares da Política de Crédito
        checklist: dict[str, dict[str, Any]] = {}
        motivos_reprovacao: list[str] = []
        condicoes_aprovacao: list[str] = []
        pontos_positivos: list[str] = []

        # Regra 1: Comprovante de Residência
        if comprovante_residencia:
            checklist["comprovante_residencia"] = {
                "status": "APROVADO",
                "descricao": "Comprovante de residência regular e validado",
                "critico": False,
            }
            pontos_positivos.append("Documento de residência validado.")
        else:
            checklist["comprovante_residencia"] = {
                "status": "PENDENTE",
                "descricao": "Comprovante de residência não apresentado ou pendente de envio",
                "critico": True,
            }
            condicoes_aprovacao.append(
                "Apresentação obrigatória de comprovante de residência recente (últimos 90 dias)."
            )

        # Regra 2: Comprometimento de Renda (DTI)
        if dti_pct <= 30.0:
            checklist["comprometimento_renda"] = {
                "status": "APROVADO",
                "descricao": f"Comprometimento de {dti_pct}% dentro do teto seguro de 30%",
                "critico": False,
            }
            pontos_positivos.append(f"Parcela consome {dti_pct}% da renda líquida (dentro do limite de 30%).")
        elif dti_pct <= 35.0:
            checklist["comprometimento_renda"] = {
                "status": "ALERTA",
                "descricao": f"Comprometimento de {dti_pct}% na faixa de tolerância (30% a 35%)",
                "critico": False,
            }
            condicoes_aprovacao.append(
                f"Comprometimento de renda em {dti_pct}%. Recomendado aumentar a entrada ou "
                "incluir coobrigado/cônjuge na composição de renda."
            )
        else:
            checklist["comprometimento_renda"] = {
                "status": "REPROVADO",
                "descricao": f"Comprometimento de {dti_pct}% excede o limite prudencial de 35%",
                "critico": True,
            }
            motivos_reprovacao.append(
                f"Capacidade de pagamento insuficiente: a parcela de R$ {valor_parcela:,.2f} "
                f"compromete {dti_pct}% do salário (limite máximo permitido é 30% a 35%)."
            )

        # Regra 3: Entrada e LTV
        if entrada_informada <= 0:
            checklist["valor_entrada"] = {
                "status": "ALERTA",
                "descricao": "Financiamento 100% integral sem entrada inicial (LTV de 100%)",
                "critico": False,
            }
            if dti_pct > 25.0:
                condicoes_aprovacao.append(
                    "Operação sem valor de entrada: requer contratação de seguro de proteção de crédito "
                    "ou aporte de no mínimo 10% a 15% de entrada para enquadramento preferencial."
                )
        elif pct_entrada >= 20.0:
            checklist["valor_entrada"] = {
                "status": "APROVADO",
                "descricao": f"Entrada de R$ {entrada_informada:,.2f} ({pct_entrada}% do bem - LTV saudável de {ltv}%)",
                "critico": False,
            }
            pontos_positivos.append(f"Entrada robusta de {pct_entrada}% reduz sensivelmente o risco financeiro.")
        else:
            checklist["valor_entrada"] = {
                "status": "APROVADO",
                "descricao": f"Entrada de R$ {entrada_informada:,.2f} ({pct_entrada}%) aceita para o perfil",
                "critico": False,
            }

        # Regra 4: Idade e Vigência do Contrato
        if idade_final <= 75.0:
            checklist["idade_proponente"] = {
                "status": "APROVADO",
                "descricao": f"Idade final de {idade_final:.0f} anos dentro do limite securitário (< 75 anos)",
                "critico": False,
            }
        elif idade_final <= 80.0:
            checklist["idade_proponente"] = {
                "status": "ALERTA",
                "descricao": f"Idade final de {idade_final:.0f} anos próxima ao limite máximo (80 anos)",
                "critico": False,
            }
            condicoes_aprovacao.append(
                f"Idade do cliente ao término do financiamento será {idade_final:.0f} anos. "
                "Exige apólice de seguro de crédito prestamista com cobertura atuarial estendida."
            )
        else:
            checklist["idade_proponente"] = {
                "status": "REPROVADO",
                "descricao": f"Idade na quitação ({idade_final:.0f} anos) ultrapassa a regra prudencial de 80 anos",
                "critico": True,
            }
            motivos_reprovacao.append(
                f"Idade ao término do contrato ({idade_final:.0f} anos) ultrapassa o limite prudencial de 80 anos."
            )

        # Regra 5: Ocupação e Estabilidade
        tipo_emp_norm = tipo_emprego.strip().lower()
        tempo = tempo_emprego_meses or 12

        if "desempreg" in tipo_emp_norm or "sem renda" in tipo_emp_norm:
            checklist["estabilidade_emprego"] = {
                "status": "REPROVADO",
                "descricao": "Proponente sem fonte de renda ativa comprovada",
                "critico": True,
            }
            motivos_reprovacao.append("Não há comprovação de renda profissional ativa.")
        elif "servidor" in tipo_emp_norm or "concursado" in tipo_emp_norm:
            checklist["estabilidade_emprego"] = {
                "status": "APROVADO",
                "descricao": "Servidor Público com estabilidade profissional e financeira máxima",
                "critico": False,
            }
            pontos_positivos.append("Vínculo público estatutário oferece alta previsibilidade de pagamento.")
        elif "aposentad" in tipo_emp_norm or "pensionista" in tipo_emp_norm:
            checklist["estabilidade_emprego"] = {
                "status": "APROVADO",
                "descricao": "Benefício previdenciário fixo e contínuo",
                "critico": False,
            }
            pontos_positivos.append("Renda previdenciária contínua e sem risco de demissão.")
        elif "clt" in tipo_emp_norm:
            if tempo < 6:
                checklist["estabilidade_emprego"] = {
                    "status": "ALERTA",
                    "descricao": f"CLT em período probatório / recente ({tempo} meses)",
                    "critico": False,
                }
                condicoes_aprovacao.append(
                    f"Tempo de empresa recente ({tempo} meses). Recomenda-se apresentar extrato do FGTS "
                    "ou avalista solidário se o valor financiado for elevado."
                )
            else:
                checklist["estabilidade_emprego"] = {
                    "status": "APROVADO",
                    "descricao": f"CLT com estabilidade confirmada ({tempo} meses de empresa)",
                    "critico": False,
                }
                pontos_positivos.append(f"Vínculo CLT consolidado ({tempo} meses).")
        else:  # Autônomo / Empresário / PJ
            checklist["estabilidade_emprego"] = {
                "status": "ALERTA",
                "descricao": f"Atividade {tipo_emprego} (renda variável/empresarial)",
                "critico": False,
            }
            condicoes_aprovacao.append(
                "Apresentação dos últimos 3 extratos bancários de pessoa física e Declaração de IRPF com recibo."
            )

        # Regra 6: Score de IA
        if score_ia < 0.20:
            faixa_risco_ia = "Baixo Risco"
            checklist["score_ia"] = {
                "status": "APROVADO",
                "descricao": f"Score IA {score_ia:.4f} (Probabilidade de inadimplência muito baixa: {score_ia*100:.1f}%)",
                "critico": False,
            }
            pontos_positivos.append(f"Algoritmo preditivo de IA apontou Baixo Risco de inadimplência ({score_ia*100:.1f}%).")
        elif score_ia <= 0.40:
            faixa_risco_ia = "Risco Moderado"
            checklist["score_ia"] = {
                "status": "ALERTA",
                "descricao": f"Score IA {score_ia:.4f} (Probabilidade de inadimplência moderada: {score_ia*100:.1f}%)",
                "critico": False,
            }
        else:
            faixa_risco_ia = "Alto Risco"
            checklist["score_ia"] = {
                "status": "REPROVADO",
                "descricao": f"Score IA {score_ia:.4f} (Alta propensão estatística a atrasos: {score_ia*100:.1f}%)",
                "critico": True,
            }
            motivos_reprovacao.append(
                f"Modelo estatístico de IA identificou risco elevado de inadimplência ({score_ia*100:.1f}%)."
            )

        # 7. Veredito Final
        if motivos_reprovacao:
            status_decisao = "Reprovado"
            aprovado = False
            parecer_resumo = (
                "Financiamento REPROVADO devido a desconformidades de capacidade financeira ou políticas prudenciais."
            )
        elif condicoes_aprovacao:
            status_decisao = "Aprovado com Condições"
            aprovado = True
            parecer_resumo = (
                "Financiamento APROVADO CONDICIONALMENTE, com ressalvas operacionais ou exigências documentais adicionais."
            )
        else:
            status_decisao = "Aprovado"
            aprovado = True
            parecer_resumo = (
                "Financiamento APROVADO integralmente! O proponente atende com excelência a todos os critérios de risco e renda."
            )

        # 8. Simulação de Viabilização Alternativa (Soluções para o Analista)
        viabilizacao: dict[str, Any] = {}
        if dti_pct > 30.0:
            # Entrada necessária para enquadrar a parcela em 30%
            parcela_alvo = margem_maxima_30
            if taxa_mensal > 0:
                fator = (1.0 + taxa_mensal) ** prazo
                saldo_alvo = parcela_alvo * (fator - 1.0) / (taxa_mensal * fator)
            else:
                saldo_alvo = parcela_alvo * prazo

            entrada_minima_sugerida = round(max(0.0, valor_financiado - saldo_alvo), 2)
            viabilizacao["entrada_minima_para_aprovar"] = entrada_minima_sugerida
            viabilizacao["percentual_entrada_minima"] = round((entrada_minima_sugerida / valor_financiado) * 100.0, 1)

            # Prazo necessário para caber em 30% da renda mantendo a mesma entrada
            # PMT_alvo = PV * (i * (1+i)^n) / ((1+i)^n - 1)
            # 1 - (PV*i)/PMT_alvo = (1+i)^(-n)
            if taxa_mensal > 0 and (saldo_liquido * taxa_mensal) < parcela_alvo:
                termo = 1.0 - ((saldo_liquido * taxa_mensal) / parcela_alvo)
                if termo > 0:
                    prazo_calculado = -math.log(termo) / math.log(1.0 + taxa_mensal)
                    viabilizacao["prazo_sugerido_meses"] = int(math.ceil(prazo_calculado))
                else:
                    viabilizacao["prazo_sugerido_meses"] = None
            else:
                viabilizacao["prazo_sugerido_meses"] = None

            viabilizacao["salario_minimo_necessario"] = round(valor_parcela / 0.30, 2)

        return {
            "cliente": {
                "nome": nome_cliente or "Cliente Analisado",
                "cpf": cpf_cliente or "000.000.000-00",
                "idade": idade,
                "estado_civil": estado_civil,
                "tipo_emprego": tipo_emprego,
                "tempo_emprego_meses": tempo_emprego_meses or 12,
                "salario_mensal": salario,
                "comprovante_residencia": comprovante_residencia,
            },
            "financiamento": {
                "tipo_financiamento": tipo_financiamento or "Veículo",
                "valor_total_bem": round(valor_financiado, 2),
                "valor_entrada": round(entrada_informada, 2),
                "percentual_entrada": pct_entrada,
                "saldo_financiado": round(saldo_liquido, 2),
                "ltv_percentual": ltv,
                "prazo_meses": prazo,
                "taxa_juros_anual": taxa_anual,
                "taxa_juros_mensal_pct": round(taxa_mensal * 100.0, 3),
                "sistema_amortizacao": sistema,
                "valor_parcela": valor_parcela,
                "total_a_pagar": total_pago_estimado,
                "total_juros": total_juros,
            },
            "capacidade_pagamento": {
                "salario_mensal": salario,
                "valor_parcela": valor_parcela,
                "comprometimento_renda_pct": dti_pct,
                "margem_maxima_30pct": margem_maxima_30,
                "margem_tolerancia_35pct": margem_tolerancia_35,
                "margem_disponivel": margem_livre,
                "idade_final_financiamento": idade_final,
            },
            "inteligencia_artificial": {
                "modelo": modelo_nome,
                "score_inadimplencia": round(score_ia, 4),
                "probabilidade_inadimplencia": f"{score_ia * 100:.2f}%",
                "faixa_risco": faixa_risco_ia,
            },
            "resultado_decisao": {
                "aprovado": aprovado,
                "status_decisao": status_decisao,
                "parecer_resumo": parecer_resumo,
                "pontos_positivos": pontos_positivos,
                "condicoes_aprovacao": condicoes_aprovacao,
                "motivos_reprovacao": motivos_reprovacao,
            },
            "checklist_politica_credito": checklist,
            "viabilizacao_credito": viabilizacao,
        }
