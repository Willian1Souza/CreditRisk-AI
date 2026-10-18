# CreditRisk AI

Aplicação de análise de risco de crédito com interface web, API REST em FastAPI e modelos de machine learning. O projeto também inclui uma simulação de financiamento e um pipeline experimental para previsão de inadimplência por coortes.

> **Importante:** os resultados são estimativas para apoio à análise e não substituem avaliação profissional, validação de políticas de crédito ou revisão humana. A simulação de financiamento adapta os dados informados para as variáveis do modelo de cartão de crédito; não é um modelo treinado especificamente para aprovação de financiamentos.

## Funcionalidades

- Análise individual e em lote de risco de inadimplência em cartão de crédito.
- Cálculo e validação automática de atributos derivados do histórico de pagamentos.
- Simulação de financiamento com tabelas Price e SAC, capacidade de pagamento, regras de crédito e cenários de viabilização.
- Interface web em React e Vite.
- API documentada automaticamente pelo Swagger.
- Scripts para análise exploratória, treinamento de classificadores e avaliação experimental de dados de coortes.

## Tecnologias

- Python, pandas, scikit-learn e XGBoost
- FastAPI, Pydantic e Uvicorn
- React, TypeScript e Vite

## Pré-requisitos

- Python instalado e disponível no terminal
- Node.js e npm

## Instalação e execução

No PowerShell, a partir da pasta raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

cd Front-end
npm install
cd ..

python start.py
```

O iniciador sobe a API e a interface localmente. Quando estiver pronto, acesse:

- **Aplicação:** http://127.0.0.1:5173
- **Documentação interativa da API:** o endereço `/docs` exibido no terminal (a API escolhe uma porta disponível entre 8000 e 8099)
- **Health check:** o endereço `/health` na mesma porta da API

Para encerrar os serviços, pressione `Ctrl+C` no terminal em que `python start.py` está rodando.

### Executar os serviços separadamente

Em um terminal, inicie a API:

```powershell
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Em outro terminal, inicie o front-end:

```powershell
cd Front-end
npm run dev
```

Com essa execução separada, a interface espera a API em `http://127.0.0.1:8000`.

## API

### Endpoints principais

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/health` | Status da API e informações básicas do modelo carregado |
| `GET` | `/model/info` | Features, categorias, regras dos atributos derivados e métricas |
| `POST` | `/predict` | Predição de risco para um cliente |
| `POST` | `/predict/batch` | Predições para uma lista de clientes |
| `POST` | `/financiamento/analisar` | Análise e simulação de uma proposta de financiamento |

O Swagger mostra os schemas e permite testar cada rota em `/docs`.

### Exemplo de predição

O endpoint `/predict` recebe 23 dados brutos. Os três atributos derivados podem ser omitidos: a API os calcula. Se forem enviados, seus valores precisam ser consistentes com o histórico e com o limite informado.

```powershell
$cliente = @{
  SEX = 2
  EDUCATION = 2
  MARRIAGE = 1
  LIMIT_BAL = 50000
  AGE = 35
  PAY_0 = 2
  PAY_2 = 1
  PAY_3 = 0
  PAY_4 = 0
  PAY_5 = 0
  PAY_6 = 0
  BILL_AMT1 = 30000
  BILL_AMT2 = 28000
  BILL_AMT3 = 25000
  BILL_AMT4 = 23000
  BILL_AMT5 = 20000
  BILL_AMT6 = 18000
  PAY_AMT1 = 2000
  PAY_AMT2 = 3000
  PAY_AMT3 = 2500
  PAY_AMT4 = 2000
  PAY_AMT5 = 1500
  PAY_AMT6 = 1000
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/predict" `
  -Method Post -ContentType "application/json" -Body $cliente
```

O resultado contém a classe (`0` = baixo risco; `1` = alto risco), o score/probabilidade estimada e os atributos derivados. As categorias aceitas e as regras completas estão em `/model/info`.

Para a análise de financiamento, envie os campos obrigatórios `valor_financiado`, `salario`, `idade`, `tipo_emprego`, `estado_civil` e `comprovante_residencia`. Os demais campos, como entrada, prazo, taxa e sistema de amortização, são opcionais e têm valores padrão descritos no Swagger.

## Treinamento e análise de dados

Os artefatos do modelo de risco individual e as métricas usados pela API estão em `models/`. Para reproduzir as etapas:

```powershell
# Análise exploratória; usa o CSV local ou baixa a base do UCI Repository
python EDA.py

# Treina e compara Regressão Logística, Random Forest e XGBoost
python train.py

# Treina e avalia a previsão agregada por coortes
python train_cohort.py
```

O treinamento principal usa `data/credit_card_clients_clean.csv`, salva pipelines e métricas em `models/` e gera gráficos em `plots/`. Execute a EDA antes do treinamento se o CSV tratado não estiver disponível.

O pipeline de coortes é experimental e separado do endpoint de predição individual. Na avaliação atualmente registrada em `models/cohort_delinquency_metrics.json`, o candidato não supera o baseline do mês anterior; por isso, o pipeline não salva o modelo candidato como aprovado para uso.

## Testes

Os testes no estilo pytest podem ser executados assim (instale `pytest` no ambiente caso ainda não esteja disponível):

```powershell
python -m pip install pytest
python -m pytest
```

Os testes de API, predição e financiamento também têm scripts executáveis diretamente:

```powershell
python tests\test_api.py
python tests\test_predict.py
python tests\test_financiamento.py
```

## Estrutura do projeto

```text
api/          API, rotas e schemas de entrada/saída
src/          Predição, EDA, treinamento e lógica de financiamento
Front-end/    Interface React/TypeScript com Vite
data/         Bases de dados do projeto
models/       Modelos serializados e métricas
plots/        Gráficos da análise exploratória e avaliação
tests/        Testes automatizados
```
