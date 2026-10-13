from typing import Any

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
DERIVED_FEATURES = {
    "MAX_ATRASO_6M",
    "QTD_MESES_ATRASO",
    "TAXA_UTILIZACAO_LIMITE",
}
PAYMENT_FEATURES = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
FEATURES = [
    "SEX",
    "EDUCATION",
    "MARRIAGE",
    "LIMIT_BAL",
    "AGE",
    *PAYMENT_FEATURES,
    *(f"BILL_AMT{month}" for month in range(1, 7)),
    *(f"PAY_AMT{month}" for month in range(1, 7)),
    "MAX_ATRASO_6M",
    "QTD_MESES_ATRASO",
    "TAXA_UTILIZACAO_LIMITE",
]
PAYMENT_STATUSES = list(range(-2, 10))

st.set_page_config(
    page_title="CreditRisk AI",
    page_icon="📊",
    layout="wide",
)

st.title("📊 CreditRisk AI")
st.write("Sistema inteligente de análise de risco de crédito")


@st.cache_data(ttl=30)
def carregar_info_api() -> dict[str, Any]:
    response = requests.get(f"{API_URL}/model/info", timeout=10)
    response.raise_for_status()
    return response.json()


try:
    info = carregar_info_api()
    features = info.get("features_esperadas", info.get("features_entrada", info.get("features", [])))
    modelo = info.get("modelo", info.get("melhor_modelo", "Não informado"))

    if not features:
        st.error("A API não retornou as variáveis do modelo.")
        st.stop()
    if features != FEATURES:
        st.error("As variáveis disponibilizadas pela API não correspondem ao formulário.")
        st.stop()

    st.success("API conectada com sucesso!")
    st.caption(f"Modelo: {modelo} | Variáveis: {len(features)}")

except requests.RequestException as erro:
    st.error(f"Erro ao consultar a API: {erro}")
    st.stop()
except (AttributeError, TypeError, ValueError) as erro:
    st.error(f"Erro ao interpretar as informações da API: {erro}")
    st.stop()

meses = {
    "PAY_0": "Setembro",
    "PAY_2": "Agosto",
    "PAY_3": "Julho",
    "PAY_4": "Junho",
    "PAY_5": "Maio",
    "PAY_6": "Abril",
}

with st.form("formulario_credito"):
    st.subheader("👤 Dados do cliente")
    col_dados, col_demograficos = st.columns(2)

    with col_dados:
        limite = st.number_input(
            "Limite de crédito",
            min_value=0.01,
            value=50000.0,
            step=1000.0,
            format="%.2f",
        )
        idade = st.number_input(
            "Idade",
            min_value=18,
            max_value=120,
            value=35,
            step=1,
        )

    with col_demograficos:
        sexo = st.selectbox(
            "Sexo",
            options=[1, 2],
            format_func=lambda valor: {1: "Masculino", 2: "Feminino"}[valor],
        )
        escolaridade = st.selectbox(
            "Escolaridade",
            options=[1, 2, 3, 4],
            format_func=lambda valor: {
                1: "Pós-graduação",
                2: "Universidade",
                3: "Ensino médio",
                4: "Outros",
            }[valor],
        )
        estado_civil = st.selectbox(
            "Estado civil",
            options=[1, 2, 3],
            format_func=lambda valor: {
                1: "Casado(a)",
                2: "Solteiro(a)",
                3: "Outros",
            }[valor],
        )

    st.divider()
    st.subheader("📅 Histórico de pagamentos")
    st.caption("Informe a situação de pagamento de cada um dos últimos seis meses.")
    colunas_atrasos = st.columns(3)
    atrasos: dict[str, int] = {}
    for indice, feature in enumerate(PAYMENT_FEATURES):
        with colunas_atrasos[indice % 3]:
            atrasos[feature] = st.selectbox(
                f"Situação em {meses[feature]}",
                options=PAYMENT_STATUSES,
                index=PAYMENT_STATUSES.index(0),
                format_func=lambda valor: (
                    f"{valor} - {valor} mês(es) de atraso"
                    if valor > 0
                    else {
                        -2: "-2 - sem uso",
                        -1: "-1 - pagamento em dia",
                        0: "0 - pagamento mínimo/rotativo",
                    }[valor]
                ),
            )

    st.divider()
    st.subheader("💰 Informações financeiras")
    col_faturas, col_pagamentos = st.columns(2)
    faturas: dict[str, float] = {}
    pagamentos: dict[str, float] = {}

    with col_faturas:
        st.markdown("**Valores das faturas**")
        for month in range(1, 7):
            faturas[f"BILL_AMT{month}"] = st.number_input(
                f"Fatura do mês {month}",
                value=1000.0,
                step=100.0,
                format="%.2f",
            )

    with col_pagamentos:
        st.markdown("**Valores pagos**")
        for month in range(1, 7):
            pagamentos[f"PAY_AMT{month}"] = st.number_input(
                f"Pagamento do mês {month}",
                min_value=0.0,
                value=100.0,
                step=100.0,
                format="%.2f",
            )

    enviar = st.form_submit_button(
        "🔍 Analisar risco de crédito",
        type="primary",
        width="stretch",
    )

if enviar:
    dados: dict[str, int | float] = {
        "SEX": sexo,
        "EDUCATION": escolaridade,
        "MARRIAGE": estado_civil,
        "LIMIT_BAL": limite,
        "AGE": idade,
        **atrasos,
        **faturas,
        **pagamentos,
    }
    dados["MAX_ATRASO_6M"] = max(atrasos.values())
    dados["QTD_MESES_ATRASO"] = sum(valor > 0 for valor in atrasos.values())
    dados["TAXA_UTILIZACAO_LIMITE"] = round(
        max(0.0, min(faturas["BILL_AMT1"] / limite, 2.0)),
        4,
    )

    faltantes = set(features) - set(dados)
    extras = set(dados) - set(features)
    if faltantes or extras:
        st.error("Incompatibilidade entre o formulário e o modelo.")
        if faltantes:
            st.write("Variáveis faltantes:", sorted(faltantes))
        if extras:
            st.write("Variáveis extras:", sorted(extras))
        st.stop()

    dados_ordenados = {feature: dados[feature] for feature in features}

    with st.spinner("Analisando risco de crédito..."):
        try:
            response = requests.post(
                f"{API_URL}/predict",
                json={"dados": dados_ordenados},
                timeout=30,
            )
            response.raise_for_status()
            resultado = response.json()

            st.subheader("📈 Resultado da análise")
            st.json(resultado)

        except requests.HTTPError as erro:
            resposta = erro.response
            if resposta is None:
                st.error(f"Erro na previsão: {erro}")
            else:
                try:
                    corpo = resposta.json()
                except ValueError:
                    st.error(f"Erro na previsão: {resposta.text or erro}")
                else:
                    detalhes = corpo.get("detalhes")
                    if isinstance(detalhes, list):
                        mensagens = [
                            f"{item.get('campo', 'dados')}: {item.get('mensagem', '')}"
                            for item in detalhes
                        ]
                        st.error("\n".join(mensagens))
                    else:
                        st.error(str(corpo.get("detail", corpo.get("mensagem", erro))))
        except requests.RequestException as erro:
            st.error(f"Erro na previsão: {erro}")
        except ValueError as erro:
            st.error(f"Resposta inválida da API: {erro}")

    with st.expander("Visualizar dados enviados ao modelo"):
        st.json(dados_ordenados)
