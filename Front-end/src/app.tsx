import { useEffect, useState, useMemo, type FormEvent } from "react";
import {
  ShieldCheck,
  LayoutGrid,
  FileText,
  Briefcase,
  TrendingUp,
  GitBranch,
  Settings,
  HelpCircle,
  MoreHorizontal,
  Search,

  Plus,
  Download,
  Shield,
  FileCheck2,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  Filter,
  X,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Calculator,
  
  Check,
  
  Wallet,
  Gauge,
  Clock,
  
  Percent,
  Trash2,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL;

const PAYMENT_FEATURES = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"] as const;
const BILL_FEATURES = Array.from({ length: 6 }, (_, i) => `BILL_AMT${i + 1}`);
const PAID_FEATURES = Array.from({ length: 6 }, (_, i) => `PAY_AMT${i + 1}`);

const MONTHS: Record<string, string> = {
  PAY_0: "Setembro",
  PAY_2: "Agosto",
  PAY_3: "Julho",
  PAY_4: "Junho",
  PAY_5: "Maio",
  PAY_6: "Abril",
};

const PAYMENT_STATUSES = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8];
const PAYMENT_LABELS: Record<number, string> = {
  [-2]: "-2 - Sem uso no mês",
  [-1]: "-1 - Pagamento em dia",
  0: "0 - Uso de crédito rotativo",
  1: "1 - 1 mês de atraso",
  2: "2 - 2 meses de atraso",
  3: "3 - 3 meses de atraso",
};

type NumericData = Record<string, number>;

interface PrevisaoApiResponse {
  modelo: string;
  score_modelo: number;
  classe_predita: number;
  decisao: string;
  probabilidade_inadimplencia: string;
  atributos_derivados?: {
    MAX_ATRASO_6M: number;
    QTD_MESES_ATRASO: number;
    TAXA_UTILIZACAO_LIMITE: number;
  };
}

interface AnaliseItem {
  id: string;
  cliente: string;
  documento: string;
  valorSolicitado: number;
  score: number;
  pdEstimada: string;
  decisao: "Baixo Risco" | "Alto Risco" | "Em Análise";
  data: string;
}

interface FinanciamentoApiResponse {
  cliente: {
    nome: string;
    cpf: string;
    idade: number;
    estado_civil: string;
    tipo_emprego: string;
    tempo_emprego_meses: number;
    salario_mensal: number;
    comprovante_residencia: boolean;
  };
  financiamento: {
    tipo_financiamento: string;
    valor_total_bem: number;
    valor_entrada: number;
    percentual_entrada: number;
    saldo_financiado: number;
    ltv_percentual: number;
    prazo_meses: number;
    taxa_juros_anual: number;
    taxa_juros_mensal_pct: number;
    sistema_amortizacao: string;
    valor_parcela: number;
    total_a_pagar: number;
    total_juros: number;
  };
  capacidade_pagamento: {
    salario_mensal: number;
    valor_parcela: number;
    comprometimento_renda_pct: number;
    margem_maxima_30pct: number;
    margem_tolerancia_35pct: number;
    margem_disponivel: number;
    idade_final_financiamento: number;
  };
  inteligencia_artificial: {
    modelo: string;
    score_inadimplencia: number;
    probabilidade_inadimplencia: string;
    faixa_risco: string;
  };
  resultado_decisao: {
    aprovado: boolean;
    status_decisao: string;
    parecer_resumo: string;
    pontos_positivos: string[];
    condicoes_aprovacao: string[];
    motivos_reprovacao: string[];
  };
  checklist_politica_credito: Record<
    string,
    {
      status: string;
      descricao: string;
      critico: boolean;
    }
  >;
  viabilizacao_credito: {
    entrada_minima_para_aprovar?: number | null;
    percentual_entrada_minima?: number | null;
    prazo_sugerido_meses?: number | null;
    salario_minimo_necessario?: number | null;
  };
}

interface FinanciamentoHistoricoItem {
  id: string;
  cliente: string;
  cpf: string;
  tipo: string;
  valorTotal: number;
  valorEntrada: number;
  saldoFinanciado: number;
  salario: number;
  parcela: number;
  dti: number;
  scoreIa: number;
  status: "Aprovado" | "Aprovado com Condições" | "Reprovado";
  data: string;
}

const ANALISES_INICIAIS: AnaliseItem[] = [
  {
    id: "AN-1092",
    cliente: "Lucas de Oliveira",
    documento: "341.***.***-18",
    valorSolicitado: 45000,
    score: 0.12,
    pdEstimada: "1,20%",
    decisao: "Baixo Risco",
    data: "Hoje, 14:32",
  },
  {
    id: "AN-1091",
    cliente: "Mariana Costa Silva",
    documento: "812.***.***-45",
    valorSolicitado: 120000,
    score: 0.18,
    pdEstimada: "2,45%",
    decisao: "Baixo Risco",
    data: "Hoje, 11:15",
  },
  {
    id: "AN-1090",
    cliente: "Roberto Carlos Almeida",
    documento: "198.***.***-90",
    valorSolicitado: 85000,
    score: 0.74,
    pdEstimada: "14,80%",
    decisao: "Alto Risco",
    data: "Ontem, 16:40",
  },
  {
    id: "AN-1089",
    cliente: "Beatriz Santos Ferreira",
    documento: "524.***.***-63",
    valorSolicitado: 30000,
    score: 0.08,
    pdEstimada: "0,95%",
    decisao: "Baixo Risco",
    data: "Ontem, 10:20",
  },
];

const FINANCIAMENTOS_INICIAIS: FinanciamentoHistoricoItem[] = [
  {
    id: "FIN-8041",
    cliente: "Gabriel Sampaio Rocha",
    cpf: "219.***.***-44",
    tipo: "Veículo",
    valorTotal: 85000,
    valorEntrada: 20000,
    saldoFinanciado: 65000,
    salario: 8200,
    parcela: 1763.76,
    dti: 21.5,
    scoreIa: 0.114,
    status: "Aprovado",
    data: "Hoje, 15:40",
  },
  {
    id: "FIN-8040",
    cliente: "Patrícia Nogueira Lima",
    cpf: "492.***.***-12",
    tipo: "Imóvel",
    valorTotal: 280000,
    valorEntrada: 30000,
    saldoFinanciado: 250000,
    salario: 9500,
    parcela: 3120.45,
    dti: 32.8,
    scoreIa: 0.228,
    status: "Aprovado com Condições",
    data: "Hoje, 11:10",
  },
  {
    id: "FIN-8039",
    cliente: "Marcos Vinícius Prado",
    cpf: "883.***.***-05",
    tipo: "Veículo",
    valorTotal: 120000,
    valorEntrada: 0,
    saldoFinanciado: 120000,
    salario: 4200,
    parcela: 3256.17,
    dti: 77.5,
    scoreIa: 0.542,
    status: "Reprovado",
    data: "Ontem, 17:05",
  },
];

function getInitialFormData(): NumericData {
  return {
    SEX: 1,
    EDUCATION: 2,
    MARRIAGE: 2,
    LIMIT_BAL: 50000,
    AGE: 32,
    PAY_0: 0,
    PAY_2: 0,
    PAY_3: 0,
    PAY_4: 0,
    PAY_5: 0,
    PAY_6: 0,
    BILL_AMT1: 12000,
    BILL_AMT2: 11500,
    BILL_AMT3: 10000,
    BILL_AMT4: 9500,
    BILL_AMT5: 8000,
    BILL_AMT6: 7500,
    PAY_AMT1: 12000,
    PAY_AMT2: 11500,
    PAY_AMT3: 10000,
    PAY_AMT4: 9500,
    PAY_AMT5: 8000,
    PAY_AMT6: 7500,
  };
}

export default function CreditRiskApp() {
  const [activeTab, setActiveTab] = useState<"overview" | "financing" | "analyses">("overview");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [periodo, setPeriodo] = useState("30 dias");

  // Status da API e Modelo
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [modelName, setModelName] = useState("Random Forest");
  const [analyses, setAnalyses] = useState<AnaliseItem[]>(ANALISES_INICIAIS);

  // Form State - Análise de Cartão / Inadimplência Legada
  const [formData, setFormData] = useState<NumericData>(getInitialFormData);
  const [clientName, setClientName] = useState("Novo Cliente");
  const [clientDoc, setClientDoc] = useState("123.456.789-00");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [predictionResult, setPredictionResult] = useState<PrevisaoApiResponse | null>(null);
  const [formError, setFormError] = useState("");

  // ==========================================
  // ESTADO DA ANÁLISE DE FINANCIAMENTO (NOVO)
  // ==========================================
  const [finValorTotal, setFinValorTotal] = useState<number>(85000);
  const [finEntrada, setFinEntrada] = useState<number | "">(20000);
  const [finSemEntrada, setFinSemEntrada] = useState<boolean>(false);
  const [finSalario, setFinSalario] = useState<number>(7500);
  const [finIdade, setFinIdade] = useState<number>(33);
  const [finTipoEmprego, setFinTipoEmprego] = useState<string>("CLT");
  const [finTempoEmprego, setFinTempoEmprego] = useState<number>(24);
  const [finEstadoCivil, setFinEstadoCivil] = useState<string>("Casado");
  const [finComprovanteResidencia, setFinComprovanteResidencia] = useState<boolean>(true);
  const [finPrazoMeses, setFinPrazoMeses] = useState<number>(48);
  const [finTaxaJuros, setFinTaxaJuros] = useState<number>(14.5);
  const [finSistemaAmort, setFinSistemaAmort] = useState<"PRICE" | "SAC">("PRICE");
  const [finTipoBem, setFinTipoBem] = useState<string>("Veículo");
  const [finNomeCliente, setFinNomeCliente] = useState<string>("Ana Beatriz Souza");
  const [finCpfCliente, setFinCpfCliente] = useState<string>("342.781.905-22");

  const [isFinancingLoading, setIsFinancingLoading] = useState(false);
  const [financingError, setFinancingError] = useState("");
  const [financingResult, setFinancingResult] = useState<FinanciamentoApiResponse | null>(null);
  const [financingHistory, setFinancingHistory] =
    useState<FinanciamentoHistoricoItem[]>(FINANCIAMENTOS_INICIAIS);

  function handleDeleteFinancing(id: string, cliente: string) {
    if (!window.confirm(`Deseja excluir a proposta de financiamento de ${cliente}?`)) {
      return;
    }

    setFinancingHistory((prev) => prev.filter((item) => item.id !== id));
  }

  function handleClearFinancingHistory() {
    if (
      !window.confirm(
        `Deseja excluir todas as ${financingHistory.length} propostas do histórico de financiamentos?`,
      )
    ) {
      return;
    }

    setFinancingHistory([]);
  }

  // Checa status da API ao montar
  useEffect(() => {
    const controller = new AbortController();
    async function carregarStatusApi() {
      try {
        const [healthResponse, modelResponse] = await Promise.all([
          fetch(`${API_URL}/health`, { signal: controller.signal }),
          fetch(`${API_URL}/model/info`, { signal: controller.signal }),
        ]);
        if (!healthResponse.ok || !modelResponse.ok) {
          throw new Error("API indisponível");
        }

        const health = (await healthResponse.json()) as { status?: string };
        const dados = (await modelResponse.json()) as { modelo?: string };
        if (health.status === "online") {
          setApiOnline(true);
          if (dados.modelo) setModelName(dados.modelo);
        }
      } catch {
        if (!controller.signal.aborted) setApiOnline(false);
      }
    }

    void carregarStatusApi();

    return () => controller.abort();
  }, []);

  function handleUpdateField(field: string, val: number) {
    setFormData((prev) => ({ ...prev, [field]: val }));
  }

  function handleApplyPreset(type: "saudavel" | "risco") {
    if (type === "saudavel") {
      setClientName("Camila Rodrigues");
      setClientDoc("452.889.123-04");
      setFormData({
        SEX: 2,
        EDUCATION: 1,
        MARRIAGE: 1,
        LIMIT_BAL: 80000,
        AGE: 38,
        PAY_0: -1,
        PAY_2: -1,
        PAY_3: -1,
        PAY_4: -1,
        PAY_5: -1,
        PAY_6: -1,
        BILL_AMT1: 8500,
        BILL_AMT2: 8000,
        BILL_AMT3: 7200,
        BILL_AMT4: 6900,
        BILL_AMT5: 6400,
        BILL_AMT6: 5800,
        PAY_AMT1: 8500,
        PAY_AMT2: 8000,
        PAY_AMT3: 7200,
        PAY_AMT4: 6900,
        PAY_AMT5: 6400,
        PAY_AMT6: 5800,
      });
    } else {
      setClientName("Fernando Mendes");
      setClientDoc("761.340.912-88");
      setFormData({
        SEX: 1,
        EDUCATION: 3,
        MARRIAGE: 2,
        LIMIT_BAL: 20000,
        AGE: 29,
        PAY_0: 2,
        PAY_2: 2,
        PAY_3: 1,
        PAY_4: 0,
        PAY_5: 0,
        PAY_6: 0,
        BILL_AMT1: 19800,
        BILL_AMT2: 19500,
        BILL_AMT3: 18900,
        BILL_AMT4: 17200,
        BILL_AMT5: 16000,
        BILL_AMT6: 15400,
        PAY_AMT1: 500,
        PAY_AMT2: 0,
        PAY_AMT3: 1000,
        PAY_AMT4: 500,
        PAY_AMT5: 400,
        PAY_AMT6: 300,
      });
    }
  }

  // Predefinições rápidas para a Análise de Financiamento
  function handleApplyFinancingPreset(
    preset: "aprovado" | "sem_entrada" | "reprovado_renda" | "sem_comprovante",
  ) {
    setFinancingError("");
    if (preset === "aprovado") {
      setFinNomeCliente("Juliana Fernandes");
      setFinCpfCliente("512.903.441-89");
      setFinTipoBem("Veículo");
      setFinValorTotal(90000);
      setFinEntrada(25000);
      setFinSemEntrada(false);
      setFinSalario(8500);
      setFinIdade(34);
      setFinTipoEmprego("CLT");
      setFinTempoEmprego(36);
      setFinEstadoCivil("Casado");
      setFinComprovanteResidencia(true);
      setFinPrazoMeses(48);
      setFinTaxaJuros(14.5);
      setFinSistemaAmort("PRICE");
    } else if (preset === "sem_entrada") {
      setFinNomeCliente("Rodrigo Barreto");
      setFinCpfCliente("789.123.654-00");
      setFinTipoBem("Veículo");
      setFinValorTotal(50000);
      setFinEntrada(0);
      setFinSemEntrada(true);
      setFinSalario(9000);
      setFinIdade(29);
      setFinTipoEmprego("Servidor Público");
      setFinTempoEmprego(48);
      setFinEstadoCivil("Solteiro");
      setFinComprovanteResidencia(true);
      setFinPrazoMeses(48);
      setFinTaxaJuros(13.8);
      setFinSistemaAmort("PRICE");
    } else if (preset === "reprovado_renda") {
      setFinNomeCliente("Carlos Eduardo Castro");
      setFinCpfCliente("199.456.882-31");
      setFinTipoBem("Imóvel");
      setFinValorTotal(220000);
      setFinEntrada(15000);
      setFinSemEntrada(false);
      setFinSalario(4200);
      setFinIdade(41);
      setFinTipoEmprego("Autônomo");
      setFinTempoEmprego(14);
      setFinEstadoCivil("Divorciado");
      setFinComprovanteResidencia(true);
      setFinPrazoMeses(48);
      setFinTaxaJuros(15.2);
      setFinSistemaAmort("PRICE");
    } else if (preset === "sem_comprovante") {
      setFinNomeCliente("Thiago Alves Muniz");
      setFinCpfCliente("634.821.503-77");
      setFinTipoBem("Crédito Pessoal");
      setFinValorTotal(60000);
      setFinEntrada(15000);
      setFinSemEntrada(false);
      setFinSalario(7500);
      setFinIdade(28);
      setFinTipoEmprego("CLT");
      setFinTempoEmprego(18);
      setFinEstadoCivil("Solteiro");
      setFinComprovanteResidencia(false); // Pendente
      setFinPrazoMeses(36);
      setFinTaxaJuros(14.5);
      setFinSistemaAmort("PRICE");
    }
  }

  // Executa Análise do Financiamento
  async function handleFinancingSubmit(e?: FormEvent) {
    if (e) e.preventDefault();
    setIsFinancingLoading(true);
    setFinancingError("");

    const entradaValor = finSemEntrada ? null : finEntrada === "" ? 0 : Number(finEntrada);

    const payload = {
      valor_financiado: Number(finValorTotal),
      valor_entrada: entradaValor,
      salario: Number(finSalario),
      idade: Number(finIdade),
      tipo_emprego: finTipoEmprego,
      tempo_emprego_meses: Number(finTempoEmprego),
      estado_civil: finEstadoCivil,
      comprovante_residencia: Boolean(finComprovanteResidencia),
      prazo_meses: Number(finPrazoMeses),
      taxa_juros_anual: Number(finTaxaJuros),
      sistema_amortizacao: finSistemaAmort,
      tipo_financiamento: finTipoBem,
      nome_cliente: finNomeCliente,
      cpf_cliente: finCpfCliente,
    };

    try {
      const response = await fetch(`${API_URL}/financiamento/analisar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const body = await response.json();
      if (!response.ok) {
        const errorMsg =
          typeof body.detail === "string"
            ? body.detail
            : body.mensagem || "Erro ao processar análise do financiamento.";
        throw new Error(errorMsg);
      }

      const res = body as FinanciamentoApiResponse;
      setFinancingResult(res);

      // Adiciona ao histórico de financiamentos
      const novoFin: FinanciamentoHistoricoItem = {
        id: `FIN-${Math.floor(8000 + Math.random() * 1999)}`,
        cliente: res.cliente.nome,
        cpf: res.cliente.cpf,
        tipo: res.financiamento.tipo_financiamento,
        valorTotal: res.financiamento.valor_total_bem,
        valorEntrada: res.financiamento.valor_entrada,
        saldoFinanciado: res.financiamento.saldo_financiado,
        salario: res.capacidade_pagamento.salario_mensal,
        parcela: res.financiamento.valor_parcela,
        dti: res.capacidade_pagamento.comprometimento_renda_pct,
        scoreIa: res.inteligencia_artificial.score_inadimplencia,
        status: res.resultado_decisao.status_decisao as
          | "Aprovado"
          | "Aprovado com Condições"
          | "Reprovado",
        data: "Agora mesmo",
      };

      setFinancingHistory((prev) => [novoFin, ...prev]);
    } catch (err) {
      setFinancingError(
        err instanceof Error ? err.message : "Erro desconhecido na análise de financiamento.",
      );
    } finally {
      setIsFinancingLoading(false);
    }
  }

  async function handleFormSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError("");
    setPredictionResult(null);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dados: formData }),
      });

      const body = await response.json();
      if (!response.ok) {
        const errorMsg =
          typeof body.detail === "string"
            ? body.detail
            : body.mensagem || "Erro ao processar análise.";
        throw new Error(errorMsg);
      }

      const res = body as PrevisaoApiResponse;
      setPredictionResult(res);

      // Adiciona à lista de análises recentes
      const novaAnalise: AnaliseItem = {
        id: `AN-${Math.floor(1000 + Math.random() * 9000)}`,
        cliente: clientName || "Cliente Analisado",
        documento: clientDoc || "000.***.***-00",
        valorSolicitado: formData.LIMIT_BAL,
        score: res.score_modelo,
        pdEstimada: res.probabilidade_inadimplencia,
        decisao: res.decisao === "Alto Risco" ? "Alto Risco" : "Baixo Risco",
        data: "Agora mesmo",
      };

      setAnalyses((prev) => [novaAnalise, ...prev]);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro desconhecido na predição.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const filteredAnalyses = useMemo(() => {
    if (!searchTerm.trim()) return analyses;
    const term = searchTerm.toLowerCase();
    return analyses.filter(
      (a) =>
        a.cliente.toLowerCase().includes(term) ||
        a.documento.toLowerCase().includes(term) ||
        a.id.toLowerCase().includes(term),
    );
  }, [analyses, searchTerm]);

  const filteredFinancing = useMemo(() => {
    if (!searchTerm.trim()) return financingHistory;
    const term = searchTerm.toLowerCase();
    return financingHistory.filter(
      (f) =>
        f.cliente.toLowerCase().includes(term) ||
        f.cpf.toLowerCase().includes(term) ||
        f.id.toLowerCase().includes(term),
    );
  }, [financingHistory, searchTerm]);

  return (
    <div className="bg-[#f8fafc] text-slate-800 flex h-screen overflow-hidden">
      {/* SIDEBAR */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between p-4 flex-shrink-0">
        <div>
          {/* Logo */}
          <div className="flex items-center gap-3 px-2 py-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-bold shadow-sm shadow-emerald-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 leading-none text-base">
                CreditRisk <span className="text-emerald-500">AI</span>
              </h1>
              <span className="text-[10px] tracking-wider text-slate-400 font-semibold uppercase">
                Inteligência de Risco
              </span>
            </div>
          </div>

          {/* Navigation: Workspace */}
          <div className="mb-6">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2">
              Workspace
            </p>
            <nav className="space-y-1">
              {/* Aba Visão Geral */}
              <button
                type="button"
                onClick={() => setActiveTab("overview")}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  activeTab === "overview"
                    ? "bg-emerald-50 text-emerald-600"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <LayoutGrid className="w-4 h-4" />
                  <span>Visão geral</span>
                </div>
              </button>

              {/* Aba Financiamento (NOVA E PRINCIPAL) */}
              <button
                type="button"
                onClick={() => setActiveTab("financing")}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  activeTab === "financing"
                    ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/30"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Calculator className="w-4 h-4" />
                  <span className="font-semibold">Financiamento</span>
                </div>
                <span
                  className={`text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full ${
                    activeTab === "financing"
                      ? "bg-white text-emerald-700"
                      : "bg-emerald-100 text-emerald-700"
                  }`}
                >
                  Novo
                </span>
              </button>

              {/* Aba Análises de Cartão */}
              <button
                type="button"
                onClick={() => setActiveTab("analyses")}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  activeTab === "analyses"
                    ? "bg-emerald-50 text-emerald-600"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4" />
                  <span>Cartões / Inadimplência</span>
                </div>
                <span className="bg-slate-100 text-slate-500 text-xs px-2 py-0.5 rounded-full font-semibold">
                  {analyses.length}
                </span>
              </button>

              <button
                type="button"
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-50 font-medium text-sm transition-colors text-left"
              >
                <Briefcase className="w-4 h-4" />
                <span>Carteira</span>
              </button>

              <button
                type="button"
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-50 font-medium text-sm transition-colors text-left"
              >
                <TrendingUp className="w-4 h-4" />
                <span>Cenários</span>
              </button>

              <button
                type="button"
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-50 font-medium text-sm transition-colors text-left"
              >
                <GitBranch className="w-4 h-4" />
                <span>Modelos</span>
              </button>
            </nav>
          </div>

          {/* Navigation: Sistema */}
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2">
              Sistema
            </p>
            <nav className="space-y-1">
              <button
                type="button"
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-50 font-medium text-sm transition-colors text-left"
              >
                <Settings className="w-4 h-4" />
                <span>Configurações</span>
              </button>
              <button
                type="button"
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-50 font-medium text-sm transition-colors text-left"
              >
                <HelpCircle className="w-4 h-4" />
                <span>Central de ajuda</span>
              </button>
            </nav>
          </div>
        </div>

        {/* Status do Modelo e Perfil do Utilizador */}
        <div className="space-y-4">
          <div className="p-3 bg-emerald-50/60 border border-emerald-100 rounded-2xl">
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`w-2 h-2 rounded-full ${
                  apiOnline === false ? "bg-amber-500" : "bg-emerald-500 animate-pulse"
                }`}
              />
              <span className="text-xs font-semibold text-emerald-900">
                {apiOnline === false ? "Modelo offline (local)" : "Modelo operacional"}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 truncate" title={modelName}>
              {apiOnline === false ? "API desconectada" : `${modelName} Ativo`}
            </p>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-xs">
                CM
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800 leading-tight">Carolina Mendes</p>
                <p className="text-xs text-slate-400">Analista sênior</p>
              </div>
            </div>
            <button
              type="button"
              className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              aria-label="Opções do usuário"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* HEADER / TOPBAR */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10">
          {/* Search Bar */}
          <div className="relative w-96">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar cliente, CPF ou proposta..."
              className="w-full pl-9 pr-12 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-slate-400 border border-slate-200 rounded px-1.5 py-0.5 bg-white">
              ⌘ K
            </span>
          </div>

          {/* Header Right Actions */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-100 text-emerald-700 px-3 py-1.5 rounded-full text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>Motor de Risco Online</span>
            </div>

            <button
              type="button"
              onClick={() => setActiveTab("financing")}
              className={`flex items-center gap-2 font-medium text-xs px-3.5 py-2 rounded-xl transition-all ${
                activeTab === "financing"
                  ? "bg-slate-900 text-white"
                  : "bg-emerald-50 border border-emerald-200 text-emerald-700 hover:bg-emerald-100"
              }`}
            >
              <Calculator className="w-3.5 h-3.5" />
              <span>Simular Financiamento</span>
            </button>

            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs px-3.5 py-2 rounded-xl transition-all shadow-sm shadow-emerald-600/20 active:scale-95"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Nova Análise (Cartão)</span>
            </button>
          </div>
        </header>

        {/* CONTENT BODY */}
        <main className="p-8 space-y-6">
          {/* ======================================================== */}
          {/* VIEW 1: ANÁLISE DE FINANCIAMENTO (NOVA TELA PRINCIPAL)   */}
          {/* ======================================================== */}
          {activeTab === "financing" && (
            <div className="space-y-6 animate-fade-in">
              {/* Header da Aba Financiamento */}
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                  <div className="inline-flex items-center gap-2 text-xs font-bold tracking-wider text-emerald-600 uppercase bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100 mb-2">
                    <Calculator className="w-3.5 h-3.5" />
                    <span>Módulo do Analista de Crédito • Financiamentos</span>
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900">
                    Análise e Simulação de Aprovação de Financiamento
                  </h2>
                  <p className="text-sm text-slate-500 mt-1 max-w-3xl">
                    Insira as métricas do proponente (valor do bem, emprego, salário, idade, valor
                    de entrada ou nulo, estado civil e comprovante de residência) para avaliar
                    automaticamente o comprometimento de renda (DTI), LTV e o score de IA.
                  </p>
                </div>

                {/* Preenchimento Rápido com Presets */}
                <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-sm flex flex-col gap-1.5 flex-shrink-0">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Cenários de Teste do Analista:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleApplyFinancingPreset("aprovado")}
                      className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-lg border border-emerald-200 transition-colors flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      CLT Aprovado
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApplyFinancingPreset("sem_entrada")}
                      className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold rounded-lg border border-amber-200 transition-colors flex items-center gap-1"
                    >
                      <Percent className="w-3 h-3 text-amber-600" />
                      Sem Entrada (100%)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApplyFinancingPreset("reprovado_renda")}
                      className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-800 text-xs font-semibold rounded-lg border border-rose-200 transition-colors flex items-center gap-1"
                    >
                      <AlertCircle className="w-3 h-3 text-rose-600" />
                      Reprovado por Renda
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApplyFinancingPreset("sem_comprovante")}
                      className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 transition-colors flex items-center gap-1"
                    >
                      <Clock className="w-3 h-3 text-slate-500" />
                      Sem Comprovante
                    </button>
                  </div>
                </div>
              </div>

              {/* Grid Principal: Formulário à Esquerda, Resultados à Direita */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* COLUNA ESQUERDA: FORMULÁRIO DO ANALISTA (5 COLUNAS) */}
                <div className="lg:col-span-5 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                        <Wallet className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">
                          Dados da Operação e Tomador
                        </h3>
                        <p className="text-xs text-slate-400">
                          Parâmetros submetidos para cálculo
                        </p>
                      </div>
                    </div>
                  </div>

                  <form onSubmit={handleFinancingSubmit} className="space-y-4">
                    {/* Bloco 1: Proponente */}
                    <div className="space-y-3 bg-slate-50/70 p-3.5 rounded-xl border border-slate-100">
                      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        1. Identificação e Perfil Cadastral
                      </p>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Nome Completo
                          </label>
                          <input
                            type="text"
                            required
                            value={finNomeCliente}
                            onChange={(e) => setFinNomeCliente(e.target.value)}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-medium"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            CPF
                          </label>
                          <input
                            type="text"
                            required
                            value={finCpfCliente}
                            onChange={(e) => setFinCpfCliente(e.target.value)}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-mono"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Idade (anos)
                          </label>
                          <input
                            type="number"
                            min={18}
                            max={100}
                            required
                            value={finIdade}
                            onChange={(e) => setFinIdade(Number(e.target.value))}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Estado Civil
                          </label>
                          <select
                            value={finEstadoCivil}
                            onChange={(e) => setFinEstadoCivil(e.target.value)}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                          >
                            <option value="Solteiro">Solteiro(a)</option>
                            <option value="Casado">Casado(a)</option>
                            <option value="União Estável">União Estável</option>
                            <option value="Divorciado">Divorciado(a)</option>
                            <option value="Viúvo">Viúvo(a)</option>
                          </select>
                        </div>
                      </div>

                      {/* Emprego e Salário */}
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Emprego / Vínculo
                          </label>
                          <select
                            value={finTipoEmprego}
                            onChange={(e) => setFinTipoEmprego(e.target.value)}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-medium"
                          >
                            <option value="CLT">CLT (Carteira Assinada)</option>
                            <option value="Servidor Público">Servidor Público / Concursado</option>
                            <option value="Aposentado / Pensionista">
                              Aposentado / Pensionista INSS
                            </option>
                            <option value="Autônomo / Liberal">
                              Autônomo / Profissional Liberal
                            </option>
                            <option value="Empresário / MEI / PJ">Empresário / PJ / MEI</option>
                            <option value="Desempregado">Sem Renda Comprovada</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Tempo no Emprego (meses)
                          </label>
                          <input
                            type="number"
                            min={0}
                            max={600}
                            value={finTempoEmprego}
                            onChange={(e) => setFinTempoEmprego(Number(e.target.value))}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Salário / Renda Mensal Líquida (R$)
                        </label>
                        <div className="relative">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
                            R$
                          </span>
                          <input
                            type="number"
                            step={100}
                            min={500}
                            required
                            value={finSalario}
                            onChange={(e) => setFinSalario(Number(e.target.value))}
                            className="w-full text-sm font-bold text-slate-900 pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                          />
                        </div>
                      </div>

                      {/* Comprovante de Residência (Obrigatório / Verificação) */}
                      <div className="pt-1">
                        <label className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-xl cursor-pointer hover:border-emerald-300 transition-colors">
                          <div className="flex items-center gap-2.5">
                            <div
                              className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                                finComprovanteResidencia
                                  ? "bg-emerald-50 text-emerald-600"
                                  : "bg-rose-50 text-rose-500"
                              }`}
                            >
                              <FileCheck2 className="w-4 h-4" />
                            </div>
                            <div>
                              <p className="text-xs font-bold text-slate-800 leading-tight">
                                Comprovante de Residência
                              </p>
                              <p className="text-[11px] text-slate-400">
                                {finComprovanteResidencia
                                  ? "Apresentado e Válido (< 90 dias)"
                                  : "Não apresentado / Pendente"}
                              </p>
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            checked={finComprovanteResidencia}
                            onChange={(e) => setFinComprovanteResidencia(e.target.checked)}
                            className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500 cursor-pointer"
                          />
                        </label>
                      </div>
                    </div>

                    {/* Bloco 2: Valores do Financiamento e Entrada */}
                    <div className="space-y-3 bg-slate-50/70 p-3.5 rounded-xl border border-slate-100">
                      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        2. Condições do Financiamento
                      </p>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Tipo de Financiamento
                          </label>
                          <select
                            value={finTipoBem}
                            onChange={(e) => setFinTipoBem(e.target.value)}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg"
                          >
                            <option value="Veículo">Financiamento de Veículo</option>
                            <option value="Imóvel">Financiamento Imobiliário</option>
                            <option value="Crédito Pessoal">Crédito Pessoal</option>
                            <option value="Equipamento">Máquinas & Equipamentos</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Prazo (meses)
                          </label>
                          <select
                            value={finPrazoMeses}
                            onChange={(e) => setFinPrazoMeses(Number(e.target.value))}
                            className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg font-semibold text-slate-800"
                          >
                            <option value={12}>12x (1 ano)</option>
                            <option value={24}>24x (2 anos)</option>
                            <option value={36}>36x (3 anos)</option>
                            <option value={48}>48x (4 anos)</option>
                            <option value={60}>60x (5 anos)</option>
                            <option value={72}>72x (6 anos)</option>
                            <option value={120}>120x (10 anos)</option>
                            <option value={240}>240x (20 anos)</option>
                            <option value={360}>360x (30 anos)</option>
                          </select>
                        </div>
                      </div>

                      {/* Valor a ser Financiado */}
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Valor Total do Bem / Crédito (R$)
                        </label>
                        <div className="relative">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
                            R$
                          </span>
                          <input
                            type="number"
                            step={1000}
                            min={1000}
                            required
                            value={finValorTotal}
                            onChange={(e) => setFinValorTotal(Number(e.target.value))}
                            className="w-full text-base font-extrabold text-slate-900 pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                          />
                        </div>
                      </div>

                      {/* Valor de Entrada (Aceita Nulo / 0) */}
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-xs font-semibold text-slate-700">
                            Valor de Entrada (R$ ou Nulo)
                          </label>
                          <button
                            type="button"
                            onClick={() => {
                              const novoSemEntrada = !finSemEntrada;
                              setFinSemEntrada(novoSemEntrada);
                              if (novoSemEntrada) setFinEntrada(0);
                              else setFinEntrada(Math.round(finValorTotal * 0.2));
                            }}
                            className={`text-[11px] font-bold px-2 py-0.5 rounded transition-colors ${
                              finSemEntrada
                                ? "bg-amber-100 text-amber-800 border border-amber-300"
                                : "text-slate-500 hover:text-emerald-700 bg-slate-100"
                            }`}
                          >
                            {finSemEntrada ? "✓ Sem Entrada (100% Financiado)" : "Zerar Entrada (Nulo)"}
                          </button>
                        </div>

                        {!finSemEntrada ? (
                          <div className="space-y-2">
                            <div className="relative">
                              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">
                                R$
                              </span>
                              <input
                                type="number"
                                step={500}
                                min={0}
                                max={finValorTotal - 1}
                                value={finEntrada}
                                onChange={(e) => setFinEntrada(Number(e.target.value))}
                                className="w-full text-sm font-semibold text-slate-800 pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                              />
                            </div>
                            <div className="flex gap-1.5 text-[11px]">
                              {[10, 20, 30, 40].map((pct) => (
                                <button
                                  key={pct}
                                  type="button"
                                  onClick={() => setFinEntrada(Math.round(finValorTotal * (pct / 100)))}
                                  className="px-2 py-0.5 bg-white border border-slate-200 text-slate-600 rounded hover:bg-slate-50 font-medium"
                                >
                                  {pct}% (R$ {((finValorTotal * pct) / 100).toLocaleString("pt-BR")})
                                </button>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="p-2.5 bg-amber-50/80 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-600" />
                            <span>
                              Operação sem valor de entrada (LTV = 100%). O saldo a financiar será o valor total.
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-3 pt-1">
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                            Taxa de Juros Nominal (% a.a.)
                          </label>
                          <input
                            type="number"
                            step={0.1}
                            min={0}
                            value={finTaxaJuros}
                            onChange={(e) => setFinTaxaJuros(Number(e.target.value))}
                            className="w-full text-xs px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                            Tabela / Amortização
                          </label>
                          <select
                            value={finSistemaAmort}
                            onChange={(e) => setFinSistemaAmort(e.target.value as "PRICE" | "SAC")}
                            className="w-full text-xs px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg"
                          >
                            <option value="PRICE">Price (Parcelas Fixas)</option>
                            <option value="SAC">SAC (Decrescente)</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {financingError && (
                      <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span>{financingError}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={isFinancingLoading}
                      className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2 shadow-md shadow-emerald-600/20 active:scale-98 transition-all disabled:opacity-50"
                    >
                      {isFinancingLoading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Processando Política e Score IA...</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-4 h-4" />
                          <span>Verificar Aprovação do Financiamento</span>
                        </>
                      )}
                    </button>
                  </form>
                </div>

                {/* COLUNA DIREITA: RESULTADO DA ANÁLISE E IA (7 COLUNAS) */}
                <div className="lg:col-span-7 space-y-5">
                  {!financingResult ? (
                    <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center space-y-4">
                      <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto shadow-inner">
                        <Calculator className="w-8 h-8" />
                      </div>
                      <div className="max-w-md mx-auto">
                        <h3 className="text-base font-bold text-slate-900">
                          Pronto para Analisar Propostas
                        </h3>
                        <p className="text-xs text-slate-500 mt-1">
                          Preencha as informações do financiamento à esquerda ou clique em um dos
                          cenários rápidos para testar o motor de decisão em tempo real.
                        </p>
                      </div>
                      <div className="pt-2">
                        <button
                          type="button"
                          onClick={() => handleFinancingSubmit()}
                          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
                        >
                          Executar Simulação Padrão
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-5">
                      {/* HERO CARD DE DECISÃO */}
                      <div
                        className={`p-6 rounded-2xl border shadow-sm transition-all ${
                          financingResult.resultado_decisao.status_decisao === "Aprovado"
                            ? "bg-gradient-to-br from-emerald-500/10 via-emerald-500/5 to-white border-emerald-300 text-slate-900"
                            : financingResult.resultado_decisao.status_decisao ===
                                "Aprovado com Condições"
                              ? "bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-white border-amber-300 text-slate-900"
                              : "bg-gradient-to-br from-rose-500/10 via-rose-500/5 to-white border-rose-300 text-slate-900"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-center gap-3.5">
                            <div
                              className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-md ${
                                financingResult.resultado_decisao.status_decisao === "Aprovado"
                                  ? "bg-emerald-600 shadow-emerald-600/30"
                                  : financingResult.resultado_decisao.status_decisao ===
                                      "Aprovado com Condições"
                                    ? "bg-amber-500 shadow-amber-500/30"
                                    : "bg-rose-600 shadow-rose-600/30"
                              }`}
                            >
                              {financingResult.resultado_decisao.status_decisao === "Aprovado" ? (
                                <CheckCircle2 className="w-6 h-6" />
                              ) : financingResult.resultado_decisao.status_decisao ===
                                "Aprovado com Condições" ? (
                                <AlertTriangle className="w-6 h-6" />
                              ) : (
                                <AlertCircle className="w-6 h-6" />
                              )}
                            </div>

                            <div>
                              <div className="flex items-center gap-2">
                                <span
                                  className={`text-[11px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                                    financingResult.resultado_decisao.status_decisao === "Aprovado"
                                      ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                                      : financingResult.resultado_decisao.status_decisao ===
                                          "Aprovado com Condições"
                                        ? "bg-amber-100 text-amber-900 border-amber-300"
                                        : "bg-rose-100 text-rose-900 border-rose-300"
                                  }`}
                                >
                                  {financingResult.resultado_decisao.status_decisao === "Aprovado"
                                    ? "Financiamento Aprovado"
                                    : financingResult.resultado_decisao.status_decisao ===
                                        "Aprovado com Condições"
                                      ? "Aprovado com Condições"
                                      : "Financiamento Reprovado"}
                                </span>
                                <span className="text-xs text-slate-500 font-medium">
                                  {financingResult.cliente.nome}
                                </span>
                              </div>
                              <h3 className="text-lg font-bold text-slate-900 mt-1">
                                {financingResult.resultado_decisao.parecer_resumo}
                              </h3>
                            </div>
                          </div>
                        </div>

                        {/* CARDS DE MÉTRICAS RÁPIDAS DA DECISÃO */}
                        <div className="grid grid-cols-4 gap-3 mt-5 pt-4 border-t border-slate-200/60">
                          <div className="bg-white/80 p-3 rounded-xl border border-slate-200/60 text-center">
                            <span className="text-[10px] uppercase font-bold text-slate-400">
                              Parcela Estimada
                            </span>
                            <p className="text-base font-extrabold text-slate-900 mt-0.5">
                              R${" "}
                              {financingResult.financiamento.valor_parcela.toLocaleString(
                                "pt-BR",
                                { minimumFractionDigits: 2 },
                              )}
                            </p>
                            <span className="text-[10px] text-slate-400">
                              {financingResult.financiamento.prazo_meses}x parcelas
                            </span>
                          </div>

                          <div className="bg-white/80 p-3 rounded-xl border border-slate-200/60 text-center">
                            <span className="text-[10px] uppercase font-bold text-slate-400">
                              Comprometimento (DTI)
                            </span>
                            <p
                              className={`text-base font-extrabold mt-0.5 ${
                                financingResult.capacidade_pagamento.comprometimento_renda_pct <= 30
                                  ? "text-emerald-600"
                                  : financingResult.capacidade_pagamento
                                        .comprometimento_renda_pct <= 35
                                    ? "text-amber-600"
                                    : "text-rose-600"
                              }`}
                            >
                              {financingResult.capacidade_pagamento.comprometimento_renda_pct}%
                            </p>
                            <span className="text-[10px] text-slate-400">teto ideal: 30%</span>
                          </div>

                          <div className="bg-white/80 p-3 rounded-xl border border-slate-200/60 text-center">
                            <span className="text-[10px] uppercase font-bold text-slate-400">
                              Saldo Financiado
                            </span>
                            <p className="text-base font-extrabold text-slate-900 mt-0.5">
                              R${" "}
                              {financingResult.financiamento.saldo_financiado.toLocaleString(
                                "pt-BR",
                              )}
                            </p>
                            <span className="text-[10px] text-slate-400">
                              Entrada: {financingResult.financiamento.percentual_entrada}%
                            </span>
                          </div>

                          <div className="bg-white/80 p-3 rounded-xl border border-slate-200/60 text-center">
                            <span className="text-[10px] uppercase font-bold text-slate-400">
                              Score IA / Risco
                            </span>
                            <p className="text-base font-extrabold text-slate-900 mt-0.5">
                              {financingResult.inteligencia_artificial.probabilidade_inadimplencia}
                            </p>
                            <span
                              className={`text-[10px] font-bold ${
                                financingResult.inteligencia_artificial.faixa_risco === "Baixo Risco"
                                  ? "text-emerald-600"
                                  : financingResult.inteligencia_artificial.faixa_risco ===
                                      "Risco Moderado"
                                    ? "text-amber-600"
                                    : "text-rose-600"
                              }`}
                            >
                              {financingResult.inteligencia_artificial.faixa_risco}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* TERMÔMETRO DE COMPROMETIMENTO DE RENDA (DTI) */}
                      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Gauge className="w-4 h-4 text-emerald-600" />
                            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                              Termômetro de Capacidade de Pagamento (DTI)
                            </h4>
                          </div>
                          <span className="text-xs font-bold text-slate-700">
                            Renda: R${" "}
                            {financingResult.capacidade_pagamento.salario_mensal.toLocaleString(
                              "pt-BR",
                            )}
                          </span>
                        </div>

                        {/* Barra visual de DTI */}
                        <div className="relative pt-2">
                          <div className="h-3.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                            <div
                              style={{
                                width: `${Math.min(
                                  100,
                                  financingResult.capacidade_pagamento.comprometimento_renda_pct,
                                )}%`,
                              }}
                              className={`h-full transition-all duration-500 rounded-full ${
                                financingResult.capacidade_pagamento.comprometimento_renda_pct <= 30
                                  ? "bg-emerald-500"
                                  : financingResult.capacidade_pagamento
                                        .comprometimento_renda_pct <= 35
                                    ? "bg-amber-500"
                                    : "bg-rose-500"
                              }`}
                            />
                          </div>

                          {/* Marcadores de limite 30% e 35% */}
                          <div className="flex justify-between text-[10px] font-semibold text-slate-400 mt-1.5">
                            <span>0%</span>
                            <span className="text-emerald-600 font-bold">30% (Margem Ideal)</span>
                            <span className="text-amber-600 font-bold">35% (Tolerância Máx)</span>
                            <span>50%+</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                          <div className="p-2.5 bg-slate-50 rounded-xl">
                            <span className="text-slate-400 block text-[11px]">
                              Margem Máxima de Parcela (30%)
                            </span>
                            <span className="font-bold text-slate-800">
                              R${" "}
                              {financingResult.capacidade_pagamento.margem_maxima_30pct.toLocaleString(
                                "pt-BR",
                                { minimumFractionDigits: 2 },
                              )}
                            </span>
                          </div>

                          <div className="p-2.5 bg-slate-50 rounded-xl">
                            <span className="text-slate-400 block text-[11px]">
                              {financingResult.capacidade_pagamento.margem_disponivel >= 0
                                ? "Margem Livre Restante"
                                : "Excedente Negativo"}
                            </span>
                            <span
                              className={`font-bold ${
                                financingResult.capacidade_pagamento.margem_disponivel >= 0
                                  ? "text-emerald-700"
                                  : "text-rose-600"
                              }`}
                            >
                              R${" "}
                              {Math.abs(
                                financingResult.capacidade_pagamento.margem_disponivel,
                              ).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* CHECKLIST DE CONFORMIDADE DA POLÍTICA DE CRÉDITO */}
                      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                            <Shield className="w-4 h-4 text-emerald-600" />
                            <span>Checklist de Políticas e Critérios de Concessão</span>
                          </h4>
                          <span className="text-[11px] text-slate-400 font-semibold">
                            6 Pilares Verificados
                          </span>
                        </div>

                        <div className="space-y-2">
                          {Object.entries(financingResult.checklist_politica_credito).map(
                            ([chave, item]) => (
                              <div
                                key={chave}
                                className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50/70 border border-slate-100 text-xs"
                              >
                                <div className="flex items-center gap-2.5">
                                  <span
                                    className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${
                                      item.status === "APROVADO"
                                        ? "bg-emerald-100 text-emerald-700"
                                        : item.status === "ALERTA"
                                          ? "bg-amber-100 text-amber-800"
                                          : "bg-rose-100 text-rose-700"
                                    }`}
                                  >
                                    {item.status === "APROVADO" ? (
                                      <Check className="w-3.5 h-3.5" />
                                    ) : item.status === "ALERTA" ? (
                                      <AlertTriangle className="w-3.5 h-3.5" />
                                    ) : (
                                      <X className="w-3.5 h-3.5" />
                                    )}
                                  </span>
                                  <div>
                                    <p className="font-semibold text-slate-800 capitalize">
                                      {chave.replace(/_/g, " ")}
                                    </p>
                                    <p className="text-[11px] text-slate-500">{item.descricao}</p>
                                  </div>
                                </div>

                                <span
                                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                                    item.status === "APROVADO"
                                      ? "bg-emerald-50 text-emerald-700"
                                      : item.status === "ALERTA"
                                        ? "bg-amber-50 text-amber-700"
                                        : "bg-rose-50 text-rose-700"
                                  }`}
                                >
                                  {item.status}
                                </span>
                              </div>
                            ),
                          )}
                        </div>
                      </div>

                      {/* CENÁRIOS DE VIABILIZAÇÃO (SE REPROVADO OU CONDICIONAL) */}
                      {financingResult.viabilizacao_credito &&
                        Object.keys(financingResult.viabilizacao_credito).length > 0 &&
                        (financingResult.viabilizacao_credito.entrada_minima_para_aprovar ||
                          financingResult.viabilizacao_credito.prazo_sugerido_meses) && (
                          <div className="bg-gradient-to-br from-indigo-50/80 via-white to-slate-50 p-5 rounded-2xl border border-indigo-100 shadow-sm space-y-3">
                            <div className="flex items-center gap-2 text-indigo-900">
                              <Sparkles className="w-4 h-4 text-indigo-600" />
                              <h4 className="text-xs font-bold uppercase tracking-wider">
                                Como Viabilizar a Aprovação da Proposta
                              </h4>
                            </div>
                            <p className="text-xs text-slate-600">
                              O motor de inteligência identificou os parâmetros exatos necessários
                              para que a parcela se enquadre nos 30% da renda:
                            </p>

                            <div className="grid grid-cols-3 gap-3 pt-1">
                              {financingResult.viabilizacao_credito.entrada_minima_para_aprovar && (
                                <div className="p-3 bg-white rounded-xl border border-indigo-100 text-center">
                                  <span className="text-[10px] uppercase font-bold text-indigo-500">
                                    Entrada Necessária
                                  </span>
                                  <p className="text-sm font-extrabold text-indigo-950 mt-0.5">
                                    R${" "}
                                    {financingResult.viabilizacao_credito.entrada_minima_para_aprovar.toLocaleString(
                                      "pt-BR",
                                    )}
                                  </p>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (
                                        financingResult.viabilizacao_credito
                                          .entrada_minima_para_aprovar
                                      ) {
                                        setFinEntrada(
                                          financingResult.viabilizacao_credito
                                            .entrada_minima_para_aprovar,
                                        );
                                        setFinSemEntrada(false);
                                      }
                                    }}
                                    className="text-[10px] text-indigo-600 hover:underline font-semibold mt-1"
                                  >
                                    Aplicar no form
                                  </button>
                                </div>
                              )}

                              {financingResult.viabilizacao_credito.prazo_sugerido_meses && (
                                <div className="p-3 bg-white rounded-xl border border-indigo-100 text-center">
                                  <span className="text-[10px] uppercase font-bold text-indigo-500">
                                    Prazo Recomendado
                                  </span>
                                  <p className="text-sm font-extrabold text-indigo-950 mt-0.5">
                                    {financingResult.viabilizacao_credito.prazo_sugerido_meses} meses
                                  </p>
                                  <span className="text-[10px] text-slate-400 block mt-1">
                                    (dilui a parcela)
                                  </span>
                                </div>
                              )}

                              {financingResult.viabilizacao_credito.salario_minimo_necessario && (
                                <div className="p-3 bg-white rounded-xl border border-indigo-100 text-center">
                                  <span className="text-[10px] uppercase font-bold text-indigo-500">
                                    Renda Mínima
                                  </span>
                                  <p className="text-sm font-extrabold text-indigo-950 mt-0.5">
                                    R${" "}
                                    {financingResult.viabilizacao_credito.salario_minimo_necessario.toLocaleString(
                                      "pt-BR",
                                    )}
                                  </p>
                                  <span className="text-[10px] text-slate-400 block mt-1">
                                    (ou renda conjunta)
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                      {/* PARECER TÉCNICO & OBSERVAÇÕES */}
                      <div className="bg-slate-900 text-white p-5 rounded-2xl shadow-lg space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                            Parecer Executivo para o Analista
                          </span>
                          <span className="text-[11px] text-slate-400">
                            Motor de Inferência:{" "}
                            {financingResult.inteligencia_artificial.modelo}
                          </span>
                        </div>

                        <div className="space-y-2 text-xs">
                          {financingResult.resultado_decisao.pontos_positivos.length > 0 && (
                            <div>
                              <p className="font-semibold text-emerald-300 mb-1">
                                Pontos Fortes Observados:
                              </p>
                              <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                                {financingResult.resultado_decisao.pontos_positivos.map((p, idx) => (
                                  <li key={idx}>{p}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {financingResult.resultado_decisao.condicoes_aprovacao.length > 0 && (
                            <div className="pt-1">
                              <p className="font-semibold text-amber-300 mb-1">
                                Exigências e Mitigadores de Risco:
                              </p>
                              <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                                {financingResult.resultado_decisao.condicoes_aprovacao.map((c, idx) => (
                                  <li key={idx}>{c}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {financingResult.resultado_decisao.motivos_reprovacao.length > 0 && (
                            <div className="pt-1">
                              <p className="font-semibold text-rose-300 mb-1">
                                Motivos de Não Enquadramento:
                              </p>
                              <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                                {financingResult.resultado_decisao.motivos_reprovacao.map((m, idx) => (
                                  <li key={idx}>{m}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* HISTÓRICO DAS ANÁLISES DE FINANCIAMENTO RECENTES */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm mt-8">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">
                      Histórico Recente de Financiamentos
                    </h3>
                    <p className="text-xs text-slate-400">
                      Propostas simuladas e avaliadas pelo comitê de crédito
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 font-medium">
                      Total: {financingHistory.length} propostas
                    </span>
                    {financingHistory.length > 0 && (
                      <button
                        type="button"
                        onClick={handleClearFinancingHistory}
                        className="flex items-center gap-1.5 border border-rose-200 px-3 py-1.5 rounded-lg text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Limpar histórico
                      </button>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-7 text-[11px] font-bold text-slate-400 uppercase tracking-wider py-2.5 border-b border-slate-100">
                  <span>Proposta / Cliente</span>
                  <span>Valor do Bem</span>
                  <span>Entrada</span>
                  <span>Parcela</span>
                  <span>Comprometimento (DTI)</span>
                  <span>Decisão</span>
                  <span>Data / Ações</span>
                </div>

                <div className="divide-y divide-slate-100">
                  {filteredFinancing.length === 0 ? (
                    <div className="py-8 text-center text-slate-400 text-sm">
                      Nenhum financiamento encontrado no histórico.
                    </div>
                  ) : (
                    filteredFinancing.map((item) => (
                      <div
                        key={item.id}
                        className="grid grid-cols-7 items-center py-3.5 text-sm hover:bg-slate-50/60 rounded-xl px-1 transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-slate-900 leading-tight">{item.cliente}</p>
                          <p className="text-[11px] text-slate-400">
                            {item.id} • {item.tipo}
                          </p>
                        </div>
                        <div className="font-medium text-slate-700">
                          R$ {item.valorTotal.toLocaleString("pt-BR")}
                        </div>
                        <div className="text-xs text-slate-600">
                          {item.valorEntrada > 0 ? (
                            <span>R$ {item.valorEntrada.toLocaleString("pt-BR")}</span>
                          ) : (
                            <span className="text-amber-600 font-semibold">Sem Entrada</span>
                          )}
                        </div>
                        <div className="font-semibold text-slate-900">
                          R$ {item.parcela.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </div>
                        <div className="font-semibold text-slate-800">{item.dti.toFixed(1)}%</div>
                        <div>
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                              item.status === "Aprovado"
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : item.status === "Reprovado"
                                  ? "bg-rose-50 text-rose-700 border border-rose-200"
                                  : "bg-amber-50 text-amber-700 border border-amber-200"
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                item.status === "Aprovado"
                                  ? "bg-emerald-500"
                                  : item.status === "Reprovado"
                                    ? "bg-rose-500"
                                    : "bg-amber-500"
                              }`}
                            />
                            {item.status}
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs text-slate-400">{item.data}</span>
                          <button
                            type="button"
                            onClick={() => handleDeleteFinancing(item.id, item.cliente)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                            title={`Excluir proposta ${item.id}`}
                            aria-label={`Excluir proposta ${item.id} de ${item.cliente}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* VIEW 2: VISÃO GERAL (DASHBOARD EXECUTIVO)                */}
          {/* ======================================================== */}
          {activeTab === "overview" && (
            <>
              {/* WELCOME HEADER */}
              <div className="flex items-end justify-between">
                <div>
                  <span className="text-xs font-bold tracking-wider text-emerald-600 uppercase">
                    Risco de Crédito • Visão Consolidada
                  </span>
                  <h2 className="text-2xl font-bold text-slate-900 mt-1">Bom dia, Carolina.</h2>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Acompanhe a saúde da carteira, os modelos de IA e as decisões de crédito.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 bg-white border border-slate-200 px-3 py-1.5 rounded-xl text-sm font-medium text-slate-700 shadow-sm">
                    <span className="text-xs text-slate-400">Período</span>
                    <select
                      value={periodo}
                      onChange={(e) => setPeriodo(e.target.value)}
                      className="bg-transparent border-none text-sm font-semibold text-slate-800 focus:outline-none cursor-pointer"
                    >
                      <option>30 dias</option>
                      <option>60 dias</option>
                      <option>90 dias</option>
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      const csvContent =
                        "data:text/csv;charset=utf-8," +
                        "Cliente,Documento,Valor,Score,PD,Decisao,Data\n" +
                        analyses
                          .map(
                            (a) =>
                              `"${a.cliente}","${a.documento}",${a.valorSolicitado},${a.score},"${a.pdEstimada}","${a.decisao}","${a.data}"`,
                          )
                          .join("\n");
                      const encodedUri = encodeURI(csvContent);
                      const link = document.createElement("a");
                      link.setAttribute("href", encodedUri);
                      link.setAttribute(
                        "download",
                        `relatorio_risco_${periodo.replace(" ", "_")}.csv`,
                      );
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    className="p-2 border border-slate-200 rounded-xl bg-white text-slate-600 hover:bg-slate-50 shadow-sm"
                    title="Exportar dados da carteira"
                    aria-label="Exportar relatório"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* CARD DE DESTAQUE: SIMULADOR DE FINANCIAMENTO */}
              <div className="bg-gradient-to-r from-emerald-600 to-teal-700 text-white p-6 rounded-2xl shadow-lg flex items-center justify-between">
                <div className="space-y-1">
                  <span className="bg-white/20 text-white text-[10px] font-bold tracking-wider px-2.5 py-1 rounded-full uppercase">
                    Novo Recurso Disponível
                  </span>
                  <h3 className="text-xl font-bold mt-2">
                    Simulador & Análise de Financiamentos
                  </h3>
                  <p className="text-xs text-emerald-100 max-w-xl">
                    Avalie solicitações de financiamento calculando DTI, LTV, exigências de entrada
                    (ou nula), estabilidade profissional, idade e score preditivo de inadimplência.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveTab("financing")}
                  className="px-5 py-2.5 bg-white text-emerald-800 hover:bg-emerald-50 rounded-xl font-bold text-xs shadow-md transition-all flex items-center gap-2 flex-shrink-0"
                >
                  <Calculator className="w-4 h-4 text-emerald-600" />
                  <span>Acessar Simulador</span>
                </button>
              </div>

              {/* KPI METRICS GRID */}
              <div className="grid grid-cols-4 gap-4">
                {/* Metric 1 */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:border-slate-300 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
                      <Briefcase className="w-5 h-5" />
                    </div>
                    <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      <ArrowUpRight className="w-3 h-3" /> 8,4%
                    </span>
                  </div>
                  <p className="text-xs font-medium text-slate-400">Carteira analisada</p>
                  <h3 className="text-2xl font-bold text-slate-900 mt-1">R$ 48,2 mi</h3>
                  <p className="text-xs text-slate-400 mt-2">vs. 30 dias anteriores</p>
                </div>

                {/* Metric 2 */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:border-slate-300 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl">
                      <Shield className="w-5 h-5" />
                    </div>
                    <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full">
                      <ArrowDownRight className="w-3 h-3" /> 0,32 p.p.
                    </span>
                  </div>
                  <p className="text-xs font-medium text-slate-400">PD média da carteira</p>
                  <h3 className="text-2xl font-bold text-slate-900 mt-1">4,28%</h3>
                  <p className="text-xs text-emerald-600 font-medium mt-2">abaixo do limite de 5,0%</p>
                </div>

                {/* Metric 3 */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:border-slate-300 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2.5 bg-purple-50 text-purple-600 rounded-xl">
                      <FileCheck2 className="w-5 h-5" />
                    </div>
                    <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      <ArrowUpRight className="w-3 h-3" /> 12,1%
                    </span>
                  </div>
                  <p className="text-xs font-medium text-slate-400">Análises concluídas</p>
                  <h3 className="text-2xl font-bold text-slate-900 mt-1">1.284</h3>
                  <p className="text-xs text-slate-400 mt-2">87 aguardando revisão</p>
                </div>

                {/* Metric 4 */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:border-slate-300 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                    <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      <ArrowUpRight className="w-3 h-3" /> 2,4 p.p.
                    </span>
                  </div>
                  <p className="text-xs font-medium text-slate-400">Taxa de aprovação</p>
                  <h3 className="text-2xl font-bold text-slate-900 mt-1">72,6%</h3>
                  <p className="text-xs text-slate-400 mt-2">18,3% com restrições</p>
                </div>
              </div>

              {/* MIDDLE SECTION: RISK EXPOSURE & AI PERFORMANCE */}
              <div className="grid grid-cols-3 gap-6">
                {/* Exposição por Faixa de Risco (2 Colunas) */}
                <div className="col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-bold text-slate-900 text-base">
                        Exposição por faixa de risco
                      </h3>
                      <button
                        type="button"
                        onClick={() => setActiveTab("financing")}
                        className="text-emerald-600 text-sm font-semibold hover:underline"
                      >
                        Simular proposta
                      </button>
                    </div>
                    <p className="text-xs text-slate-400 mb-6">
                      Saldo da carteira e distribuição de PD
                    </p>

                    {/* Barra Proporcional de Risco */}
                    <div className="h-3.5 w-full bg-slate-100 rounded-full overflow-hidden flex gap-1 mb-6">
                      <div className="bg-emerald-500 h-full w-[46%]" title="Muito baixo: 46%" />
                      <div className="bg-teal-400 h-full w-[31%]" title="Baixo: 31%" />
                      <div className="bg-amber-400 h-full w-[17%]" title="Moderado: 17%" />
                      <div className="bg-rose-500 h-full w-[6%]" title="Elevado: 6%" />
                    </div>

                    {/* Legenda e Valores */}
                    <div className="grid grid-cols-4 gap-4 text-xs">
                      <div>
                        <div className="flex items-center gap-1.5 text-slate-500 font-medium mb-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-500" />
                          <span>A • Muito baixo</span>
                        </div>
                        <p className="font-bold text-slate-900 text-sm">
                          R$ 22,2 mi{" "}
                          <span className="text-xs text-slate-400 font-normal">46%</span>
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center gap-1.5 text-slate-500 font-medium mb-1">
                          <span className="w-2 h-2 rounded-full bg-teal-400" />
                          <span>B • Baixo</span>
                        </div>
                        <p className="font-bold text-slate-900 text-sm">
                          R$ 14,9 mi{" "}
                          <span className="text-xs text-slate-400 font-normal">31%</span>
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center gap-1.5 text-slate-500 font-medium mb-1">
                          <span className="w-2 h-2 rounded-full bg-amber-400" />
                          <span>C • Moderado</span>
                        </div>
                        <p className="font-bold text-slate-900 text-sm">
                          R$ 8,2 mi{" "}
                          <span className="text-xs text-slate-400 font-normal">17%</span>
                        </p>
                      </div>

                      <div>
                        <div className="flex items-center gap-1.5 text-slate-500 font-medium mb-1">
                          <span className="w-2 h-2 rounded-full bg-rose-500" />
                          <span>D/E • Elevado</span>
                        </div>
                        <p className="font-bold text-slate-900 text-sm">
                          R$ 2,9 mi <span className="text-xs text-slate-400 font-normal">6%</span>
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Alert Box */}
                  <div className="mt-6 p-3.5 bg-amber-50/70 border border-amber-200/60 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 bg-amber-100 text-amber-700 rounded-lg">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                      <p className="text-xs text-slate-700">
                        <span className="font-bold text-amber-900">Atenção:</span> propostas sem
                        entrada requerem DTI estrito abaixo de 25% e comprovante de residência regular.
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-amber-600" />
                  </div>
                </div>

                {/* Performance do Modelo (Card Escuro - 1 Coluna) */}
                <div className="bg-[#0b1329] text-white p-6 rounded-2xl flex flex-col justify-between shadow-lg">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                        <Sparkles className="w-5 h-5" />
                      </div>
                      <span className="bg-emerald-500/20 text-emerald-300 text-[10px] font-bold tracking-wider px-2.5 py-1 rounded-full uppercase">
                        Operacional
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 font-medium">Performance do modelo</p>
                    <div className="flex items-baseline gap-2 mt-1 mb-6">
                      <h3 className="text-3xl font-extrabold tracking-tight text-white">0,775</h3>
                      <span className="text-xs text-slate-400 font-medium">ROC-AUC</span>
                    </div>

                    {/* Metric Progress Bars */}
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-slate-400">Recall de Inadimplência</span>
                          <span className="font-semibold text-white">59,7%</span>
                        </div>
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-emerald-400 h-full w-[59.7%]" />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-slate-400">Gini</span>
                          <span className="font-semibold text-white">0,551</span>
                        </div>
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-blue-400 h-full w-[75%]" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-[11px] text-slate-500 mt-6">
                    <span>CreditRisk v1.0.0</span>
                    <span>Random Forest</span>
                  </div>
                </div>
              </div>

              {/* BOTTOM SECTION: RECENT ANALYSES */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Análises recentes</h3>
                    <p className="text-xs text-slate-400">
                      Decisões e recomendações geradas pelo motor de risco
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setSearchTerm("")}
                      className="flex items-center gap-2 border border-slate-200 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                      <Filter className="w-3.5 h-3.5" /> Limpar filtros
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab("analyses")}
                      className="text-emerald-600 text-xs font-semibold hover:underline"
                    >
                      Ver todas ({analyses.length})
                    </button>
                  </div>
                </div>

                {/* Cabeçalho da Tabela */}
                <div className="grid grid-cols-6 text-[11px] font-bold text-slate-400 uppercase tracking-wider py-2.5 border-b border-slate-100">
                  <span>Cliente</span>
                  <span>Valor Solicitado</span>
                  <span>Score</span>
                  <span>PD Estimada</span>
                  <span>Decisão</span>
                  <span>Data</span>
                </div>

                {/* Linhas da Tabela */}
                <div className="divide-y divide-slate-100">
                  {filteredAnalyses.length === 0 ? (
                    <div className="py-8 text-center text-slate-400 text-sm">
                      Nenhuma análise encontrada para o filtro atual.
                    </div>
                  ) : (
                    filteredAnalyses.map((item) => (
                      <div
                        key={item.id}
                        className="grid grid-cols-6 items-center py-3.5 text-sm hover:bg-slate-50/60 rounded-xl px-1 transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-slate-900 leading-tight">{item.cliente}</p>
                          <p className="text-[11px] text-slate-400">{item.documento}</p>
                        </div>
                        <div className="font-medium text-slate-700">
                          R$ {item.valorSolicitado.toLocaleString("pt-BR")}
                        </div>
                        <div className="font-mono text-xs text-slate-600">
                          {item.score.toFixed(3)}
                        </div>
                        <div className="font-semibold text-slate-800">{item.pdEstimada}</div>
                        <div>
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                              item.decisao === "Baixo Risco"
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                                : item.decisao === "Alto Risco"
                                  ? "bg-rose-50 text-rose-700 border border-rose-200/60"
                                  : "bg-amber-50 text-amber-700 border border-amber-200/60"
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                item.decisao === "Baixo Risco"
                                  ? "bg-emerald-500"
                                  : item.decisao === "Alto Risco"
                                    ? "bg-rose-500"
                                    : "bg-amber-500"
                              }`}
                            />
                            {item.decisao}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400">{item.data}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          )}

          {/* ======================================================== */}
          {/* VIEW 3: CARTÕES / INADIMPLÊNCIA                          */}
          {/* ======================================================== */}
          {activeTab === "analyses" && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">
                    Histórico de Análises de Cartões e Risco
                  </h2>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Consultas individuais processadas pelo modelo preditivo com atributos derivados.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(true)}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs px-4 py-2 rounded-xl transition-all shadow-sm"
                >
                  <Plus className="w-4 h-4" />
                  <span>Nova Análise</span>
                </button>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <div className="grid grid-cols-6 text-[11px] font-bold text-slate-400 uppercase tracking-wider py-2.5 border-b border-slate-100">
                  <span>Cliente</span>
                  <span>Limite Concedido</span>
                  <span>Score Modelo</span>
                  <span>PD Estimada</span>
                  <span>Decisão</span>
                  <span>Data</span>
                </div>
                <div className="divide-y divide-slate-100">
                  {filteredAnalyses.map((item) => (
                    <div
                      key={item.id}
                      className="grid grid-cols-6 items-center py-3.5 text-sm hover:bg-slate-50/60 rounded-xl px-1 transition-colors"
                    >
                      <div>
                        <p className="font-semibold text-slate-900 leading-tight">{item.cliente}</p>
                        <p className="text-[11px] text-slate-400">{item.documento}</p>
                      </div>
                      <div className="font-medium text-slate-700">
                        R$ {item.valorSolicitado.toLocaleString("pt-BR")}
                      </div>
                      <div className="font-mono text-xs text-slate-600">
                        {item.score.toFixed(3)}
                      </div>
                      <div className="font-semibold text-slate-800">{item.pdEstimada}</div>
                      <div>
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                            item.decisao === "Baixo Risco"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                              : "bg-rose-50 text-rose-700 border border-rose-200/60"
                          }`}
                        >
                          {item.decisao}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">{item.data}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* MODAL NOVA ANÁLISE DE CARTÃO (26 FEATURES) */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">
                    Nova Análise de Risco de Crédito (Cartão)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Insira os parâmetros para obter o score de inadimplência em tempo real
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-xl hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Presets Bar */}
            <div className="px-6 py-2.5 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500 font-medium">Preenchimento rápido de teste:</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleApplyPreset("saudavel")}
                  className="px-2.5 py-1 bg-white border border-emerald-200 text-emerald-700 hover:bg-emerald-50 rounded-lg font-medium transition-colors"
                >
                  Perfil Conservador (Baixo Risco)
                </button>
                <button
                  type="button"
                  onClick={() => handleApplyPreset("risco")}
                  className="px-2.5 py-1 bg-white border border-rose-200 text-rose-700 hover:bg-rose-50 rounded-lg font-medium transition-colors"
                >
                  Perfil Crítico (Alto Risco)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setFormData(getInitialFormData());
                    setClientName("Novo Cliente");
                    setPredictionResult(null);
                  }}
                  className="px-2.5 py-1 bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-lg font-medium flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" /> Limpar
                </button>
              </div>
            </div>

            {/* Modal Body Form */}
            <form onSubmit={handleFormSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Identificação Básica */}
              <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-100">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                  1. Identificação do Cliente
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Nome Completo
                    </label>
                    <input
                      type="text"
                      required
                      value={clientName}
                      onChange={(e) => setClientName(e.target.value)}
                      className="w-full text-sm px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      CPF / Documento
                    </label>
                    <input
                      type="text"
                      required
                      value={clientDoc}
                      onChange={(e) => setClientDoc(e.target.value)}
                      className="w-full text-sm px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                  </div>
                </div>
              </div>

              {/* Perfil Cadastral e Limite */}
              <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-100">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                  2. Limite e Perfil Sociodemográfico
                </h4>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Limite de Crédito (R$)
                    </label>
                    <input
                      type="number"
                      min={1000}
                      step={500}
                      required
                      value={formData.LIMIT_BAL}
                      onChange={(e) => handleUpdateField("LIMIT_BAL", Number(e.target.value))}
                      className="w-full text-sm px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-semibold text-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Idade (anos)
                    </label>
                    <input
                      type="number"
                      min={18}
                      max={100}
                      required
                      value={formData.AGE}
                      onChange={(e) => handleUpdateField("AGE", Number(e.target.value))}
                      className="w-full text-sm px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Sexo
                    </label>
                    <select
                      value={formData.SEX}
                      onChange={(e) => handleUpdateField("SEX", Number(e.target.value))}
                      className="w-full text-sm px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    >
                      <option value={1}>Masculino</option>
                      <option value={2}>Feminino</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Escolaridade
                    </label>
                    <select
                      value={formData.EDUCATION}
                      onChange={(e) => handleUpdateField("EDUCATION", Number(e.target.value))}
                      className="w-full text-sm px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    >
                      <option value={1}>Pós-Graduação</option>
                      <option value={2}>Universidade</option>
                      <option value={3}>Ensino Médio</option>
                      <option value={4}>Outros</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Histórico de Atrasos Recentes (6 meses) */}
              <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-100">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                  3. Histórico de Pagamentos (PAY_0 a PAY_6)
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  {PAYMENT_FEATURES.map((feature) => (
                    <div key={feature}>
                      <label className="block text-xs text-slate-600 font-medium mb-1">
                        {MONTHS[feature]} ({feature})
                      </label>
                      <select
                        value={formData[feature]}
                        onChange={(e) => handleUpdateField(feature, Number(e.target.value))}
                        className="w-full text-xs px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg focus:ring-1 focus:ring-emerald-500"
                      >
                        {PAYMENT_STATUSES.map((val) => (
                          <option key={val} value={val}>
                            {PAYMENT_LABELS[val] ?? `${val} meses de atraso`}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>

              {/* Faturas e Pagamentos */}
              <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-100">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                  4. Valores de Fatura e Pagamentos Efetuados
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-slate-600 mb-1">Valores das Faturas</p>
                    {BILL_FEATURES.map((feat, idx) => (
                      <div key={feat} className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-400 w-16">Mês {idx + 1}</span>
                        <input
                          type="number"
                          step={100}
                          value={formData[feat]}
                          onChange={(e) => handleUpdateField(feat, Number(e.target.value))}
                          className="w-full text-xs px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg"
                        />
                      </div>
                    ))}
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-slate-600 mb-1">Pagamentos Realizados</p>
                    {PAID_FEATURES.map((feat, idx) => (
                      <div key={feat} className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-400 w-16">Pago {idx + 1}</span>
                        <input
                          type="number"
                          min={0}
                          step={100}
                          value={formData[feat]}
                          onChange={(e) => handleUpdateField(feat, Number(e.target.value))}
                          className="w-full text-xs px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {formError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              {/* Resultado da Predição */}
              {predictionResult && (
                <div className="p-5 bg-slate-900 text-white rounded-2xl space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      <span className="font-bold text-sm">Resultado da Análise Preditiva</span>
                    </div>
                    <span
                      className={`text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider ${
                        predictionResult.decisao === "Baixo Risco"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                      }`}
                    >
                      {predictionResult.decisao}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-3 pt-2 text-center">
                    <div className="p-3 bg-slate-800/80 rounded-xl">
                      <p className="text-[11px] text-slate-400">Score de Risco</p>
                      <p className="text-xl font-extrabold text-white">
                        {predictionResult.score_modelo.toFixed(3)}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-800/80 rounded-xl">
                      <p className="text-[11px] text-slate-400">PD Estimada</p>
                      <p className="text-xl font-extrabold text-emerald-400">
                        {predictionResult.probabilidade_inadimplencia}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-800/80 rounded-xl">
                      <p className="text-[11px] text-slate-400">Motor de Inferência</p>
                      <p className="text-xs font-semibold text-slate-200 mt-1 truncate">
                        {predictionResult.modelo}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Fechar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold flex items-center gap-2 transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <span>Processando via IA...</span>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4" />
                      <span>Executar Análise de Risco</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}