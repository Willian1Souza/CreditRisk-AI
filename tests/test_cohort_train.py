import unittest

import pandas as pd

from src.cohort_train import (
    DATE_COLUMN,
    DENOMINATOR_COLUMN,
    TARGET_COLUMN,
    TARGET_DATE_COLUMN,
    construir_amostras_supervisionadas,
)


def _registro(data_base: str, atraso_90: int, qtd_operacoes: int = 100) -> dict:
    return {
        "Coorte": pd.Timestamp("2024-01-31"),
        "Tipo_de_Cliente": 1,
        "Modalidade": "PF - Veículos",
        "Faixa_de_Prazo_da_Operacao": ">= 2 e < 3 anos",
        DATE_COLUMN: pd.Timestamp(data_base),
        "Qtd_Atraso_30_dias": atraso_90 + 3,
        "Volume_Atraso_30_dias": 300.0,
        "Qtd_Atraso_60_dias": atraso_90 + 2,
        "Volume_Atraso_60_dias": 200.0,
        "Qtd_Atraso_90_dias": atraso_90,
        "Volume_Atraso_90_dias": atraso_90 * 100.0,
        "Qtd_Prejuizo_Acumulado": 1,
        "Volume_Prejuizo_Acumulado": 100.0,
        "Qtd_Operacoes_Excluidas_Atraso_90_E_H_Acumulado": 0,
        "Volume_Operacoes_Excluidas_Atraso_90_E_H_Acumulado": 0.0,
        DENOMINATOR_COLUMN: qtd_operacoes,
        "Valor_Operacoes_Coorte": 10000.0,
    }


class CohortTrainingTests(unittest.TestCase):
    def test_builds_next_month_target_without_using_future_denominator(self) -> None:
        dados = pd.DataFrame(
            [
                _registro("2024-10-31", atraso_90=2, qtd_operacoes=100),
                _registro("2024-11-30", atraso_90=4, qtd_operacoes=200),
            ]
        )

        amostras = construir_amostras_supervisionadas(dados)

        self.assertEqual(len(amostras), 1)
        self.assertEqual(amostras.loc[0, TARGET_COLUMN], 0.04)
        self.assertEqual(amostras.loc[0, TARGET_DATE_COLUMN], pd.Timestamp("2024-11-30"))
        self.assertEqual(amostras.loc[0, DENOMINATOR_COLUMN], 100)

    def test_does_not_create_pairs_across_missing_months(self) -> None:
        dados = pd.DataFrame(
            [
                _registro("2024-10-31", atraso_90=2),
                _registro("2024-12-31", atraso_90=4),
            ]
        )

        with self.assertRaisesRegex(ValueError, "snapshots mensais consecutivos"):
            construir_amostras_supervisionadas(dados)

    def test_uses_group_identity_when_matching_following_snapshot(self) -> None:
        first = _registro("2024-10-31", atraso_90=2)
        next_record = _registro("2024-11-30", atraso_90=4)
        next_record["Modalidade"] = "PF - Habitacional"
        dados = pd.DataFrame([first, next_record])

        with self.assertRaisesRegex(ValueError, "snapshots mensais consecutivos"):
            construir_amostras_supervisionadas(dados)


if __name__ == "__main__":
    unittest.main()
