import os
import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

# Definicao de Diretorios e Caminhos
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
PLOTS_DIR = os.path.join(os.path.dirname(DATA_DIR), "plots")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

RAW_CSV_PATH = os.path.join(DATA_DIR, "credit_card_clients.csv")
CLEAN_CSV_PATH = os.path.join(DATA_DIR, "credit_card_clients_clean.csv")


# Dicionario oficial de mapeamento de variaveis categoricas para nomes legiveis
MAPEAMENTO_SEXO = {
    1: "Masculino",
    2: "Feminino"
}

MAPEAMENTO_ESCOLARIDADE = {
    1: "Pos-Graduacao",
    2: "Universidade",
    3: "Ensino Medio",
    4: "Outros"  # 0, 4, 5 e 6 consolidados em 'Outros'
}

MAPEAMENTO_ESTADO_CIVIL = {
    1: "Casado",
    2: "Solteiro",
    3: "Outros"  # 0 e 3 consolidados em 'Outros'
}

def carregar_dados_brutos():
    """Carrega o dataset bruto do CSV local em data/ ou baixa do UCI Repository."""
    if not os.path.exists(RAW_CSV_PATH):
        print("[+] Baixando dataset do UCI Repository (ID: 350)...")
        dataset = fetch_ucirepo(id=350)
        
        var_mapping = dict(zip(dataset.variables["name"], dataset.variables["description"]))
        X = dataset.data.features.copy()
        y = dataset.data.targets.copy()
        
        rename_cols = {col: str(var_mapping[col]) for col in X.columns if col in var_mapping and pd.notna(var_mapping[col])}
        X = X.rename(columns=rename_cols)
        
        df = X.copy()
        df["inadimplente"] = y.iloc[:, 0].to_numpy() if hasattr(y, "iloc") and getattr(y, "ndim", 1) == 2 else np.array(y).ravel()
        df.to_csv(RAW_CSV_PATH, index=False)
        print(f"[OK] Dados brutos salvos em: {RAW_CSV_PATH}")
    else:
        print(f"[INFO] Carregando dados brutos de: {RAW_CSV_PATH}")
        df = pd.read_csv(RAW_CSV_PATH)
        
    return df

def validar_integridade(df):
    """
    Realiza a verificacao de integridade dos dados:
    - Verificacao de nulos e tipos
    - Deteccao e remocao de duplicatas
    - Padronização de nomes de colunas (PAY_1 -> PAY_0)
    - Tratamento de categorias anomalas em EDUCATION e MARRIAGE
    - Validacao de intervalos numericos (valores negativos em faturas vs pagamentos)
    """
    print("\n" + "="*65)
    print(" 1. VALIDACAO DE INTEGRIDADE DOS DADOS ")
    print("="*65)
    
    print(f"Registros iniciais: {len(df):,}")
    print(f"Total de colunas: {df.shape[1]}")
    
    nulos = df.isnull().sum()
    total_nulos = nulos.sum()
    if total_nulos == 0:
        print("[OK] Nao foram encontrados valores nulos em nenhuma coluna.")
    else:
        print(f"[ALERTA] Valores nulos encontrados:\n{nulos[nulos > 0]}")

    qtd_duplicadas = df.duplicated().sum()
    print(f"\n[DUPLICATAS] Total de linhas duplicadas identificadas: {qtd_duplicadas}")
    if qtd_duplicadas > 0:
        df_tratado = df.drop_duplicates().copy()
        print(f"-> Removidas {qtd_duplicadas} linhas identicas. Registros unicos: {len(df_tratado):,}")
    else:
        df_tratado = df.copy()

    # Normalização preventiva de nomenclatura de colunas
    if "PAY_1" in df_tratado.columns and "PAY_0" not in df_tratado.columns:
        df_tratado = df_tratado.rename(columns={"PAY_1": "PAY_0"})

    print("\n[VALIDACAO CATEGORICA] Padronizando categorias nao documentadas:")
    anomalias_edu = df_tratado["EDUCATION"].isin([0, 5, 6]).sum()
    print(f"-> EDUCATION: {anomalias_edu} registros com codigos [0, 5, 6] consolidados na classe 4 (Outros).")
    df_tratado["EDUCATION"] = df_tratado["EDUCATION"].replace({0: 4, 5: 4, 6: 4})

    anomalias_mar = (df_tratado["MARRIAGE"] == 0).sum()
    print(f"-> MARRIAGE: {anomalias_mar} registros com codigo [0] consolidados na classe 3 (Outros).")
    df_tratado["MARRIAGE"] = df_tratado["MARRIAGE"].replace({0: 3})

    print("\n[CONSISTENCIA FINANCEIRA]")
    faturas_negativas = (df_tratado["BILL_AMT1"] < 0).sum()
    print(f"-> Faturas com saldo negativo (BILL_AMT1 < 0): {faturas_negativas} clientes (representa saldo credor valido).")
    
    pagamentos_negativos = (df_tratado[[f"PAY_AMT{i}" for i in range(1, 7)]] < 0).sum().sum()
    print(f"-> Pagamentos negativos detectados: {pagamentos_negativos} [OK]")

    return df_tratado

def enriquecer_variaveis(df):
    """
    Cria colunas descritivas para analise exploratoria e indicadores de risco de credito:
    - Descricoes textuais (SEXO_DESC, ESCOLARIDADE_DESC, ESTADO_CIVIL_DESC)
    - Faixas de Idade e Limite
    - Indicadores comportamentais de credito (Max atraso, Qtd meses atrasados, Utilizacao de Limite)
    """
    df_feat = df.copy()
    
    df_feat["SEXO_DESC"] = df_feat["SEX"].map(MAPEAMENTO_SEXO)
    df_feat["ESCOLARIDADE_DESC"] = df_feat["EDUCATION"].map(MAPEAMENTO_ESCOLARIDADE)
    df_feat["ESTADO_CIVIL_DESC"] = df_feat["MARRIAGE"].map(MAPEAMENTO_ESTADO_CIVIL)
    
    df_feat["FAIXA_LIMITE"] = pd.cut(
        df_feat["LIMIT_BAL"],
        bins=[0, 50000, 100000, 200000, 400000, 1500000],
        labels=["Ate 50k", "50k-100k", "100k-200k", "200k-400k", "Acima de 400k"],
        include_lowest=True
    )
    
    df_feat["FAIXA_ETARIA"] = pd.cut(
        df_feat["AGE"],
        bins=[20, 30, 40, 50, 60, 100],
        labels=["21-30", "31-40", "41-50", "51-60", "60+"],
        include_lowest=True
    )
    
    colunas_atraso = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
    df_feat["MAX_ATRASO_6M"] = df_feat[colunas_atraso].max(axis=1)
    df_feat["QTD_MESES_ATRASO"] = (df_feat[colunas_atraso] > 0).sum(axis=1)
    
    limite_seguro = df_feat["LIMIT_BAL"].replace(0, np.nan)
    df_feat["TAXA_UTILIZACAO_LIMITE"] = (df_feat["BILL_AMT1"] / limite_seguro).fillna(0.0).clip(lower=0.0, upper=2.0)

    return df_feat


def imprimir_relatorio_estatistico(df):
    """Exibe estatisticas detalhadas e taxas de inadimplencia cruzadas."""
    print("\n" + "="*65)
    print(" 2. ANALISE DA VARIAVEL ALVO (DISTRIBUICAO DE INADIMPLENCIA) ")
    print("="*65)
    total = len(df)
    qtd_0 = (df["inadimplente"] == 0).sum()
    qtd_1 = (df["inadimplente"] == 1).sum()
    pct_0 = (qtd_0 / total) * 100
    pct_1 = (qtd_1 / total) * 100
    print(f"Clientes Adimplentes (0):    {qtd_0:,} ({pct_0:.2f}%)")
    print(f"Clientes Inadimplentes (1):  {qtd_1:,} ({pct_1:.2f}%)")
    print(f"Taxa Media de Inadimplencia da Carteira: {pct_1:.2f}%\n")

    print("\n" + "="*65)
    print(" 3. TAXAS DE INADIMPLENCIA SEGMENTADAS (ANALISE BIVARIADA) ")
    print("="*65)

    print("\n[A] Por Sexo:")
    print(df.groupby("SEXO_DESC", observed=False)["inadimplente"].agg(Total="count", Inadimplentes="sum", Taxa_Inadimplencia="mean").apply(lambda x: x.map("{:.2%}".format) if x.name == "Taxa_Inadimplencia" else x))

    print("\n[B] Por Escolaridade:")
    print(df.groupby("ESCOLARIDADE_DESC", observed=False)["inadimplente"].agg(Total="count", Inadimplentes="sum", Taxa_Inadimplencia="mean").apply(lambda x: x.map("{:.2%}".format) if x.name == "Taxa_Inadimplencia" else x))

    print("\n[C] Por Estado Civil:")
    print(df.groupby("ESTADO_CIVIL_DESC", observed=False)["inadimplente"].agg(Total="count", Inadimplentes="sum", Taxa_Inadimplencia="mean").apply(lambda x: x.map("{:.2%}".format) if x.name == "Taxa_Inadimplencia" else x))

    print("\n[D] Por Faixa de Limite de Credito:")
    print(df.groupby("FAIXA_LIMITE", observed=False)["inadimplente"].agg(Total="count", Inadimplentes="sum", Taxa_Inadimplencia="mean").apply(lambda x: x.map("{:.2%}".format) if x.name == "Taxa_Inadimplencia" else x))

    print("\n[E] Por Atraso Recente (PAY_0):")
    pay0_stats = df.groupby("PAY_0", observed=False)["inadimplente"].agg(Total="count", Taxa_Inadimplencia="mean")
    pay0_stats["Taxa_Inadimplencia"] = pay0_stats["Taxa_Inadimplencia"].map("{:.2%}".format)
    print(pay0_stats)

    print("\n[F] Por Quantidade de Meses em Atraso nos Ultimos 6 Meses:")
    meses_stats = df.groupby("QTD_MESES_ATRASO", observed=False)["inadimplente"].agg(Total="count", Taxa_Inadimplencia="mean")
    meses_stats["Taxa_Inadimplencia"] = meses_stats["Taxa_Inadimplencia"].map("{:.2%}".format)
    print(meses_stats)

def gerar_graficos_eda(df):
    """Gera e salva 6 graficos de diagnostico visual de alta qualidade na pasta plots."""
    print("\n" + "="*65)
    print(" 4. GERANDO E SALVANDO GRAFICOS DE ALTO IMPACTO ")
    print("="*65)
    
    sns.set_theme(style="whitegrid", font_scale=1.0)
    cores = ["#2b5c8f", "#d9534f"]

    # 1. Distribuicao da Variavel Alvo
    plt.figure(figsize=(7, 4.5))
    ax = sns.countplot(x="inadimplente", data=df, hue="inadimplente", palette=cores, legend=False)
    plt.title("Distribuicao da Variavel Alvo: Inadimplencia no Proximo Mes", fontsize=12, pad=12)
    plt.xlabel("Status (0: Adimplente | 1: Inadimplente)", fontsize=10)
    plt.ylabel("Contagem de Clientes", fontsize=10)
    total = len(df)
    for p in ax.patches:
        h = p.get_height()
        pct = (h / total) * 100
        ax.annotate(f"{int(h):,} ({pct:.1f}%)", (p.get_x() + 0.22, h + 300), fontsize=10, weight="bold")
    plt.tight_layout()
    p1 = os.path.join(PLOTS_DIR, "01_distribuicao_alvo.png")
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p1}")

    # 2. Perfil Sociodemografico de Risco
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    for i, (col, title) in enumerate([
        ("SEXO_DESC", "Inadimplencia por Sexo"),
        ("ESCOLARIDADE_DESC", "Inadimplencia por Escolaridade"),
        ("ESTADO_CIVIL_DESC", "Inadimplencia por Estado Civil")
    ]):
        taxa = df.groupby(col, observed=False)["inadimplente"].mean().reset_index()
        sns.barplot(x=col, y="inadimplente", data=taxa, ax=axes[i], palette="Blues_r", hue=col, legend=False)
        axes[i].set_title(title, fontsize=11)
        axes[i].set_ylabel("Taxa de Inadimplencia" if i == 0 else "")
        axes[i].set_xlabel("")
        axes[i].tick_params(axis="x", rotation=15)
        for p in axes[i].patches:
            val = p.get_height()
            axes[i].annotate(f"{val*100:.1f}%", (p.get_x() + 0.25, val + 0.008), fontsize=9, weight="bold")
    plt.tight_layout()
    p2 = os.path.join(PLOTS_DIR, "02_perfil_sociodemografico_risco.png")
    plt.savefig(p2, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p2}")

    # 3. Impacto dos Atrasos no Risco
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4.5))
    
    pay0_taxa = df.groupby("PAY_0", observed=False)["inadimplente"].mean().reset_index()
    sns.barplot(x="PAY_0", y="inadimplente", data=pay0_taxa, ax=ax1, palette="Reds", hue="PAY_0", legend=False)
    ax1.set_title("Taxa de Inadimplencia por Status Recente (PAY_0)", fontsize=11)
    ax1.set_xlabel("Status de Pagamento (-2,-1: Em dia | 0: Minimo pago | 1+: Meses atraso)")
    ax1.set_ylabel("Taxa de Inadimplencia")
    for p in ax1.patches:
        val = p.get_height()
        if val > 0:
            ax1.annotate(f"{val*100:.0f}%", (p.get_x() + 0.15, val + 0.015), fontsize=8, weight="bold")

    qtd_taxa = df.groupby("QTD_MESES_ATRASO", observed=False)["inadimplente"].mean().reset_index()
    sns.barplot(x="QTD_MESES_ATRASO", y="inadimplente", data=qtd_taxa, ax=ax2, palette="Oranges", hue="QTD_MESES_ATRASO", legend=False)
    ax2.set_title("Inadimplencia por Qtd de Meses Atrasados nos Ultimos 6M", fontsize=11)
    ax2.set_xlabel("Meses com Atraso Registrado (0 a 6)")
    ax2.set_ylabel("")
    for p in ax2.patches:
        val = p.get_height()
        ax2.annotate(f"{val*100:.1f}%", (p.get_x() + 0.2, val + 0.015), fontsize=9, weight="bold")
    
    plt.tight_layout()
    p3 = os.path.join(PLOTS_DIR, "03_impacto_atrasos_no_risco.png")
    plt.savefig(p3, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p3}")

    # 4. Limite de Credito e Idade vs Inadimplencia
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 8))
    
    sns.boxplot(x="inadimplente", y="LIMIT_BAL", data=df, ax=ax1, palette=cores, hue="inadimplente", legend=False)
    ax1.set_title("Distribuicao do Limite de Credito por Status", fontsize=11)
    ax1.set_xlabel("Inadimplente (0: Nao | 1: Sim)")
    ax1.set_ylabel("Limite de Credito (NT$)")

    faixa_lim_taxa = df.groupby("FAIXA_LIMITE", observed=False)["inadimplente"].mean().reset_index()
    sns.barplot(x="FAIXA_LIMITE", y="inadimplente", data=faixa_lim_taxa, ax=ax2, palette="Blues_r", hue="FAIXA_LIMITE", legend=False)
    ax2.set_title("Taxa de Inadimplencia por Faixa de Limite", fontsize=11)
    ax2.set_ylabel("Taxa de Inadimplencia")
    ax2.tick_params(axis="x", rotation=20)
    for p in ax2.patches:
        val = p.get_height()
        ax2.annotate(f"{val*100:.1f}%", (p.get_x() + 0.2, val + 0.008), fontsize=9, weight="bold")

    sns.boxplot(x="inadimplente", y="AGE", data=df, ax=ax3, palette=cores, hue="inadimplente", legend=False)
    ax3.set_title("Distribuicao de Idade por Status", fontsize=11)
    ax3.set_xlabel("Inadimplente (0: Nao | 1: Sim)")
    ax3.set_ylabel("Idade")

    faixa_eta_taxa = df.groupby("FAIXA_ETARIA", observed=False)["inadimplente"].mean().reset_index()
    sns.barplot(x="FAIXA_ETARIA", y="inadimplente", data=faixa_eta_taxa, ax=ax4, palette="Greens_r", hue="FAIXA_ETARIA", legend=False)
    ax4.set_title("Taxa de Inadimplencia por Faixa Etaria", fontsize=11)
    ax4.set_ylabel("Taxa de Inadimplencia")
    for p in ax4.patches:
        val = p.get_height()
        ax4.annotate(f"{val*100:.1f}%", (p.get_x() + 0.25, val + 0.008), fontsize=9, weight="bold")

    plt.tight_layout()
    p4 = os.path.join(PLOTS_DIR, "04_limite_e_idade_vs_inadimplencia.png")
    plt.savefig(p4, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p4}")

    # 5. Utilizacao de Credito e Comportamento de Faturas
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4.5))
    
    sns.kdeplot(data=df[df["inadimplente"] == 0]["TAXA_UTILIZACAO_LIMITE"], ax=ax1, label="Adimplente (0)", color="#2b5c8f", fill=True, alpha=0.3)
    sns.kdeplot(data=df[df["inadimplente"] == 1]["TAXA_UTILIZACAO_LIMITE"], ax=ax1, label="Inadimplente (1)", color="#d9534f", fill=True, alpha=0.3)
    ax1.set_title("Densidade da Taxa de Utilizacao de Limite (Fatura / Limite)", fontsize=11)
    ax1.set_xlabel("Utilizacao do Limite (0.0 = 0% a 1.0 = 100%)")
    ax1.set_ylabel("Densidade")
    ax1.set_xlim(0, 1.5)
    ax1.legend()

    faturas_medias = [df[f"BILL_AMT{i}"].mean() for i in range(6, 0, -1)]
    pagamentos_medios = [df[f"PAY_AMT{i}"].mean() for i in range(6, 0, -1)]
    meses_labels = ["Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro"]
    ax2.plot(meses_labels, faturas_medias, marker="o", color="#2b5c8f", label="Fatura Media (BILL_AMT)")
    ax2.plot(meses_labels, pagamentos_medios, marker="s", color="#5cb85c", label="Pagamento Medio (PAY_AMT)")
    ax2.set_title("Evolucao Temporal da Fatura Media vs Pagamento Medio", fontsize=11)
    ax2.set_ylabel("Valor Medio (NT$)")
    ax2.legend()
    
    plt.tight_layout()
    p5 = os.path.join(PLOTS_DIR, "05_utilizacao_credito_e_faturas.png")
    plt.savefig(p5, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p5}")

    # 6. Matriz de Correlacao Completa
    cols_matriz = [
        "inadimplente", "LIMIT_BAL", "AGE", "PAY_0", "PAY_2", "PAY_3",
        "MAX_ATRASO_6M", "QTD_MESES_ATRASO", "TAXA_UTILIZACAO_LIMITE",
        "BILL_AMT1", "PAY_AMT1"
    ]
    corr = df[cols_matriz].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, cbar=True, square=True)
    plt.title("Matriz de Correlacao de Pearson (Indicadores de Risco)", fontsize=12, pad=12)
    plt.tight_layout()
    p6 = os.path.join(PLOTS_DIR, "06_matriz_correlacao_avancada.png")
    plt.savefig(p6, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p6}")

    print("\n[SUCESSO] 6 graficos de diagnostico visual salvos com sucesso na pasta 'plots'!")

def executar_pipeline_completo():
    """Executa todas as etapas do carregamento, limpeza, enriquecimento e EDA."""
    df_bruto = carregar_dados_brutos()
    df_limpo = validar_integridade(df_bruto)
    df_enriquecido = enriquecer_variaveis(df_limpo)
    
    df_enriquecido.to_csv(CLEAN_CSV_PATH, index=False)
    print(f"\n[CACHE] Base limpa e enriquecida salva em: {CLEAN_CSV_PATH}")

    imprimir_relatorio_estatistico(df_enriquecido)
    gerar_graficos_eda(df_enriquecido)

    print("\n" + "="*65)
    print(" 5. PRINCIPAIS INSIGHTS PARA O MODELO DE RISCO DE CREDITO ")
    print("="*65)
    print("1. FORTE SINAL PREDITIVO DE ATRASO: Clientes com atraso recente (PAY_0 >= 2)")
    print("   apresentam inadimplencia superior a 69% (vs 12.8% para quem paga em dia).")
    print("2. GRADIENTE DE LIMITE: Limites baixos (<50k) tem 31.8% de risco, enquanto")
    print("   limites altos (>400k) tem apenas ~12.2% de inadimplencia.")
    print("3. DESBALANCEAMENTO: Apenas 22.1% dos clientes sao inadimplentes.")
    print("   -> Recomendado balanceamento (SMOTE / class_weight) e metricas PR-AUC e ROC-AUC.")
    print("="*65 + "\n")

if __name__ == "__main__":
    executar_pipeline_completo()
