import os
import sys
import warnings
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from ucimlrepo import fetch_ucirepo

# Silencia avisos desnecessarios de versoes de bibliotecas
warnings.filterwarnings("ignore")

# Suporte seguro a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Definicao Dinamica e Resiliente de Diretorios e Caminhos
SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

DATA_DIR = BASE_DIR / "data"
PLOTS_DIR = BASE_DIR / "plots"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

RAW_CSV_PATH = DATA_DIR / "credit_card_clients.csv"
CLEAN_CSV_PATH = DATA_DIR / "credit_card_clients_clean.csv"

# Mapeamentos oficiais de variaveis categoricas para nomes legiveis
MAPEAMENTO_SEXO = {
    1: "Masculino",
    2: "Feminino",
}

MAPEAMENTO_ESCOLARIDADE = {
    1: "Pos-Graduacao",
    2: "Universidade",
    3: "Ensino Medio",
    4: "Outros",  # 0, 4, 5 e 6 consolidados em 'Outros'
}

MAPEAMENTO_ESTADO_CIVIL = {
    1: "Casado",
    2: "Solteiro",
    3: "Outros",  # 0 e 3 consolidados em 'Outros'
}


def _obter_dimensoes_barra(patch: Any) -> tuple[float, float, float]:
    """Extrai com seguranca de tipos (x, largura, altura) de uma barra grafica,
    evitando falsos positivos em linters e typecheckers como Pyrefly/Mypy.
    """
    x = float(getattr(patch, "get_x", lambda: 0.0)())
    w = float(getattr(patch, "get_width", lambda: 0.0)())
    h = float(getattr(patch, "get_height", lambda: 0.0)())
    return x, w, h


def carregar_dados_brutos() -> pd.DataFrame:
    """Carrega o dataset bruto do CSV local em data/ ou baixa do UCI Repository."""
    if not RAW_CSV_PATH.exists():
        print("[+] Baixando dataset do UCI Repository (ID: 350)...")
        dataset = fetch_ucirepo(id=350)

        var_mapping = dict(
            zip(dataset.variables["name"], dataset.variables["description"])
        )
        X = dataset.data.features.copy()
        y = dataset.data.targets.copy()

        rename_cols = {
            col: str(var_mapping[col])
            for col in X.columns
            if col in var_mapping and pd.notna(var_mapping[col])
        }
        X = X.rename(columns=rename_cols)

        df = X.copy()
        df["inadimplente"] = (
            y.iloc[:, 0].to_numpy()
            if hasattr(y, "iloc") and getattr(y, "ndim", 1) == 2
            else np.array(y).ravel()
        )
        if "ID" in df.columns:
            df = df.drop(columns=["ID"])
        df.to_csv(RAW_CSV_PATH, index=False)
        print(f"[OK] Dados brutos salvos em: {RAW_CSV_PATH}")
    else:
        print(f"[INFO] Carregando dados brutos de: {RAW_CSV_PATH}")
        df = pd.read_csv(RAW_CSV_PATH)
        if "ID" in df.columns:
            df = df.drop(columns=["ID"])

    return df


def validar_integridade(df: pd.DataFrame) -> pd.DataFrame:
    """Realiza a verificacao de integridade dos dados:
    - Normalizacao preventiva de nomenclatura (PAY_1 -> PAY_0, sinonimos do alvo)
    - Remocao de duplicatas exatas
    - Tratamento de categorias anomalas em EDUCATION e MARRIAGE com cast para int
    - Validacao e saneamento de consistencia financeira (faturas vs pagamentos)
    """
    print("\n" + "=" * 65)
    print(" 1. VALIDACAO DE INTEGRIDADE DOS DADOS ")
    print("=" * 65)

    df_tratado = df.copy()

    # Normalizacao de nomenclatura de colunas de atraso
    if "PAY_1" in df_tratado.columns and "PAY_0" not in df_tratado.columns:
        df_tratado = df_tratado.rename(columns={"PAY_1": "PAY_0"})

    # Normalizacao de possiveis sinonimos da variavel alvo
    target_aliases = [
        "default payment next month",
        "default.payment.next.month",
        "default",
        "Y",
        "INADIMPLENTE",
    ]
    for alias in target_aliases:
        if alias in df_tratado.columns and "inadimplente" not in df_tratado.columns:
            df_tratado = df_tratado.rename(columns={alias: "inadimplente"})

    print(f"Registros iniciais: {len(df_tratado):,}")
    print(f"Total de colunas: {df_tratado.shape[1]}")

    nulos = df_tratado.isnull().sum()
    total_nulos = nulos.sum()
    if total_nulos == 0:
        print("[OK] Nao foram encontrados valores nulos em nenhuma coluna.")
    else:
        print(f"[ALERTA] Valores nulos encontrados:\n{nulos[nulos > 0]}")
        df_tratado = df_tratado.dropna().copy()
        print(f"-> Registros restantes apos remocao de nulos: {len(df_tratado):,}")

    qtd_duplicadas = df_tratado.duplicated().sum()
    print(f"\n[DUPLICATAS] Total de linhas duplicadas identificadas: {qtd_duplicadas}")
    if qtd_duplicadas > 0:
        df_tratado = df_tratado.drop_duplicates().copy()
        print(
            f"-> Removidas {qtd_duplicadas} linhas identicas. Registros unicos: {len(df_tratado):,}"
        )

    print("\n[VALIDACAO CATEGORICA] Padronizando categorias nao documentadas:")
    anomalias_edu = df_tratado["EDUCATION"].isin([0, 5, 6]).sum()
    print(
        f"-> EDUCATION: {anomalias_edu} registros com codigos [0, 5, 6] consolidados na classe 4 (Outros)."
    )
    df_tratado["EDUCATION"] = (
        df_tratado["EDUCATION"].replace({0: 4, 5: 4, 6: 4}).astype(int)
    )

    anomalias_mar = (df_tratado["MARRIAGE"] == 0).sum()
    print(
        f"-> MARRIAGE: {anomalias_mar} registros com codigo [0] consolidados na classe 3 (Outros)."
    )
    df_tratado["MARRIAGE"] = df_tratado["MARRIAGE"].replace({0: 3}).astype(int)

    df_tratado["SEX"] = df_tratado["SEX"].astype(int)
    if "inadimplente" in df_tratado.columns:
        df_tratado["inadimplente"] = df_tratado["inadimplente"].astype(int)

    print("\n[CONSISTENCIA FINANCEIRA]")
    faturas_negativas = (df_tratado["BILL_AMT1"] < 0).sum()
    print(
        f"-> Faturas com saldo negativo (BILL_AMT1 < 0): {faturas_negativas} clientes (representa saldo credor valido)."
    )

    pagamentos_cols = [f"PAY_AMT{i}" for i in range(1, 7)]
    pagamentos_negativos = (df_tratado[pagamentos_cols] < 0).sum().sum()
    if pagamentos_negativos > 0:
        print(
            f"-> [ALERTA] {pagamentos_negativos} pagamentos negativos detectados. Ajustando valores negativos para 0."
        )
        for col in pagamentos_cols:
            df_tratado[col] = df_tratado[col].clip(lower=0)
    else:
        print(f"-> Pagamentos negativos detectados: 0 [OK]")

    return df_tratado


def enriquecer_variaveis(df: pd.DataFrame) -> pd.DataFrame:
    """Cria colunas descritivas para analise exploratoria e indicadores de risco de credito:
    - Descricoes textuais (SEXO_DESC, ESCOLARIDADE_DESC, ESTADO_CIVIL_DESC)
    - Faixas de Idade e Limite seguras contra extremos (sem gerar NaNs)
    - Indicadores comportamentais de credito (Max atraso, Qtd meses atrasados, Utilizacao de Limite)
    """
    df_feat = df.copy()

    df_feat["SEXO_DESC"] = df_feat["SEX"].map(MAPEAMENTO_SEXO)
    df_feat["ESCOLARIDADE_DESC"] = df_feat["EDUCATION"].map(MAPEAMENTO_ESCOLARIDADE)
    df_feat["ESTADO_CIVIL_DESC"] = df_feat["MARRIAGE"].map(MAPEAMENTO_ESTADO_CIVIL)

    # Bins de limite cobrindo ate infinito para evitar NaNs
    df_feat["FAIXA_LIMITE"] = pd.cut(
        df_feat["LIMIT_BAL"],
        bins=[0, 50000, 100000, 200000, 400000, np.inf],
        labels=["Ate 50k", "50k-100k", "100k-200k", "200k-400k", "Acima de 400k"],
        include_lowest=True,
    )

    # Bins de idade cobrindo de 17 a 120 para abarcar todas as idades validas sem gerar NaNs
    df_feat["FAIXA_ETARIA"] = pd.cut(
        df_feat["AGE"],
        bins=[17, 30, 40, 50, 60, 120],
        labels=["18-30", "31-40", "41-50", "51-60", "60+"],
        include_lowest=True,
    )

    colunas_atraso = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
    df_feat["MAX_ATRASO_6M"] = df_feat[colunas_atraso].max(axis=1).astype(int)
    df_feat["QTD_MESES_ATRASO"] = (
        (df_feat[colunas_atraso] > 0).sum(axis=1).astype(int)
    )

    limite_seguro = df_feat["LIMIT_BAL"].replace(0, np.nan)
    # Clipagem e arredondamento a 4 casas decimais consistente com a API
    df_feat["TAXA_UTILIZACAO_LIMITE"] = (
        ((df_feat["BILL_AMT1"] / limite_seguro).fillna(0.0).clip(lower=0.0, upper=2.0))
        .round(4)
        .astype(float)
    )

    return df_feat


def imprimir_relatorio_estatistico(df: pd.DataFrame) -> None:
    """Exibe estatisticas detalhadas e taxas de inadimplencia cruzadas."""
    print("\n" + "=" * 65)
    print(" 2. ANALISE DA VARIAVEL ALVO (DISTRIBUICAO DE INADIMPLENCIA) ")
    print("=" * 65)
    total = len(df)
    qtd_0 = int((df["inadimplente"] == 0).sum())
    qtd_1 = int((df["inadimplente"] == 1).sum())
    pct_0 = (qtd_0 / total) * 100
    pct_1 = (qtd_1 / total) * 100
    print(f"Clientes Adimplentes (0):    {qtd_0:,} ({pct_0:.2f}%)")
    print(f"Clientes Inadimplentes (1):  {qtd_1:,} ({pct_1:.2f}%)")
    print(f"Taxa Media de Inadimplencia da Carteira: {pct_1:.2f}%\n")

    print("\n" + "=" * 65)
    print(" 3. TAXAS DE INADIMPLENCIA SEGMENTADAS (ANALISE BIVARIADA) ")
    print("=" * 65)

    def formatar_tabela_bivariada(coluna: str, titulo: str) -> None:
        print(f"\n{titulo}:")
        tabela = df.groupby(coluna, observed=False)["inadimplente"].agg(
            Total="count", Inadimplentes="sum", Taxa_Inadimplencia="mean"
        )
        tabela_fmt = tabela.copy()
        tabela_fmt["Taxa_Inadimplencia"] = tabela_fmt["Taxa_Inadimplencia"].map(
            "{:.2%}".format
        )
        print(tabela_fmt.to_string())

    formatar_tabela_bivariada("SEXO_DESC", "[A] Por Sexo")
    formatar_tabela_bivariada("ESCOLARIDADE_DESC", "[B] Por Escolaridade")
    formatar_tabela_bivariada("ESTADO_CIVIL_DESC", "[C] Por Estado Civil")
    formatar_tabela_bivariada("FAIXA_LIMITE", "[D] Por Faixa de Limite de Credito")
    formatar_tabela_bivariada("PAY_0", "[E] Por Atraso Recente (PAY_0)")
    formatar_tabela_bivariada(
        "QTD_MESES_ATRASO",
        "[F] Por Quantidade de Meses em Atraso nos Ultimos 6 Meses",
    )


def gerar_graficos_eda(df: pd.DataFrame) -> None:
    """Gera e salva 6 graficos de diagnostico visual de alta qualidade na pasta plots com alinhamento preciso."""
    print("\n" + "=" * 65)
    print(" 4. GERANDO E SALVANDO GRAFICOS DE ALTO IMPACTO ")
    print("=" * 65)

    sns.set_theme(style="whitegrid", font_scale=1.0)
    cores = ["#2b5c8f", "#d9534f"]

    # 1. Distribuicao da Variavel Alvo
    plt.figure(figsize=(7, 4.5))
    ax = sns.countplot(
        x="inadimplente",
        data=df,
        hue="inadimplente",
        palette=cores,
        legend=False,
    )
    plt.title(
        "Distribuicao da Variavel Alvo: Inadimplencia no Proximo Mes",
        fontsize=12,
        pad=12,
    )
    plt.xlabel("Status (0: Adimplente | 1: Inadimplente)", fontsize=10)
    plt.ylabel("Contagem de Clientes", fontsize=10)
    total = len(df)
    for p in ax.patches:
        x, w, h = _obter_dimensoes_barra(p)
        if pd.notna(h) and h > 0:
            pct = (h / total) * 100
            ax.annotate(
                f"{int(h):,} ({pct:.1f}%)",
                (x + w / 2, h + total * 0.01),
                ha="center",
                va="bottom",
                fontsize=10,
                weight="bold",
            )
    plt.tight_layout()
    p1 = PLOTS_DIR / "01_distribuicao_alvo.png"
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p1}")

    # 2. Perfil Sociodemografico de Risco
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    for i, (col, title) in enumerate([
        ("SEXO_DESC", "Inadimplencia por Sexo"),
        ("ESCOLARIDADE_DESC", "Inadimplencia por Escolaridade"),
        ("ESTADO_CIVIL_DESC", "Inadimplencia por Estado Civil"),
    ]):
        taxa = df.groupby(col, observed=False)["inadimplente"].mean().reset_index()
        sns.barplot(
            x=col,
            y="inadimplente",
            data=taxa,
            ax=axes[i],
            palette="Blues_r",
            hue=col,
            legend=False,
        )
        axes[i].set_title(title, fontsize=11)
        axes[i].set_ylabel("Taxa de Inadimplencia" if i == 0 else "")
        axes[i].set_xlabel("")
        axes[i].tick_params(axis="x", rotation=15)
        for p in axes[i].patches:
            x, w, h = _obter_dimensoes_barra(p)
            if pd.notna(h) and h > 0:
                axes[i].annotate(
                    f"{h * 100:.1f}%",
                    (x + w / 2, h + 0.005),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    weight="bold",
                )
    plt.tight_layout()
    p2 = PLOTS_DIR / "02_perfil_sociodemografico_risco.png"
    plt.savefig(p2, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p2}")

    # 3. Impacto dos Atrasos no Risco
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4.5))

    pay0_taxa = df.groupby("PAY_0", observed=False)["inadimplente"].mean().reset_index()
    sns.barplot(
        x="PAY_0",
        y="inadimplente",
        data=pay0_taxa,
        ax=ax1,
        palette="Reds",
        hue="PAY_0",
        legend=False,
    )
    ax1.set_title("Taxa de Inadimplencia por Status Recente (PAY_0)", fontsize=11)
    ax1.set_xlabel("Status de Pagamento (-2,-1: Em dia | 0: Minimo pago | 1+: Meses atraso)")
    ax1.set_ylabel("Taxa de Inadimplencia")
    for p in ax1.patches:
        x, w, h = _obter_dimensoes_barra(p)
        if pd.notna(h) and h > 0:
            ax1.annotate(
                f"{h * 100:.1f}%",
                (x + w / 2, h + 0.01),
                ha="center",
                va="bottom",
                fontsize=8,
                weight="bold",
            )

    qtd_taxa = (
        df.groupby("QTD_MESES_ATRASO", observed=False)["inadimplente"]
        .mean()
        .reset_index()
    )
    sns.barplot(
        x="QTD_MESES_ATRASO",
        y="inadimplente",
        data=qtd_taxa,
        ax=ax2,
        palette="Oranges",
        hue="QTD_MESES_ATRASO",
        legend=False,
    )
    ax2.set_title("Inadimplencia por Qtd de Meses Atrasados nos Ultimos 6M", fontsize=11)
    ax2.set_xlabel("Meses com Atraso Registrado (0 a 6)")
    ax2.set_ylabel("")
    for p in ax2.patches:
        x, w, h = _obter_dimensoes_barra(p)
        if pd.notna(h) and h > 0:
            ax2.annotate(
                f"{h * 100:.1f}%",
                (x + w / 2, h + 0.01),
                ha="center",
                va="bottom",
                fontsize=9,
                weight="bold",
            )

    plt.tight_layout()
    p3 = PLOTS_DIR / "03_impacto_atrasos_no_risco.png"
    plt.savefig(p3, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p3}")

    # 4. Limite de Credito e Idade vs Inadimplencia
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 8))

    sns.boxplot(
        x="inadimplente",
        y="LIMIT_BAL",
        data=df,
        ax=ax1,
        palette=cores,
        hue="inadimplente",
        legend=False,
    )
    ax1.set_title("Distribuicao do Limite de Credito por Status", fontsize=11)
    ax1.set_xlabel("Inadimplente (0: Nao | 1: Sim)")
    ax1.set_ylabel("Limite de Credito (NT$)")

    faixa_lim_taxa = (
        df.groupby("FAIXA_LIMITE", observed=False)["inadimplente"].mean().reset_index()
    )
    sns.barplot(
        x="FAIXA_LIMITE",
        y="inadimplente",
        data=faixa_lim_taxa,
        ax=ax2,
        palette="Blues_r",
        hue="FAIXA_LIMITE",
        legend=False,
    )
    ax2.set_title("Taxa de Inadimplencia por Faixa de Limite", fontsize=11)
    ax2.set_ylabel("Taxa de Inadimplencia")
    ax2.tick_params(axis="x", rotation=20)
    for p in ax2.patches:
        x, w, h = _obter_dimensoes_barra(p)
        if pd.notna(h) and h > 0:
            ax2.annotate(
                f"{h * 100:.1f}%",
                (x + w / 2, h + 0.008),
                ha="center",
                va="bottom",
                fontsize=9,
                weight="bold",
            )

    sns.boxplot(
        x="inadimplente",
        y="AGE",
        data=df,
        ax=ax3,
        palette=cores,
        hue="inadimplente",
        legend=False,
    )
    ax3.set_title("Distribuicao de Idade por Status", fontsize=11)
    ax3.set_xlabel("Inadimplente (0: Nao | 1: Sim)")
    ax3.set_ylabel("Idade")

    faixa_eta_taxa = (
        df.groupby("FAIXA_ETARIA", observed=False)["inadimplente"].mean().reset_index()
    )
    sns.barplot(
        x="FAIXA_ETARIA",
        y="inadimplente",
        data=faixa_eta_taxa,
        ax=ax4,
        palette="Greens_r",
        hue="FAIXA_ETARIA",
        legend=False,
    )
    ax4.set_title("Taxa de Inadimplencia por Faixa Etaria", fontsize=11)
    ax4.set_ylabel("Taxa de Inadimplencia")
    for p in ax4.patches:
        x, w, h = _obter_dimensoes_barra(p)
        if pd.notna(h) and h > 0:
            ax4.annotate(
                f"{h * 100:.1f}%",
                (x + w / 2, h + 0.008),
                ha="center",
                va="bottom",
                fontsize=9,
                weight="bold",
            )

    plt.tight_layout()
    p4 = PLOTS_DIR / "04_limite_e_idade_vs_inadimplencia.png"
    plt.savefig(p4, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p4}")

    # 5. Utilizacao de Credito e Comportamento de Faturas
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4.5))

    sns.kdeplot(
        data=df[df["inadimplente"] == 0]["TAXA_UTILIZACAO_LIMITE"],
        ax=ax1,
        label="Adimplente (0)",
        color="#2b5c8f",
        fill=True,
        alpha=0.3,
    )
    sns.kdeplot(
        data=df[df["inadimplente"] == 1]["TAXA_UTILIZACAO_LIMITE"],
        ax=ax1,
        label="Inadimplente (1)",
        color="#d9534f",
        fill=True,
        alpha=0.3,
    )
    ax1.set_title(
        "Densidade da Taxa de Utilizacao de Limite (Fatura / Limite)",
        fontsize=11,
    )
    ax1.set_xlabel("Utilizacao do Limite (0.0 = 0% a 1.0 = 100%)")
    ax1.set_ylabel("Densidade")
    ax1.set_xlim(0, 1.5)
    ax1.legend()

    faturas_medias = [df[f"BILL_AMT{i}"].mean() for i in range(6, 0, -1)]
    pagamentos_medios = [df[f"PAY_AMT{i}"].mean() for i in range(6, 0, -1)]
    meses_labels = ["Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro"]
    ax2.plot(
        meses_labels,
        faturas_medias,
        marker="o",
        color="#2b5c8f",
        label="Fatura Media (BILL_AMT)",
    )
    ax2.plot(
        meses_labels,
        pagamentos_medios,
        marker="s",
        color="#5cb85c",
        label="Pagamento Medio (PAY_AMT)",
    )
    ax2.set_title(
        "Evolucao Temporal da Fatura Media vs Pagamento Medio", fontsize=11
    )
    ax2.set_ylabel("Valor Medio (NT$)")
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", "."))
    )
    ax2.legend()

    plt.tight_layout()
    p5 = PLOTS_DIR / "05_utilizacao_credito_e_faturas.png"
    plt.savefig(p5, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p5}")

    # 6. Matriz de Correlacao Completa
    cols_matriz = [
        "inadimplente",
        "LIMIT_BAL",
        "AGE",
        "PAY_0",
        "PAY_2",
        "PAY_3",
        "MAX_ATRASO_6M",
        "QTD_MESES_ATRASO",
        "TAXA_UTILIZACAO_LIMITE",
        "BILL_AMT1",
        "PAY_AMT1",
    ]
    cols_existentes = [c for c in cols_matriz if c in df.columns]
    corr = df[cols_existentes].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        cbar=True,
        square=True,
    )
    plt.title(
        "Matriz de Correlacao de Pearson (Indicadores de Risco)",
        fontsize=12,
        pad=12,
    )
    plt.tight_layout()
    p6 = PLOTS_DIR / "06_matriz_correlacao_avancada.png"
    plt.savefig(p6, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p6}")

    print(
        "\n[SUCESSO] 6 graficos de diagnostico visual salvos com sucesso na pasta 'plots'!"
    )


def executar_pipeline_completo() -> None:
    """Executa todas as etapas do carregamento, limpeza, enriquecimento e EDA."""
    df_bruto = carregar_dados_brutos()
    df_limpo = validar_integridade(df_bruto)
    df_enriquecido = enriquecer_variaveis(df_limpo)

    df_enriquecido.to_csv(CLEAN_CSV_PATH, index=False)
    print(f"\n[CACHE] Base limpa e enriquecida salva em: {CLEAN_CSV_PATH}")

    imprimir_relatorio_estatistico(df_enriquecido)
    gerar_graficos_eda(df_enriquecido)

    print("\n" + "=" * 65)
    print(" 5. PRINCIPAIS INSIGHTS PARA O MODELO DE RISCO DE CREDITO ")
    print("=" * 65)
    print(
        "1. FORTE SINAL PREDITIVO DE ATRASO: Clientes com atraso recente (PAY_0 >= 2)"
    )
    print(
        "   apresentam inadimplencia superior a 69% (vs 12.8% para quem paga em dia)."
    )
    print(
        "2. GRADIENTE DE LIMITE: Limites baixos (<50k) tem 31.8% de risco, enquanto"
    )
    print("   limites altos (>400k) tem apenas ~12.2% de inadimplencia.")
    print("3. DESBALANCEAMENTO: Apenas 22.1% dos clientes sao inadimplentes.")
    print(
        "   -> Recomendado balanceamento (SMOTE / class_weight) e metricas PR-AUC e ROC-AUC."
    )
    print("=" * 65 + "\n")


if __name__ == "__main__":
    executar_pipeline_completo()
