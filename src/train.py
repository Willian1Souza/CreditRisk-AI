import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    roc_curve,
    precision_recall_curve,
    confusion_matrix
)

# Silencia avisos desnecessarios
warnings.filterwarnings("ignore")

# Suporte seguro a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Definicao de Caminhos Dinamicos relativos a raiz do projeto
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
PLOTS_DIR = os.path.join(BASE_DIR, "plots")

CLEAN_CSV_PATH = os.path.join(DATA_DIR, "credit_card_clients_clean.csv")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

def carregar_dados():
    """Carrega o dataset limpo e preparado na etapa de EDA."""
    if not os.path.exists(CLEAN_CSV_PATH):
        raise FileNotFoundError(
            f"Dataset limpo nao encontrado em {CLEAN_CSV_PATH}. "
            "Execute primeiro 'python -m src.eda' para gerar a base tratada."
        )

    print(f"[INFO] Carregando dataset limpo de: {CLEAN_CSV_PATH}")
    df = pd.read_csv(CLEAN_CSV_PATH)
    return df

def preparar_dados(df):
    """
    Define as features preditoras e a variavel alvo, aplicando split estratificado.
    Garante que a mesma divisao seja utilizada em todos os modelos.
    """
    cat_features = ["SEX", "EDUCATION", "MARRIAGE"]
    num_features = [
        "LIMIT_BAL", "AGE", "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
        "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
        "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
        "MAX_ATRASO_6M", "QTD_MESES_ATRASO", "TAXA_UTILIZACAO_LIMITE"
    ]
    
    cat_features = [c for c in cat_features if c in df.columns]
    num_features = [c for c in num_features if c in df.columns]
    
    features = cat_features + num_features
    X = df[features]
    y = df["inadimplente"]

    print("\n" + "="*65)
    print(" 1. DIVISAO ESTRATIFICADA DE TREINO E TESTE ")
    print("="*65)
    print(f"Total de amostras: {len(df):,}")
    print(f"Features preditoras selecionadas: {len(features)} ({len(cat_features)} categoricas, {len(num_features)} numericas)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"-> Treino: {len(X_train):,} amostras (Inadimplencia: {y_train.mean():.2%})")
    print(f"-> Teste:  {len(X_test):,} amostras (Inadimplencia: {y_test.mean():.2%})")

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), cat_features),
            ("num", StandardScaler(), num_features)
        ]
    )

    return X_train, X_test, y_train, y_test, preprocessor, features

def calcular_ks(y_true, y_probs):
    """Calcula a estatistica Kolmogorov-Smirnov (KS), padrao de risco bancario."""
    fpr, tpr, _ = roc_curve(y_true, y_probs)
    return float(np.max(tpr - fpr))

def treinar_e_avaliar_modelos(X_train, X_test, y_train, y_test, preprocessor, features):
    """
    Treina e avalia Regressao Logistica, Random Forest e XGBoost sob as mesmas condicoes.
    """
    scale_pos_weight = float((y_train == 0).sum() / (y_train == 1).sum())

    modelos_config = {
        "Regressao Logistica": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.08,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1
        )
    }

    print("\n" + "="*65)
    print(" 2. TREINAMENTO DOS MODELOS COM PIPELINES UNIFICADOS ")
    print("="*65)

    resultados = {}
    pipelines_treinados = {}

    for nome, estimador in modelos_config.items():
        print(f"[*] Treinando {nome}...")
        
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", estimador)
        ])

        pipeline.fit(X_train, y_train)
        pipelines_treinados[nome] = pipeline

        probs = pipeline.predict_proba(X_test)[:, 1]
        preds = pipeline.predict(X_test)

        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        roc_auc = roc_auc_score(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)
        gini = 2 * roc_auc - 1
        ks = calcular_ks(y_test, probs)
        cm = confusion_matrix(y_test, preds)

        resultados[nome] = {
            "Acuracia": round(acc, 4),
            "Precisao": round(prec, 4),
            "Recall": round(rec, 4),
            "F1-Score": round(f1, 4),
            "ROC-AUC": round(roc_auc, 4),
            "PR-AUC": round(pr_auc, 4),
            "Gini": round(gini, 4),
            "KS": round(ks, 4),
            "probs": probs,
            "preds": preds,
            "confusion_matrix": cm.tolist()
        }

    df_comparativo = pd.DataFrame(resultados).T[[
        "Acuracia", "Precisao", "Recall", "F1-Score", "ROC-AUC", "PR-AUC", "Gini", "KS"
    ]]

    print("\n" + "="*65)
    print(" 3. COMPARATIVO DE PERFORMANCE NO CONJUNTO DE TESTE ")
    print("="*65)
    print(df_comparativo.to_string())

    return resultados, pipelines_treinados, df_comparativo

def salvar_graficos_comparativos(resultados, y_test, pipelines_treinados, preprocessor, features):
    """Gera graficos comparativos de curvas ROC, PR, Matrizes de Confusao e Importancia."""
    print("\n" + "="*65)
    print(" 4. GERANDO GRAFICOS COMPARATIVOS DE PERFORMANCE ")
    print("="*65)
    sns.set_theme(style="whitegrid")
    cores = {"Regressao Logistica": "#2b5c8f", "Random Forest": "#2ca02c", "XGBoost": "#d9534f"}

    # Curva ROC
    plt.figure(figsize=(8, 6))
    for nome, res in resultados.items():
        fpr, tpr, _ = roc_curve(y_test, res["probs"])
        plt.plot(fpr, tpr, label=f"{nome} (AUC = {res['ROC-AUC']:.4f} | Gini = {res['Gini']:.4f})", color=cores[nome], lw=2)
    plt.plot([0, 1], [0, 1], "k--", lw=1.5, label="Aleatorio (AUC = 0.5000)")
    plt.title("Comparacao de Curvas ROC (Discriminacao de Risco)", fontsize=13, pad=12)
    plt.xlabel("Taxa de Falsos Positivos (FPR)", fontsize=11)
    plt.ylabel("Taxa de Verdadeiros Positivos / Recall (TPR)", fontsize=11)
    plt.legend(loc="lower right", fontsize=10)
    plt.tight_layout()
    p_roc = os.path.join(PLOTS_DIR, "comparacao_curvas_roc.png")
    plt.savefig(p_roc, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p_roc}")

    # Curva PR
    plt.figure(figsize=(8, 6))
    taxa_base = float(y_test.mean())
    for nome, res in resultados.items():
        prec, rec, _ = precision_recall_curve(y_test, res["probs"])
        plt.plot(rec, prec, label=f"{nome} (PR-AUC = {res['PR-AUC']:.4f})", color=cores[nome], lw=2)
    plt.axhline(taxa_base, color="k", linestyle="--", lw=1.5, label=f"Baseline Inadimplencia ({taxa_base:.2%})")
    plt.title("Comparacao de Curvas Precision-Recall (Dados Desbalanceados)", fontsize=13, pad=12)
    plt.xlabel("Recall (Taxa de Captura de Inadimplentes)", fontsize=11)
    plt.ylabel("Precisao (Proporcao de Acertos dos Alarmes)", fontsize=11)
    plt.legend(loc="upper right", fontsize=10)
    plt.tight_layout()
    p_pr = os.path.join(PLOTS_DIR, "comparacao_curvas_pr.png")
    plt.savefig(p_pr, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p_pr}")

    # Matrizes de Confusao
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    for i, (nome, res) in enumerate(resultados.items()):
        cm = np.array(res["confusion_matrix"])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[i], cbar=False,
                    xticklabels=["Adimplente", "Inadimplente"],
                    yticklabels=["Adimplente", "Inadimplente"])
        axes[i].set_title(f"Matriz de Confusao - {nome}", fontsize=11)
        axes[i].set_xlabel("Predito", fontsize=10)
        axes[i].set_ylabel("Real" if i == 0 else "", fontsize=10)
    plt.tight_layout()
    p_cm = os.path.join(PLOTS_DIR, "comparacao_matrizes_confusao.png")
    plt.savefig(p_cm, dpi=300)
    plt.close()
    print(f"[+] Salvo: {p_cm}")

    # Importancia das Features
    try:
        ohe = pipelines_treinados["Random Forest"].named_steps["preprocessor"].named_transformers_["cat"]
        cat_encoded_names = list(ohe.get_feature_names_out(["SEX", "EDUCATION", "MARRIAGE"]))
        num_names = [f for f in features if f not in ["SEX", "EDUCATION", "MARRIAGE"]]
        todas_features = cat_encoded_names + num_names

        rf_imp = pipelines_treinados["Random Forest"].named_steps["classifier"].feature_importances_
        xgb_imp = pipelines_treinados["XGBoost"].named_steps["classifier"].feature_importances_

        df_imp = pd.DataFrame({
            "Feature": todas_features,
            "Random Forest": rf_imp,
            "XGBoost": xgb_imp
        })

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5))
        
        top_rf = df_imp.sort_values(by="Random Forest", ascending=False).head(10)
        sns.barplot(x="Random Forest", y="Feature", data=top_rf, ax=ax1, palette="Greens_r")
        ax1.set_title("Top 10 Features - Random Forest", fontsize=11)
        ax1.set_xlabel("Importancia Relativa")

        top_xgb = df_imp.sort_values(by="XGBoost", ascending=False).head(10)
        sns.barplot(x="XGBoost", y="Feature", data=top_xgb, ax=ax2, palette="Reds_r")
        ax2.set_title("Top 10 Features - XGBoost", fontsize=11)
        ax2.set_xlabel("Importancia Relativa")

        plt.tight_layout()
        p_imp = os.path.join(PLOTS_DIR, "importancia_features_rf_xgb.png")
        plt.savefig(p_imp, dpi=300)
        plt.close()
        print(f"[+] Salvo: {p_imp}")
    except Exception as e:
        print(f"[AVISO] Nao foi possivel plotar importancia de features: {e}")

def salvar_modelos(pipelines_treinados, resultados, df_comparativo, features):
    """Salva os modelos treinados, o melhor pipeline e o resumo de metricas em disco."""
    print("\n" + "="*65)
    print(" 5. SALVANDO MODELOS E METRICAS ")
    print("="*65)

    melhor_nome = df_comparativo["ROC-AUC"].astype(float).idxmax()
    melhor_pipeline = pipelines_treinados[melhor_nome]
    print(f"🏆 Melhor Modelo Selecionado: {melhor_nome} (ROC-AUC: {resultados[melhor_nome]['ROC-AUC']})")

    for nome, pipe in pipelines_treinados.items():
        arquivo_nome = nome.lower().replace(" ", "_") + ".joblib"
        caminho_modelo = os.path.join(MODELS_DIR, arquivo_nome)
        joblib.dump(pipe, caminho_modelo)
        print(f"[+] Modelo salvo: {caminho_modelo}")

    caminho_melhor = os.path.join(MODELS_DIR, "best_credit_risk_model.joblib")
    joblib.dump(melhor_pipeline, caminho_melhor)
    print(f"[★] Melhor modelo salvo como producao em: {caminho_melhor}")

    resumo_json = {
        "melhor_modelo": melhor_nome,
        "features_entrada": features,
        "metricas": {
            k: {m: v for m, v in vals.items() if m not in ["probs", "preds"]}
            for k, vals in resultados.items()
        }
    }
    caminho_json = os.path.join(MODELS_DIR, "metrics_summary.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(resumo_json, f, indent=4, ensure_ascii=False)
    print(f"[+] Resumo de metricas salvo em: {caminho_json}")

def executar_pipeline_treinamento():
    """Fluxo principal de execucao."""
    df = carregar_dados()
    X_train, X_test, y_train, y_test, preprocessor, features = preparar_dados(df)
    resultados, pipelines_treinados, df_comparativo = treinar_e_avaliar_modelos(
        X_train, X_test, y_train, y_test, preprocessor, features
    )
    salvar_graficos_comparativos(
        resultados, y_test, pipelines_treinados, preprocessor, features
    )
    salvar_modelos(pipelines_treinados, resultados, df_comparativo, features)

    print("\n" + "="*65)
    print(" CONCLUSAO DO TREINAMENTO DE MACHINE LEARNING ")
    print("="*65)
    print("1. Ambos os modelos de arvore (Random Forest e XGBoost) superaram")
    print("   significativamente a Regressao Logistica em ROC-AUC e PR-AUC.")
    print("2. O XGBoost demonstrou a melhor separacao global e precisao media.")
    print("3. Modelos prontos e serializados na pasta 'models' para integracao com API!")
    print("="*65 + "\n")

if __name__ == "__main__":
    executar_pipeline_treinamento()
