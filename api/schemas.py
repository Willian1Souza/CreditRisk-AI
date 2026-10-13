from typing import Any, Optional, Union
from pydantic import BaseModel, Field, model_validator


MAPEAMENTO_SEXO = {
    1: "Masculino",
    2: "Feminino"
}

MAPEAMENTO_ESCOLARIDADE = {
    1: "Pos-Graduacao",
    2: "Universidade",
    3: "Ensino Medio",
    4: "Outros"
}

MAPEAMENTO_ESTADO_CIVIL = {
    1: "Casado",
    2: "Solteiro",
    3: "Outros"
}


class ClienteInput(BaseModel):
    """
    Schema de entrada para os dados do cliente para análise de risco de crédito.
    Aceita os 23 atributos brutos e valida ou calcula automaticamente os 3 atributos derivados.
    """

    # Variáveis Demográficas e Cadastrais
    SEX: int = Field(
        ...,
        description="Sexo do cliente: 1 = Masculino, 2 = Feminino",
        examples=[2]
    )
    EDUCATION: int = Field(
        ...,
        description="Escolaridade: 1 = Pós-Graduação, 2 = Universidade, 3 = Ensino Médio, 4 = Outros (códigos 0, 5 e 6 consolidados em 4)",
        examples=[2]
    )
    MARRIAGE: int = Field(
        ...,
        description="Estado civil: 1 = Casado, 2 = Solteiro, 3 = Outros (código 0 consolidado em 3)",
        examples=[1]
    )
    LIMIT_BAL: float = Field(
        ...,
        gt=0,
        description="Valor do crédito concedido (deve ser maior que zero)",
        examples=[50000.0]
    )
    AGE: int = Field(
        ...,
        ge=18,
        le=120,
        description="Idade em anos (entre 18 e 120)",
        examples=[35]
    )

    # Histórico de Status de Pagamento (-2 = sem uso, -1 = pago em dia, 0 = rotativo, 1..9 = meses de atraso)
    PAY_0: int = Field(..., ge=-2, le=9, description="Status de pagamento em Setembro", examples=[2])
    PAY_2: int = Field(..., ge=-2, le=9, description="Status de pagamento em Agosto", examples=[1])
    PAY_3: int = Field(..., ge=-2, le=9, description="Status de pagamento em Julho", examples=[0])
    PAY_4: int = Field(..., ge=-2, le=9, description="Status de pagamento em Junho", examples=[0])
    PAY_5: int = Field(..., ge=-2, le=9, description="Status de pagamento em Maio", examples=[0])
    PAY_6: int = Field(..., ge=-2, le=9, description="Status de pagamento em Abril", examples=[0])

    # Valores das Faturas (podem ser negativos representando saldo credor)
    BILL_AMT1: float = Field(..., description="Valor da fatura em Setembro", examples=[30000.0])
    BILL_AMT2: float = Field(..., description="Valor da fatura em Agosto", examples=[28000.0])
    BILL_AMT3: float = Field(..., description="Valor da fatura em Julho", examples=[25000.0])
    BILL_AMT4: float = Field(..., description="Valor da fatura em Junho", examples=[23000.0])
    BILL_AMT5: float = Field(..., description="Valor da fatura em Maio", examples=[20000.0])
    BILL_AMT6: float = Field(..., description="Valor da fatura em Abril", examples=[18000.0])

    # Pagamentos Efetuados (devem ser não-negativos)
    PAY_AMT1: float = Field(..., ge=0, description="Pagamento realizado em Setembro", examples=[2000.0])
    PAY_AMT2: float = Field(..., ge=0, description="Pagamento realizado em Agosto", examples=[3000.0])
    PAY_AMT3: float = Field(..., ge=0, description="Pagamento realizado em Julho", examples=[2500.0])
    PAY_AMT4: float = Field(..., ge=0, description="Pagamento realizado em Junho", examples=[2000.0])
    PAY_AMT5: float = Field(..., ge=0, description="Pagamento realizado em Maio", examples=[1500.0])
    PAY_AMT6: float = Field(..., ge=0, description="Pagamento realizado em Abril", examples=[1000.0])

    # Atributos Derivados (Opcionais: se enviados são validados contra as colunas base; se omitidos são calculados)
    MAX_ATRASO_6M: Optional[int] = Field(
        None,
        description="Atraso máximo nos últimos 6 meses (max(PAY_0..PAY_6)). Calculado automaticamente se omitido.",
        examples=[2]
    )
    QTD_MESES_ATRASO: Optional[int] = Field(
        None,
        ge=0,
        le=6,
        description="Quantidade de meses com atraso positivo (> 0). Calculado automaticamente se omitido.",
        examples=[2]
    )
    TAXA_UTILIZACAO_LIMITE: Optional[float] = Field(
        None,
        ge=0.0,
        description="Taxa de utilização do limite (BILL_AMT1 / LIMIT_BAL limitada a [0, 2]). Calculada automaticamente se omitida.",
        examples=[0.60]
    )

    @model_validator(mode="before")
    @classmethod
    def desenvelopar_dados(cls, values: Any) -> Any:
        """Permite receber {'dados': {...}} ou diretamente o objeto de atributos."""
        if isinstance(values, dict) and "dados" in values and isinstance(values["dados"], dict):
            return values["dados"]
        return values

    @model_validator(mode="after")
    def validar_regras_negocio_e_derivadas(self) -> "ClienteInput":
        """
        Valida códigos categóricos, consistência financeira e integridade dos atributos derivados.
        """
        # 1. Validação Categórica: SEX
        if self.SEX not in (1, 2):
            raise ValueError(
                f"Código de 'SEX' inválido: {self.SEX}. Valores aceitos: 1 (Masculino) ou 2 (Feminino)."
            )

        # 2. Validação Categórica: EDUCATION (Regra de integridade: 0, 5, 6 consolidados em 4)
        if self.EDUCATION in (0, 5, 6):
            self.EDUCATION = 4
        elif self.EDUCATION not in (1, 2, 3, 4):
            raise ValueError(
                f"Código de 'EDUCATION' inválido: {self.EDUCATION}. "
                "Valores aceitos: 1 (Pós-Graduação), 2 (Universidade), 3 (Ensino Médio), 4 (Outros). "
                "Códigos [0, 5, 6] são automaticamente mapeados para 4."
            )

        # 3. Validação Categórica: MARRIAGE (Regra de integridade: 0 consolidado em 3)
        if self.MARRIAGE == 0:
            self.MARRIAGE = 3
        elif self.MARRIAGE not in (1, 2, 3):
            raise ValueError(
                f"Código de 'MARRIAGE' inválido: {self.MARRIAGE}. "
                "Valores aceitos: 1 (Casado), 2 (Solteiro), 3 (Outros). "
                "Código 0 é automaticamente mapeado para 3."
            )

        # 4. Validação dos códigos de histórico de pagamento
        pay_cols = [
            ("PAY_0", self.PAY_0),
            ("PAY_2", self.PAY_2),
            ("PAY_3", self.PAY_3),
            ("PAY_4", self.PAY_4),
            ("PAY_5", self.PAY_5),
            ("PAY_6", self.PAY_6)
        ]
        for nome, valor in pay_cols:
            if not (-2 <= valor <= 9):
                raise ValueError(
                    f"Código de histórico '{nome}' inválido: {valor}. O intervalo permitido é de -2 a 9."
                )

        # 5. Cálculo dos Atributos Derivados Esperados
        atrasos = [valor for _, valor in pay_cols]
        max_atraso_esperado = max(atrasos)
        qtd_atrasos_esperada = sum(1 for v in atrasos if v > 0)
        taxa_util_esperada = round(max(0.0, min(self.BILL_AMT1 / self.LIMIT_BAL, 2.0)), 4)

        # Validação / Atribuição de MAX_ATRASO_6M
        if self.MAX_ATRASO_6M is not None:
            if self.MAX_ATRASO_6M != max_atraso_esperado:
                raise ValueError(
                    f"Atributo derivado 'MAX_ATRASO_6M' inconsistente: informado {self.MAX_ATRASO_6M}, "
                    f"mas o valor real calculado a partir de PAY_0 a PAY_6 é {max_atraso_esperado}."
                )
        else:
            self.MAX_ATRASO_6M = max_atraso_esperado

        # Validação / Atribuição de QTD_MESES_ATRASO
        if self.QTD_MESES_ATRASO is not None:
            if self.QTD_MESES_ATRASO != qtd_atrasos_esperada:
                raise ValueError(
                    f"Atributo derivado 'QTD_MESES_ATRASO' inconsistente: informado {self.QTD_MESES_ATRASO}, "
                    f"mas a contagem real de meses com atraso positivo é {qtd_atrasos_esperada}."
                )
        else:
            self.QTD_MESES_ATRASO = qtd_atrasos_esperada

        # Validação / Atribuição de TAXA_UTILIZACAO_LIMITE
        if self.TAXA_UTILIZACAO_LIMITE is not None:
            if self.TAXA_UTILIZACAO_LIMITE < 0:
                raise ValueError("Atributo derivado 'TAXA_UTILIZACAO_LIMITE' não pode ser negativo.")
            # Permite pequena margem de arredondamento de até 0.05
            if abs(self.TAXA_UTILIZACAO_LIMITE - taxa_util_esperada) > 0.05:
                raise ValueError(
                    f"Atributo derivado 'TAXA_UTILIZACAO_LIMITE' inconsistente: informado {self.TAXA_UTILIZACAO_LIMITE}, "
                    f"mas a taxa calculada (BILL_AMT1 / LIMIT_BAL clipada em [0, 2]) é {taxa_util_esperada}."
                )
        else:
            self.TAXA_UTILIZACAO_LIMITE = taxa_util_esperada

        return self

    def to_features_dict(self) -> dict[str, Any]:
        """Converte a instância para o dicionário exato de 26 features esperado pelo modelo."""
        return {
            "SEX": self.SEX,
            "EDUCATION": self.EDUCATION,
            "MARRIAGE": self.MARRIAGE,
            "LIMIT_BAL": self.LIMIT_BAL,
            "AGE": self.AGE,
            "PAY_0": self.PAY_0,
            "PAY_2": self.PAY_2,
            "PAY_3": self.PAY_3,
            "PAY_4": self.PAY_4,
            "PAY_5": self.PAY_5,
            "PAY_6": self.PAY_6,
            "BILL_AMT1": self.BILL_AMT1,
            "BILL_AMT2": self.BILL_AMT2,
            "BILL_AMT3": self.BILL_AMT3,
            "BILL_AMT4": self.BILL_AMT4,
            "BILL_AMT5": self.BILL_AMT5,
            "BILL_AMT6": self.BILL_AMT6,
            "PAY_AMT1": self.PAY_AMT1,
            "PAY_AMT2": self.PAY_AMT2,
            "PAY_AMT3": self.PAY_AMT3,
            "PAY_AMT4": self.PAY_AMT4,
            "PAY_AMT5": self.PAY_AMT5,
            "PAY_AMT6": self.PAY_AMT6,
            "MAX_ATRASO_6M": self.MAX_ATRASO_6M,
            "QTD_MESES_ATRASO": self.QTD_MESES_ATRASO,
            "TAXA_UTILIZACAO_LIMITE": self.TAXA_UTILIZACAO_LIMITE
        }


class BatchClientesRequest(BaseModel):
    """
    Schema de requisição em lote. Suporta tanto uma lista direta de clientes
    quanto o formato envelopado {'clientes': [...]}.
    """
    clientes: list[ClienteInput] = Field(
        ...,
        min_length=1,
        description="Lista de clientes para previsão em lote"
    )

    @model_validator(mode="before")
    @classmethod
    def normalizar_lote(cls, values: Any) -> Any:
        if isinstance(values, list):
            return {"clientes": values}
        return values


class HealthResponse(BaseModel):
    status: str
    modelo: str
    versao: str
    total_features: int


class AtributosDerivadosResponse(BaseModel):
    MAX_ATRASO_6M: int
    QTD_MESES_ATRASO: int
    TAXA_UTILIZACAO_LIMITE: float


class PrevisaoResponse(BaseModel):
    modelo: str
    score_modelo: float
    classe_predita: int
    decisao: str
    probabilidade_inadimplencia: str
    atributos_derivados: AtributosDerivadosResponse


class ItemLoteResponse(BaseModel):
    indice: int
    modelo: str
    score_modelo: float
    classe_predita: int
    decisao: str
    probabilidade_inadimplencia: str
    atributos_derivados: AtributosDerivadosResponse


class ResumoLoteResponse(BaseModel):
    alto_risco: int
    baixo_risco: int
    taxa_inadimplencia_lote: str


class BatchPrevisaoResponse(BaseModel):
    total_solicitados: int
    resumo: ResumoLoteResponse
    previsoes: list[ItemLoteResponse]
