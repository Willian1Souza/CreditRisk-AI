import { useEffect, useState } from "react";
import { cleanNumberInput } from "./numberInput";

type Cliente = {
  SEX: number;
  EDUCATION: number;
  MARRIAGE: number;
  LIMIT_BAL: number;
  AGE: number;
  PAY_0: number;
  PAY_2: number;
  PAY_3: number;
  PAY_4: number;
  PAY_5: number;
  PAY_6: number;
  BILL_AMT1: number;
  BILL_AMT2: number;
  BILL_AMT3: number;
  BILL_AMT4: number;
  BILL_AMT5: number;
  BILL_AMT6: number;
  PAY_AMT1: number;
  PAY_AMT2: number;
  PAY_AMT3: number;
  PAY_AMT4: number;
  PAY_AMT5: number;
  PAY_AMT6: number;
};

type CampoCliente = keyof Cliente;

type CampoConfig = {
  key: CampoCliente;
  label: string;
  group: string;
  min?: number;
  max?: number;
  step?: number;
  allowDecimals?: boolean;
  allowNegative?: boolean;
};

type ScoreCredito = {
  score: number;
  faixa: string;
  rating: string;
  cor: string;
  nivel_risco: string;
  descricao: string;
  probabilidade_inadimplencia: string;
  percentual_seguranca: string;
};

type FatorSHAP = {
  feature_codigo: string;
  nome: string;
  descricao: string;
  impacto: number;
  direcao: string;
  tipo: string;
  impacto_score_pontos: number;
};

type AnaliseCompleta = {
  score_credito: ScoreCredito;
  previsao: {
    decisao: string;
    probabilidade_inadimplencia: string;
  };
  diagnostico_financeiro: {
    utilizacao_limite: { percentual: number; status: string; mensagem: string };
    comprometimento_renda: {
      dti_percentual: number | null;
      status: string;
      mensagem: string;
    };
    cobertura_pagamento: {
      percentual_coberto: number;
      status: string;
      mensagem: string;
    };
    tendencia_divida: { tendencia: string; mensagem: string };
    estresse_financeiro: { indice: number; nivel: string; cor: string };
    recomendacoes: string[];
  };
  explicabilidade_shap: {
    valor_base_modelo: number;
    top_fatores_risco: FatorSHAP[];
    top_fatores_protecao: FatorSHAP[];
  };
};

type CenarioResultado = {
  previsao: { score_modelo: number; decisao: string };
  score_credito: ScoreCredito;
  diagnostico: {
    utilizacao_limite: { percentual: number };
    comprometimento_renda: { dti_percentual: number | null };
  };
};

type ComparacaoCenarios = {
  cenario_base: CenarioResultado;
  cenario_simulado: CenarioResultado;
  comparativo: {
    delta_score: number;
    delta_probabilidade_pct: number;
    delta_utilizacao_pct: number;
    impacto_geral: string;
    resumo: string;
  };
};

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

const EXEMPLO: Cliente = {
  SEX: 2,
  EDUCATION: 2,
  MARRIAGE: 1,
  LIMIT_BAL: 50000,
  AGE: 35,
  PAY_0: 2,
  PAY_2: 1,
  PAY_3: 0,
  PAY_4: 0,
  PAY_5: 0,
  PAY_6: 0,
  BILL_AMT1: 30000,
  BILL_AMT2: 28000,
  BILL_AMT3: 25000,
  BILL_AMT4: 23000,
  BILL_AMT5: 20000,
  BILL_AMT6: 18000,
  PAY_AMT1: 2000,
  PAY_AMT2: 3000,
  PAY_AMT3: 2500,
  PAY_AMT4: 2000,
  PAY_AMT5: 1500,
  PAY_AMT6: 1000,
};

const CAMPOS: CampoConfig[] = [
  { key: "SEX", label: "Sexo (código)", group: "Cadastro", min: 1, max: 2 },
  { key: "EDUCATION", label: "Escolaridade (código)", group: "Cadastro", min: 1, max: 4 },
  { key: "MARRIAGE", label: "Estado civil (código)", group: "Cadastro", min: 1, max: 3 },
  { key: "AGE", label: "Idade", group: "Cadastro", min: 18, max: 120 },
  { key: "LIMIT_BAL", label: "Limite de crédito (R$)", group: "Crédito", min: 1, step: 100, allowDecimals: true },
  { key: "PAY_0", label: "Situação da fatura — setembro (código)", group: "Situação e atrasos da fatura", min: -2, max: 9, allowNegative: true },
  { key: "PAY_2", label: "Situação da fatura — agosto (código)", group: "Situação e atrasos da fatura", min: -2, max: 9, allowNegative: true },
  { key: "PAY_3", label: "Situação da fatura — julho (código)", group: "Situação e atrasos da fatura", min: -2, max: 9, allowNegative: true },
  { key: "PAY_4", label: "Situação da fatura — junho (código)", group: "Situação e atrasos da fatura", min: -2, max: 9, allowNegative: true },
  { key: "PAY_5", label: "Situação da fatura — maio (código)", group: "Situação e atrasos da fatura", min: -2, max: 9, allowNegative: true },
  { key: "PAY_6", label: "Situação da fatura — abril (código)", group: "Situação e atrasos da fatura", min: -2, max: 9, allowNegative: true },
  { key: "BILL_AMT1", label: "Valor da fatura de setembro (R$)", group: "Valores das faturas", step: 100, allowDecimals: true, allowNegative: true },
  { key: "BILL_AMT2", label: "Valor da fatura de agosto (R$)", group: "Valores das faturas", step: 100, allowDecimals: true, allowNegative: true },
  { key: "BILL_AMT3", label: "Valor da fatura de julho (R$)", group: "Valores das faturas", step: 100, allowDecimals: true, allowNegative: true },
  { key: "BILL_AMT4", label: "Valor da fatura de junho (R$)", group: "Valores das faturas", step: 100, allowDecimals: true, allowNegative: true },
  { key: "BILL_AMT5", label: "Valor da fatura de maio (R$)", group: "Valores das faturas", step: 100, allowDecimals: true, allowNegative: true },
  { key: "BILL_AMT6", label: "Valor da fatura de abril (R$)", group: "Valores das faturas", step: 100, allowDecimals: true, allowNegative: true },
  { key: "PAY_AMT1", label: "Valor pago em setembro (R$)", group: "Valores pagos", min: 0, step: 100, allowDecimals: true },
  { key: "PAY_AMT2", label: "Valor pago em agosto (R$)", group: "Valores pagos", min: 0, step: 100, allowDecimals: true },
  { key: "PAY_AMT3", label: "Valor pago em julho (R$)", group: "Valores pagos", min: 0, step: 100, allowDecimals: true },
  { key: "PAY_AMT4", label: "Valor pago em junho (R$)", group: "Valores pagos", min: 0, step: 100, allowDecimals: true },
  { key: "PAY_AMT5", label: "Valor pago em maio (R$)", group: "Valores pagos", min: 0, step: 100, allowDecimals: true },
  { key: "PAY_AMT6", label: "Valor pago em abril (R$)", group: "Valores pagos", min: 0, step: 100, allowDecimals: true },
];

const GRUPOS_CAMPOS = [
  "Cadastro",
  "Crédito",
  "Situação e atrasos da fatura",
  "Valores das faturas",
  "Valores pagos",
];

function mensagemErro(body: unknown) {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String(item.msg);
        }
        return String(item);
      }).join(" ");
    }
  }
  if (typeof body === "object" && body !== null && "detalhes" in body && Array.isArray(body.detalhes)) {
    return body.detalhes.map((item) => {
      if (typeof item === "object" && item !== null && "campo" in item && "mensagem" in item) {
        return `${String(item.campo)}: ${String(item.mensagem)}`;
      }
      return String(item);
    }).join(" ");
  }
  if (typeof body === "object" && body !== null && "mensagem" in body) {
    return String(body.mensagem);
  }
  return "Não foi possível concluir a solicitação. Verifique a conexão com a API.";
}

function validarPerfil(cliente: Cliente): string[] {
  const erros: string[] = [];
  if (![1, 2].includes(cliente.SEX)) erros.push("Sexo: selecione um dos valores disponíveis.");
  if (![1, 2, 3, 4].includes(cliente.EDUCATION)) erros.push("Escolaridade: selecione um dos valores disponíveis.");
  if (![1, 2, 3].includes(cliente.MARRIAGE)) erros.push("Estado civil: selecione um dos valores disponíveis.");
  if (!Number.isInteger(cliente.AGE) || cliente.AGE < 18 || cliente.AGE > 120) {
    erros.push("Idade: informe um número inteiro entre 18 e 120.");
  }
  if (!Number.isFinite(cliente.LIMIT_BAL) || cliente.LIMIT_BAL <= 0) {
    erros.push("Limite de crédito: informe um valor maior que zero.");
  }
  for (const campo of CAMPOS.filter(({ group }) => group === "Situação e atrasos da fatura")) {
    const valor = cliente[campo.key];
    if (!Number.isInteger(valor) || valor < -2 || valor > 9) {
      erros.push(`${campo.label}: use um número inteiro entre -2 e 9.`);
    }
  }
  for (const campo of CAMPOS.filter(({ group }) => group === "Valores pagos")) {
    if (!Number.isFinite(cliente[campo.key]) || cliente[campo.key] < 0) {
      erros.push(`${campo.label}: informe zero ou um valor positivo.`);
    }
  }
  for (const campo of CAMPOS.filter(({ group }) => group === "Valores das faturas")) {
    if (!Number.isFinite(cliente[campo.key])) {
      erros.push(`${campo.label}: informe um valor numérico.`);
    }
  }
  return erros;
}

function CampoNumerico({
  valor,
  onChange,
  allowDecimals,
  allowNegative,
  placeholder,
  className,
}: {
  valor: number;
  onChange: (valor: number) => void;
  allowDecimals: boolean;
  allowNegative?: boolean;
  placeholder: string;
  className: string;
}) {
  const [texto, setTexto] = useState(Number.isFinite(valor) ? String(valor) : "");

  useEffect(() => {
    if (
      Number.isFinite(valor)
      && texto !== ""
      && Number(texto) !== valor
    ) {
      setTexto(String(valor));
    }
  }, [texto, valor]);

  return (
    <input
      type="text"
      inputMode={allowDecimals ? "decimal" : "numeric"}
      value={texto}
      placeholder={placeholder}
      onFocus={(event) => event.currentTarget.select()}
      onChange={(event) => {
        const normalizado = cleanNumberInput(
          event.target.value,
          allowDecimals,
          allowNegative,
        );
        setTexto(normalizado);
        onChange(normalizado && normalizado !== "-" && normalizado !== "."
          ? Number(normalizado)
          : Number.NaN);
      }}
      className={`w-full rounded-xl border border-gray-200 bg-[#F9F8F3] px-4 py-3 font-semibold text-gray-900 transition-all focus:outline-none focus:ring-2 focus:ring-brand-dark ${className}`}
    />
  );
}

async function enviar<T>(rota: string, payload: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${rota}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body: unknown = await response.json();
  if (!response.ok) throw new Error(mensagemErro(body));
  return body as T;
}

function EditorPerfil({
  titulo,
  descricao,
  cliente,
  onChange,
  open = false,
}: {
  titulo: string;
  descricao: string;
  cliente: Cliente;
  onChange: (campo: CampoCliente, valor: number) => void;
  open?: boolean;
}) {
  return (
    <details className="rounded-2xl border border-gray-200 bg-[#FCFCF9] p-4" open={open}>
      <summary className="cursor-pointer font-semibold text-brand-dark">{titulo}</summary>
      <p className="mt-2 text-xs leading-relaxed text-gray-600">{descricao}</p>
      <div className="mt-5 space-y-5">
        {GRUPOS_CAMPOS.map((grupo) => (
          <fieldset key={grupo}>
            <legend className="mb-3 text-sm font-bold text-gray-800">{grupo}</legend>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {CAMPOS.filter((campo) => campo.group === grupo).map((campo) => (
                <label key={campo.key} className="text-xs font-medium text-gray-700">
                  {campo.label}
                  {campo.key === "SEX" || campo.key === "EDUCATION" || campo.key === "MARRIAGE" ? (
                    <select
                      value={cliente[campo.key]}
                      onChange={(event) => onChange(campo.key, Number(event.target.value))}
                      className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm"
                    >
                      {(campo.key === "SEX"
                        ? [[1, "Masculino"], [2, "Feminino"]]
                        : campo.key === "EDUCATION"
                          ? [[1, "Pós-graduação"], [2, "Universidade"], [3, "Ensino médio"], [4, "Outros"]]
                          : [[1, "Casado"], [2, "Solteiro"], [3, "Outros"]]
                      ).map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  ) : (
                    <CampoNumerico
                      valor={cliente[campo.key]}
                      allowDecimals={campo.allowDecimals ?? false}
                      allowNegative={campo.allowNegative}
                      placeholder={campo.allowDecimals ? "0.00" : "0"}
                      onChange={(valor) => onChange(campo.key, valor)}
                      className="mt-1 text-sm"
                    />
                  )}
                </label>
              ))}
            </div>
            {grupo === "Situação e atrasos da fatura" && (
              <p className="mt-2 text-xs leading-relaxed text-gray-500">
                Aqui você informa a situação, não o valor pago: -2 = sem uso, -1 = pago em dia, 0 = saldo rotativo e 1 a 9 = meses de atraso.
              </p>
            )}
            {grupo === "Valores pagos" && (
              <p className="mt-2 text-xs leading-relaxed text-gray-500">
                Informe em reais o valor efetivamente pago em cada mês. Esse valor é diferente do código de situação/atraso informado acima.
              </p>
            )}
          </fieldset>
        ))}
      </div>
    </details>
  );
}

function FatoresSHAP({ fatores }: { fatores: FatorSHAP[] }) {
  if (!fatores.length) {
    return <p className="text-sm text-gray-500">Não há fatores com impacto nessa direção para este perfil.</p>;
  }
  const maiorImpacto = Math.max(...fatores.map((fator) => Math.abs(fator.impacto)), 0.0001);
  return (
    <ul className="space-y-3">
      {fatores.map((fator) => (
        <li key={fator.feature_codigo} className="rounded-xl bg-white p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-gray-900">{fator.nome}</p>
              <p className="text-xs text-gray-500">{fator.descricao}</p>
            </div>
            <span className={`shrink-0 text-xs font-bold ${fator.impacto > 0 ? "text-rose-700" : "text-emerald-700"}`}>
              {fator.impacto > 0 ? "+" : ""}{(fator.impacto * 100).toFixed(2)} p.p.
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-100">
            <div
              className={`h-full rounded-full ${fator.impacto > 0 ? "bg-rose-500" : "bg-emerald-600"}`}
              style={{ width: `${Math.max(4, (Math.abs(fator.impacto) / maiorImpacto) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function CreditAnalysis() {
  const [cliente, setCliente] = useState<Cliente>({ ...EXEMPLO });
  const [cenario, setCenario] = useState<Cliente>({ ...EXEMPLO });
  const [renda, setRenda] = useState(4500);
  const [rendaCenario, setRendaCenario] = useState(4500);
  const [analise, setAnalise] = useState<AnaliseCompleta | null>(null);
  const [comparacao, setComparacao] = useState<ComparacaoCenarios | null>(null);
  const [erro, setErro] = useState("");
  const [carregandoAnalise, setCarregandoAnalise] = useState(false);
  const [carregandoComparacao, setCarregandoComparacao] = useState(false);

  const atualizarCliente = (
    setter: (cliente: Cliente) => void,
    atual: Cliente,
    campo: CampoCliente,
    valor: number,
  ) => setter({ ...atual, [campo]: valor });

  async function analisarPerfil() {
    setCarregandoAnalise(true);
    setErro("");
    try {
      const errosPerfil = validarPerfil(cliente);
      if (errosPerfil.length) {
        setErro(errosPerfil.join(" "));
        return;
      }
      const resultado = await enviar<AnaliseCompleta>("/analyze", {
        cliente,
        renda_mensal: renda > 0 ? renda : null,
      });
      setAnalise(resultado);
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Erro inesperado ao analisar o perfil.");
    } finally {
      setCarregandoAnalise(false);
    }
  }

  async function compararCenarios() {
    setCarregandoComparacao(true);
    setErro("");
    try {
      const errosBase = validarPerfil(cliente).map((erro) => `Perfil atual — ${erro}`);
      const errosCenario = validarPerfil(cenario).map((erro) => `Cenário simulado — ${erro}`);
      if (errosBase.length || errosCenario.length) {
        setErro([...errosBase, ...errosCenario].join(" "));
        return;
      }
      const resultado = await enviar<ComparacaoCenarios>("/scenarios/compare", {
        cenario_base: cliente,
        cenario_simulado: cenario,
        renda_base: renda > 0 ? renda : null,
        renda_simulada: rendaCenario > 0 ? rendaCenario : null,
      });
      setComparacao(resultado);
    } catch (error) {
      setErro(error instanceof Error ? error.message : "Erro inesperado ao comparar os cenários.");
    } finally {
      setCarregandoComparacao(false);
    }
  }

  return (
    <section id="analise-risco" className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 max-w-3xl space-y-3">
        <p className="text-xs font-bold uppercase tracking-wider text-emerald-700">Análise com modelo de crédito</p>
        <h2 className="text-3xl font-serif font-bold text-brand-dark sm:text-4xl">Entenda seu perfil e teste mudanças.</h2>
        <p className="text-sm leading-relaxed text-gray-600">
          Informe dados financeiros para receber a estimativa do modelo, o diagnóstico pessoal e os fatores SHAP. Os campos de cadastro são códigos usados pelo conjunto de dados do modelo; não informe nome, CPF ou outros identificadores.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-4 rounded-3xl border border-gray-100 bg-white p-5 shadow-lg sm:p-7">
          <div>
            <h3 className="text-xl font-bold text-brand-dark">Perfil atual</h3>
            <p className="mt-1 text-xs leading-relaxed text-gray-500">O modelo usa o histórico de seis meses e as variáveis demográficas disponíveis na base de treinamento.</p>
          </div>
          <label className="block text-xs font-semibold text-gray-700">
            Renda mensal (R$)
            <CampoNumerico
              valor={renda}
              allowDecimals
              placeholder="0.00"
              onChange={setRenda}
              className="mt-1 text-sm"
            />
          </label>
          <EditorPerfil
            titulo="Editar dados do perfil"
            descricao="Os três atributos derivados (atrasos e utilização do limite) são calculados automaticamente pela API."
            cliente={cliente}
            onChange={(campo, valor) => atualizarCliente(setCliente, cliente, campo, valor)}
            open
          />
          <button
            type="button"
            onClick={analisarPerfil}
            disabled={carregandoAnalise}
            className="w-full rounded-xl bg-brand-dark px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-darkHover disabled:cursor-wait disabled:opacity-60"
          >
            {carregandoAnalise ? "Analisando perfil..." : "Analisar risco e diagnóstico"}
          </button>
        </div>

        <div className="space-y-4">
          <div className="rounded-3xl border border-gray-100 bg-white p-5 shadow-lg sm:p-7">
            <h3 className="text-xl font-bold text-brand-dark">Comparar cenários</h3>
            <p className="mt-1 text-sm leading-relaxed text-gray-600">
              Edite um segundo perfil e compare a probabilidade prevista, o score e os indicadores financeiros com o perfil atual.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-semibold text-gray-700">
                Renda do cenário (R$)
                <CampoNumerico
                  valor={rendaCenario}
                  allowDecimals
                  placeholder="0.00"
                  onChange={setRendaCenario}
                  className="mt-1 text-sm"
                />
              </label>
              <button
                type="button"
                onClick={() => {
                  setCenario({ ...cliente });
                  setRendaCenario(renda);
                }}
                className="self-end rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Copiar perfil atual
              </button>
            </div>
            <div className="mt-4">
              <EditorPerfil
                titulo="Editar cenário simulado"
                descricao="Altere qualquer variável para testar o efeito estimado pelo mesmo modelo."
                cliente={cenario}
                onChange={(campo, valor) => atualizarCliente(setCenario, cenario, campo, valor)}
              />
            </div>
            <button
              type="button"
              onClick={compararCenarios}
              disabled={carregandoComparacao}
              className="mt-4 w-full rounded-xl border border-brand-dark px-5 py-3 text-sm font-semibold text-brand-dark transition hover:bg-emerald-50 disabled:cursor-wait disabled:opacity-60"
            >
              {carregandoComparacao ? "Comparando cenários..." : "Comparar previsões"}
            </button>
          </div>

          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs leading-relaxed text-amber-950">
            Esta é uma estimativa estatística baseada em uma base histórica de cartões de crédito, não uma decisão ou aprovação. A análise do modelo envia os dados numéricos informados à API configurada; esta interface não pede nome nem CPF.
          </div>
        </div>
      </div>

      {erro && (
        <div role="alert" className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          {erro}
        </div>
      )}

      {analise && (
        <div className="mt-8 space-y-5">
          <div className="grid gap-4 md:grid-cols-3">
            <article className="rounded-2xl bg-brand-dark p-5 text-white">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-200">Score de crédito estimado</p>
              <p className="mt-2 text-4xl font-bold">{analise.score_credito.score}<span className="text-lg text-emerald-200"> / 1000</span></p>
              <p className="mt-1 font-semibold">{analise.score_credito.faixa} · Rating {analise.score_credito.rating}</p>
              <p className="mt-2 text-sm text-emerald-100">{analise.score_credito.probabilidade_inadimplencia} de probabilidade prevista de inadimplência</p>
            </article>
            <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Diagnóstico financeiro</p>
              <p className="mt-2 text-xl font-bold text-brand-dark">{analise.diagnostico_financeiro.estresse_financeiro.nivel} · {analise.diagnostico_financeiro.estresse_financeiro.indice}/100</p>
              <p className="mt-2 text-sm text-gray-600">{analise.diagnostico_financeiro.utilizacao_limite.percentual}% do limite utilizado</p>
              <p className="text-sm text-gray-600">
                {analise.diagnostico_financeiro.comprometimento_renda.dti_percentual === null
                  ? "Comprometimento da renda não calculado"
                  : `${analise.diagnostico_financeiro.comprometimento_renda.dti_percentual}% da renda comprometida`}
              </p>
            </article>
            <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Previsão do modelo</p>
              <p className="mt-2 text-xl font-bold text-brand-dark">{analise.previsao.decisao}</p>
              <p className="mt-2 text-sm text-gray-600">{analise.previsao.probabilidade_inadimplencia} de inadimplência prevista</p>
              <p className="mt-1 text-xs text-gray-500">{analise.diagnostico_financeiro.comprometimento_renda.status}</p>
            </article>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-bold text-brand-dark">Diagnóstico detalhado</h3>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-gray-50 p-3">
                  <p className="text-xs font-semibold text-gray-500">Utilização do limite · {analise.diagnostico_financeiro.utilizacao_limite.status}</p>
                  <p className="mt-1 text-sm">{analise.diagnostico_financeiro.utilizacao_limite.mensagem}</p>
                </div>
                <div className="rounded-xl bg-gray-50 p-3">
                  <p className="text-xs font-semibold text-gray-500">Renda · {analise.diagnostico_financeiro.comprometimento_renda.status}</p>
                  <p className="mt-1 text-sm">{analise.diagnostico_financeiro.comprometimento_renda.mensagem}</p>
                </div>
                <div className="rounded-xl bg-gray-50 p-3">
                  <p className="text-xs font-semibold text-gray-500">Cobertura da fatura · {analise.diagnostico_financeiro.cobertura_pagamento.status}</p>
                  <p className="mt-1 text-sm">{analise.diagnostico_financeiro.cobertura_pagamento.mensagem}</p>
                </div>
                <div className="rounded-xl bg-gray-50 p-3">
                  <p className="text-xs font-semibold text-gray-500">Tendência · {analise.diagnostico_financeiro.tendencia_divida.tendencia}</p>
                  <p className="mt-1 text-sm">{analise.diagnostico_financeiro.tendencia_divida.mensagem}</p>
                </div>
              </div>
              <h4 className="mt-5 text-sm font-bold text-brand-dark">Recomendações</h4>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                {analise.diagnostico_financeiro.recomendacoes.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </article>

            <article className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-bold text-brand-dark">O que influenciou a previsão · SHAP</h3>
              <p className="mb-4 mt-1 text-xs leading-relaxed text-gray-500">
                Os impactos mostram quanto cada variável desloca a probabilidade prevista de inadimplência em relação ao valor-base do modelo. Não representam causalidade.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <h4 className="mb-2 text-sm font-semibold text-rose-800">Aumentam o risco</h4>
                  <FatoresSHAP fatores={analise.explicabilidade_shap.top_fatores_risco} />
                </div>
                <div>
                  <h4 className="mb-2 text-sm font-semibold text-emerald-800">Reduzem o risco</h4>
                  <FatoresSHAP fatores={analise.explicabilidade_shap.top_fatores_protecao} />
                </div>
              </div>
            </article>
          </div>
        </div>
      )}

      {comparacao && (
        <section className="mt-8 rounded-3xl border border-gray-100 bg-white p-5 shadow-lg sm:p-7" aria-live="polite">
          <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">Comparativo de cenários</p>
          <h3 className="mt-1 text-2xl font-bold text-brand-dark">{comparacao.comparativo.impacto_geral}</h3>
          <p className="mt-2 text-sm text-gray-600">{comparacao.comparativo.resumo}</p>
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl bg-gray-50 p-4">
              <p className="text-xs text-gray-500">Score atual → simulado</p>
              <p className="mt-1 text-lg font-bold text-brand-dark">{comparacao.cenario_base.score_credito.score} → {comparacao.cenario_simulado.score_credito.score}</p>
              <p className="text-sm">{comparacao.comparativo.delta_score > 0 ? "+" : ""}{comparacao.comparativo.delta_score} pontos</p>
            </div>
            <div className="rounded-xl bg-gray-50 p-4">
              <p className="text-xs text-gray-500">Probabilidade de inadimplência</p>
              <p className="mt-1 text-lg font-bold text-brand-dark">
                {(comparacao.cenario_base.previsao.score_modelo * 100).toFixed(2)}% → {(comparacao.cenario_simulado.previsao.score_modelo * 100).toFixed(2)}%
              </p>
              <p className="text-sm">{comparacao.comparativo.delta_probabilidade_pct > 0 ? "+" : ""}{comparacao.comparativo.delta_probabilidade_pct.toFixed(2)} pontos percentuais</p>
            </div>
            <div className="rounded-xl bg-gray-50 p-4">
              <p className="text-xs text-gray-500">Utilização do limite</p>
              <p className="mt-1 text-lg font-bold text-brand-dark">
                {comparacao.cenario_base.diagnostico.utilizacao_limite.percentual}% → {comparacao.cenario_simulado.diagnostico.utilizacao_limite.percentual}%
              </p>
              <p className="text-sm">Variação de {comparacao.comparativo.delta_utilizacao_pct.toFixed(1)} p.p.</p>
            </div>
          </div>
          <p className="mt-4 text-xs text-gray-500">
            Cenário base: {comparacao.cenario_base.score_credito.rating} · {comparacao.cenario_base.previsao.decisao}. Cenário simulado: {comparacao.cenario_simulado.score_credito.rating} · {comparacao.cenario_simulado.previsao.decisao}.
          </p>
        </section>
      )}
    </section>
  );
}
