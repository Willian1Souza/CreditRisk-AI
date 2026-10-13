import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Garante que a raiz do projeto esteja disponível para resolução de módulos
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.predict import CreditRiskPredictor
from api.schemas import (
    ClienteInput,
    BatchClientesRequest,
    HealthResponse,
    PrevisaoResponse,
    AtributosDerivadosResponse,
    BatchPrevisaoResponse,
    ItemLoteResponse,
    ResumoLoteResponse,
    MAPEAMENTO_SEXO,
    MAPEAMENTO_ESCOLARIDADE,
    MAPEAMENTO_ESTADO_CIVIL
)

app = FastAPI(
    title="CreditRisk AI - API de Risco de Crédito",
    description="""
API REST para predição e análise de risco de inadimplência em cartões de crédito.
Valida rigorosamente códigos categóricos e atributos derivados comportamentais antes da inferência.
""",
    version="1.0.0"
)

# Inicializa o preditor (carrega modelo joblib e metadados)
predictor = CreditRiskPredictor()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Retorna detalhes amigáveis e estruturados sobre falhas de validação de dados de entrada."""
    erros = []
    for erro in exc.errors():
        loc = erro.get("loc", [])
        # Remove prefixo de envelopamento interno caso exista
        campo = " -> ".join(str(item) for item in loc if item not in ("body",))
        mensagem = erro.get("msg", "")
        # Remove o prefixo padrão 'Value error, ' do Pydantic se presente
        if mensagem.startswith("Value error, "):
            mensagem = mensagem.replace("Value error, ", "")

        erros.append({
            "campo": campo or "dados",
            "mensagem": mensagem
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "status": "erro_validacao",
            "mensagem": "Falha na validação dos dados de entrada.",
            "detalhes": erros
        }
    )


@app.get("/health", response_model=HealthResponse, tags=["Monitoramento"])
def health():
    """Verifica a integridade e status de operação da API e do modelo carregado."""
    return HealthResponse(
        status="online",
        modelo=predictor.nome_modelo,
        versao="1.0.0",
        total_features=len(predictor.features)
    )


@app.get("/model/info", tags=["Informações do Modelo"])
def model_info():
    """Retorna metadados completos do modelo, regras de validação e métricas de desempenho."""
    metricas_modelo = predictor.metricas.get(predictor.nome_modelo, {})

    return {
        "modelo": predictor.nome_modelo,
        "versao_api": "1.0.0",
        "total_features": len(predictor.features),
        "features_esperadas": predictor.features,
        "mapeamento_categorias": {
            "SEX": MAPEAMENTO_SEXO,
            "EDUCATION": MAPEAMENTO_ESCOLARIDADE,
            "MARRIAGE": MAPEAMENTO_ESTADO_CIVIL
        },
        "regras_atributos_derivados": {
            "MAX_ATRASO_6M": "Máximo atraso entre PAY_0 e PAY_6 (calculado automaticamente se omitido)",
            "QTD_MESES_ATRASO": "Quantidade de meses com atraso positivo (> 0) (calculado automaticamente se omitido)",
            "TAXA_UTILIZACAO_LIMITE": "BILL_AMT1 / LIMIT_BAL limitada a [0, 2] (calculada automaticamente se omitida)"
        },
        "metricas_performance": metricas_modelo
    }


def formatar_resultado(pred_dict: dict[str, Any], cliente_dict: dict[str, Any]) -> PrevisaoResponse:
    score = float(pred_dict.get("score_modelo", 0.0))
    classe = int(pred_dict.get("classe_predita", 0))
    decisao = "Alto Risco" if classe == 1 else "Baixo Risco"
    nome_modelo = str(pred_dict.get("modelo") or predictor.nome_modelo)

    return PrevisaoResponse(
        modelo=nome_modelo,
        score_modelo=score,
        classe_predita=classe,
        decisao=decisao,
        probabilidade_inadimplencia=f"{score * 100:.2f}%",
        atributos_derivados=AtributosDerivadosResponse(
            MAX_ATRASO_6M=cliente_dict["MAX_ATRASO_6M"],
            QTD_MESES_ATRASO=cliente_dict["QTD_MESES_ATRASO"],
            TAXA_UTILIZACAO_LIMITE=cliente_dict["TAXA_UTILIZACAO_LIMITE"]
        )
    )


@app.post("/predict", response_model=PrevisaoResponse, tags=["Predição"])
def predict(cliente: ClienteInput):
    """
    Executa a análise de risco de crédito para um único cliente.
    Valida códigos categóricos, consistência financeira e calcula/valida os atributos derivados.
    """
    try:
        dados_modelo = cliente.to_features_dict()
        resultado = predictor.prever(dados_modelo)
        return formatar_resultado(resultado, dados_modelo)

    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro)
        )
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar previsão: {str(erro)}"
        )


@app.post("/predict/batch", response_model=BatchPrevisaoResponse, tags=["Predição"])
def predict_batch(lote: BatchClientesRequest):
    """
    Executa a análise de risco de crédito para um lote de clientes.
    Valida individualmente cada registro e processa a predição vetorialmente em alta performance.
    """
    try:
        lista_dados = [c.to_features_dict() for c in lote.clientes]
        resultados_pred = predictor.prever_lote(lista_dados)

        previsoes_formatadas = []
        alto_risco = 0
        baixo_risco = 0

        for i, (res, dados) in enumerate(zip(resultados_pred, lista_dados)):
            score = float(res.get("score_modelo", 0.0))
            classe = int(res.get("classe_predita", 0))
            decisao = "Alto Risco" if classe == 1 else "Baixo Risco"
            nome_modelo = str(res.get("modelo") or predictor.nome_modelo)

            if classe == 1:
                alto_risco += 1
            else:
                baixo_risco += 1

            previsoes_formatadas.append(
                ItemLoteResponse(
                    indice=i,
                    modelo=nome_modelo,
                    score_modelo=score,
                    classe_predita=classe,
                    decisao=decisao,
                    probabilidade_inadimplencia=f"{score * 100:.2f}%",
                    atributos_derivados=AtributosDerivadosResponse(
                        MAX_ATRASO_6M=dados["MAX_ATRASO_6M"],
                        QTD_MESES_ATRASO=dados["QTD_MESES_ATRASO"],
                        TAXA_UTILIZACAO_LIMITE=dados["TAXA_UTILIZACAO_LIMITE"]
                    )
                )
            )

        total = len(lista_dados)
        taxa_inadimp = (alto_risco / total * 100) if total > 0 else 0.0

        return BatchPrevisaoResponse(
            total_solicitados=total,
            resumo=ResumoLoteResponse(
                alto_risco=alto_risco,
                baixo_risco=baixo_risco,
                taxa_inadimplencia_lote=f"{taxa_inadimp:.2f}%"
            ),
            previsoes=previsoes_formatadas
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro)
        )
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar lote: {str(erro)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("\n[+] Iniciando CreditRisk AI API em http://127.0.0.1:8000 ...")
    print("[+] Documentação Swagger em: http://127.0.0.1:8000/docs\n")
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)