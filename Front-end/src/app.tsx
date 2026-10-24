import { useMemo, useState } from "react";

const formatBRL = (value: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

const formatPercent = (value: number) =>
  `${new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)}%`;

function calculateInstallment(principal: number, months: number, ratePerMonth: number) {
  if (principal <= 0 || months <= 0) return 0;
  if (ratePerMonth <= 0) return principal / months;

  const growth = Math.expm1(months * Math.log1p(ratePerMonth));
  return Math.round(((principal * ratePerMonth * (growth + 1)) / growth) * 100) / 100;
}

function calculateRateFromPayment(principal: number, months: number, payment: number) {
  if (!principal || !months || !payment) return 0;
  let minRate = 0.000001;
  let maxRate = 1;

  for (let i = 0; i < 250; i += 1) {
    const midRate = (minRate + maxRate) / 2;
    const expectedPayment = calculateInstallment(principal, months, midRate);
    if (expectedPayment > payment) {
      maxRate = midRate;
    } else {
      minRate = midRate;
    }
  }

  return ((minRate + maxRate) / 2) * 100;
}

function calculateAmountFromRateAndPayment(months: number, ratePerMonth: number, payment: number) {
  if (!months || !payment) return 0;
  if (ratePerMonth <= 0) return payment * months;

  const divisor = (ratePerMonth * Math.pow(1 + ratePerMonth, months)) / (Math.pow(1 + ratePerMonth, months) - 1);
  return payment / divisor;
}

export default function CreditRiskApp() {
  const [amount, setAmount] = useState(15000);
  const [months, setMonths] = useState(24);
  const [income, setIncome] = useState(4500);
  const [monthlyRate, setMonthlyRate] = useState(2.35);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [calcType, setCalcType] = useState<"rate" | "installment" | "amount">("rate");
  const [calcAmount, setCalcAmount] = useState(25000);
  const [calcDownPayment, setCalcDownPayment] = useState(5000);
  const [calcMonths, setCalcMonths] = useState(24);
  const [calcRate, setCalcRate] = useState(2.35);
  const [calcInstallment, setCalcInstallment] = useState(1100);

  const principalAmount = Math.max(calcAmount - calcDownPayment, 0);
  const calculatedRate = calculateRateFromPayment(principalAmount, calcMonths, calcInstallment);
  const calculatedInstallment = calculateInstallment(principalAmount, calcMonths, calcRate / 100);
  const calculatedAmount = calculateAmountFromRateAndPayment(calcMonths, calcRate / 100, calcInstallment);
  const displayRate = calcType === "rate" ? calculatedRate : calcRate;
  const displayInstallment = calcType === "installment" ? calculatedInstallment : calcInstallment;
  const displayAmount = calcType === "amount" ? calculatedAmount : calcAmount;

  const installmentValue = useMemo(() => {
    return calculateInstallment(amount, months, monthlyRate / 100);
  }, [amount, months, monthlyRate]);

  const ratio = (installmentValue / income) * 100;
  const totalInstallments = installmentValue * months;
  const interestCost = totalInstallments - amount;
  const rate = displayRate;
  const annualRate = rate * 12;
  const totalPaid = displayInstallment * calcMonths;

  return (
    <div className="bg-brand-bg text-brand-textDark font-sans antialiased selection:bg-brand-accent selection:text-brand-dark min-h-screen flex flex-col justify-between">
      <style>{`
        input[type=range] {
          -webkit-appearance: none;
          width: 100%;
          background: transparent;
        }
        input[type=range]:focus { outline: none; }
        input[type=range]::-webkit-slider-runnable-track {
          width: 100%;
          height: 8px;
          cursor: pointer;
          background: #E8E3D5;
          border-radius: 4px;
        }
        input[type=range]::-webkit-slider-thumb {
          height: 24px;
          width: 24px;
          border-radius: 50%;
          background: #023824;
          cursor: pointer;
          -webkit-appearance: none;
          margin-top: -8px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.15);
          transition: transform 0.1s ease;
        }
        input[type=range]::-webkit-slider-thumb:hover { transform: scale(1.15); }
        input[type=range]::-moz-range-track {
          width: 100%;
          height: 8px;
          cursor: pointer;
          background: #E8E3D5;
          border-radius: 4px;
        }
        input[type=range]::-moz-range-thumb {
          height: 24px;
          width: 24px;
          border-radius: 50%;
          background: #023824;
          cursor: pointer;
          box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        .toggle-checkbox:checked { right: 0; background-color: #023824; }
        .toggle-checkbox:checked + .toggle-label { background-color: #C5E898; }
        .faq-btn[aria-expanded="true"] .faq-icon { transform: rotate(45deg); }
      `}</style>

      <header className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between">
        <a href="#" className="flex items-center gap-1 text-2xl font-bold tracking-tight text-brand-dark">
          <span className="font-bold text-3xl font-serif">Simula</span>
          <span className="font-bold text-3xl font-serif text-emerald-600">Livre</span>
        </a>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-700">
          <a href="#calculadora-juros" className="hover:text-brand-dark transition-colors">Calculadora de juros</a>
          <a href="#sobre-estimativa" className="hover:text-brand-dark transition-colors">Sobre a estimativa</a>
          <a href="#simulador-principal" className="bg-brand-dark hover:bg-brand-darkHover text-white px-6 py-2.5 rounded-full font-medium transition-all shadow-sm">
            Simular
          </a>
        </nav>

        <div className="md:hidden">
          <a href="#simulador-principal" className="bg-brand-dark text-white px-4 py-2 rounded-full text-xs font-semibold">Simular</a>
        </div>
      </header>

      <main className="space-y-16 lg:space-y-24">
        <section id="simulador-principal" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4 pb-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            <div className="lg:col-span-5 space-y-6 pt-4">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 border border-gray-200 text-xs font-medium text-gray-700 shadow-sm">
                <span>🔒</span> Sem cadastro · sem login · sem rastro
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-serif font-bold text-brand-dark leading-[1.1] tracking-tight">
                Simule o custo do crédito <span className="italic text-emerald-800 font-serif">sem entregar seus dados.</span>
              </h1>

              <p className="text-gray-600 text-base sm:text-lg leading-relaxed">
                Informe valor, prazo, juros e renda para estimar a parcela e o comprometimento mensal. O cálculo acontece no seu navegador.
              </p>

              <ul className="space-y-3 pt-2 text-sm sm:text-base text-gray-700 font-medium">
                <li className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 shrink-0" />
                  Zero campos pessoais: nada de nome, CPF ou e-mail
                </li>
                <li className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 shrink-0" />
                  Não consulta nem afeta seu score
                </li>
                <li className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 shrink-0" />
                  Resultado em tempo real, sem esperar
                </li>
              </ul>
            </div>

            <div className="lg:col-span-7 bg-white rounded-3xl p-6 sm:p-8 shadow-xl border border-gray-100/80 space-y-8">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl sm:text-3xl font-serif font-bold text-brand-dark">Simule agora</h2>
                <span className="bg-brand-accentLight text-emerald-900 text-xs font-semibold px-3 py-1 rounded-full">Nada é salvo</span>
              </div>

              <div className="space-y-6">
                <div className="space-y-2">
                  <div className="flex justify-between items-baseline gap-4">
                    <label className="text-sm font-semibold text-gray-800">Valor a financiar</label>
                    <span className="text-2xl font-serif font-bold text-brand-dark">{formatBRL(amount)}</span>
                  </div>
                  <input
                    type="range"
                    min={1000}
                    max={50000}
                    step={100}
                    value={amount}
                    onChange={(event) => setAmount(Number(event.target.value))}
                  />
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <span>🔒</span> Só existe nesta tela. Não sai do seu aparelho.
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-baseline gap-4">
                    <label className="text-sm font-semibold text-gray-800">Em quantos meses?</label>
                    <span className="text-2xl font-serif font-bold text-brand-dark">{months} meses</span>
                  </div>
                  <input
                    type="range"
                    min={6}
                    max={72}
                    step={1}
                    value={months}
                    onChange={(event) => setMonths(Number(event.target.value))}
                  />
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <span>🔒</span> Mude à vontade: o resultado se ajusta na hora.
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-baseline gap-4">
                    <label className="text-sm font-semibold text-gray-800">Juros mensais</label>
                    <span className="text-2xl font-serif font-bold text-brand-dark">{formatPercent(monthlyRate)}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={5}
                    step={0.01}
                    value={monthlyRate}
                    onChange={(event) => setMonthlyRate(Number(event.target.value))}
                  />
                  <p className="text-xs text-gray-500">
                    Informe a taxa da proposta. O CET, tarifas, seguros e impostos não estão incluídos.
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-baseline gap-4">
                    <label className="text-sm font-semibold text-gray-800">Sua renda mensal</label>
                    <span className="text-2xl font-serif font-bold text-brand-dark">{formatBRL(income)}</span>
                  </div>
                  <input
                    type="range"
                    min={1000}
                    max={25000}
                    step={100}
                    value={income}
                    onChange={(event) => setIncome(Number(event.target.value))}
                  />
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <span>🔒</span> Um valor aproximado basta. Não pedimos comprovante.
                  </p>
                </div>
              </div>

              <hr className="border-gray-100" />

              <div className="bg-brand-dark rounded-2xl p-5 text-white space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium text-emerald-200/80">Parcela Price estimada</div>
                    <div className="text-2xl sm:text-3xl font-serif font-bold">{formatBRL(installmentValue)}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-emerald-200/80">Comprometimento da renda</div>
                    <div className="text-2xl sm:text-3xl font-serif font-bold">{formatPercent(ratio)}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 border-t border-emerald-800/80 pt-4 text-sm">
                  <div>
                    <div className="text-emerald-200">Total estimado das parcelas</div>
                    <div className="font-semibold">{formatBRL(totalInstallments)}</div>
                  </div>
                  <div>
                    <div className="text-emerald-200">Juros estimados</div>
                    <div className="font-semibold">{formatBRL(interestCost)}</div>
                  </div>
                </div>
                <p className="text-xs text-emerald-100/80">
                  Estimativa pela Tabela Price, sem tarifas, seguros ou impostos. Não representa chance de aprovação nem avaliação de inadimplência.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="sobre-estimativa" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-lg border border-gray-100">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              <div className="space-y-6">
                <div className="space-y-3">
                  <p className="text-xs font-bold tracking-wider uppercase text-emerald-600">Como funciona</p>
                  <h2 className="text-3xl sm:text-4xl font-serif font-bold text-brand-dark">Veja o que influencia o valor estimado.</h2>
                </div>

                <p className="text-sm leading-relaxed text-gray-700">
                  A parcela é calculada pela Tabela Price a partir do valor, prazo e taxa mensal informados. Confira esses dados na proposta; o custo efetivo total pode incluir tarifas, seguros e impostos que não entram aqui.
                </p>
              </div>

              <div className="bg-brand-dark text-white rounded-3xl p-6 shadow-lg">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-emerald-200">Valores desta simulação</span>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-emerald-200">Valor financiado</span>
                    <span className="font-semibold">{formatBRL(amount)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-emerald-200">Parcela estimada</span>
                    <span className="font-semibold">{formatBRL(installmentValue)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-emerald-200">Renda após esta parcela</span>
                    <span className="font-semibold">{formatBRL(income - installmentValue)}</span>
                  </div>
                </div>
                <p className="mt-5 border-t border-emerald-800/80 pt-4 text-xs text-emerald-100/80">
                  O comprometimento considera somente esta parcela; outras dívidas e despesas não foram informadas. O resultado não estima aprovação nem inadimplência.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="calculadora-juros" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="space-y-3 mb-8">
            <h2 className="text-3xl sm:text-4xl font-serif font-bold text-brand-dark">Calculadora de juros</h2>
            <p className="text-gray-600 text-sm sm:text-base max-w-2xl">
              Descubra a taxa real escondida numa proposta. Escolha o que quer descobrir e preencha o resto.
            </p>
          </div>

          <div className="bg-white rounded-3xl p-6 sm:p-10 shadow-lg border border-gray-100">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
              <div className="lg:col-span-7 space-y-6">
                <div className="space-y-2">
                  <label className="text-xs sm:text-sm font-semibold text-gray-800">O que você quer descobrir?</label>
                  <div className="flex flex-wrap gap-2">
                    {[
                      { value: "rate", label: "Taxa de juros" },
                      { value: "installment", label: "Prestação" },
                      { value: "amount", label: "Valor financiado" },
                    ].map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`calc-tab px-4 py-2 rounded-full text-xs sm:text-sm font-semibold ${calcType === option.value ? "bg-brand-dark text-white shadow-sm" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
                        onClick={() => setCalcType(option.value as "rate" | "installment" | "amount")}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Valor financiado</label>
                    <div className="relative">
                      <input
                        type="number"
                        value={Number(displayAmount.toFixed(2))}
                        onChange={(event) => setCalcAmount(Number(event.target.value) || 0)}
                        readOnly={calcType === "amount"}
                        className={`w-full bg-[#F9F8F3] border border-gray-200 rounded-xl py-3 px-4 text-gray-900 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-dark ${calcType === "amount" ? "bg-gray-100 text-gray-500" : ""}`}
                      />
                      <span className="absolute right-3 top-3 text-sm text-gray-400 font-medium">R$</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Valor de entrada</label>
                    <div className="relative">
                      <input
                        type="number"
                        value={calcDownPayment}
                        onChange={(event) => setCalcDownPayment(Number(event.target.value) || 0)}
                        className="w-full bg-[#F9F8F3] border border-gray-200 rounded-xl py-3 px-4 text-gray-900 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-dark"
                      />
                      <span className="absolute right-3 top-3 text-sm text-gray-400 font-medium">R$</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Número de meses</label>
                    <div className="relative">
                      <input
                        type="number"
                        value={calcMonths}
                        onChange={(event) => setCalcMonths(Math.max(1, Number(event.target.value) || 1))}
                        className="w-full bg-[#F9F8F3] border border-gray-200 rounded-xl py-3 px-4 text-gray-900 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-dark"
                      />
                      <span className="absolute right-3 top-3 text-sm text-gray-400 font-medium">meses</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Taxa de juros mensal</label>
                    <div className="relative">
                      <input
                        type="number"
                        step="0.01"
                        value={Number(displayRate.toFixed(2))}
                        onChange={(event) => setCalcRate(Number(event.target.value) || 0)}
                        readOnly={calcType === "rate"}
                        className={`w-full bg-[#F9F8F3] border border-gray-200 rounded-xl py-3 px-4 text-gray-900 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-dark ${calcType === "rate" ? "bg-gray-100 text-gray-500" : ""}`}
                      />
                      <span className="absolute right-3 top-2 text-xs text-gray-400 text-right leading-none">%<br /><span className="text-[9px]">a.m.</span></span>
                    </div>
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Valor da prestação</label>
                    <div className="relative">
                      <input
                        type="number"
                        value={Number(displayInstallment.toFixed(2))}
                        onChange={(event) => setCalcInstallment(Number(event.target.value) || 0)}
                        readOnly={calcType === "installment"}
                        className={`w-full bg-[#F9F8F3] border border-gray-200 rounded-xl py-3 px-4 text-gray-900 font-semibold focus:outline-none focus:ring-2 focus:ring-brand-dark ${calcType === "installment" ? "bg-gray-100 text-gray-500" : ""}`}
                      />
                      <span className="absolute right-3 top-3 text-sm text-gray-400 font-medium">R$</span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-gray-500 leading-relaxed">
                  O valor de entrada é descontado do valor financiado. Cálculo pela Tabela Price, feito no seu aparelho.
                </p>
              </div>

              <div className="lg:col-span-5 bg-brand-dark text-white rounded-2xl p-6 sm:p-8 flex flex-col justify-between space-y-6">
                <div>
                  <span className="text-xs font-medium text-emerald-200">Taxa de juros</span>
                  <div className="text-4xl sm:text-5xl font-serif font-bold text-white mt-1">{rate.toFixed(2)}% a.m.</div>
                </div>

                <div className="space-y-3 pt-4 border-t border-emerald-800/80 text-xs sm:text-sm">
                  <div className="flex justify-between">
                    <span className="text-emerald-200">Juros mensais</span>
                    <span className="font-semibold text-white">{rate.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-emerald-200">Juros anuais</span>
                    <span className="font-semibold text-white">{annualRate.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-emerald-200">Valor parcelado</span>
                    <span className="font-semibold text-white">{formatBRL(principalAmount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-emerald-200">Total pago nas parcelas</span>
                    <span className="font-semibold text-white">{formatBRL(totalPaid)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-emerald-200">Custo total de juros</span>
                    <span className="font-semibold text-white">{formatBRL(totalPaid - principalAmount)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          <h2 className="text-3xl sm:text-4xl font-serif font-bold text-brand-dark text-center sm:text-left">Perguntas frequentes</h2>

          <div className="space-y-4 border-t border-gray-200/80 pt-4">
            {[
              { question: "Vocês guardam alguma informação?", answer: "Nenhuma. Todos os cálculos ocorrem localmente no código JavaScript executado direto no seu próprio navegador. Não enviamos dados para servidores externos." },
              { question: "Isso afeta meu score?", answer: "Não afeta de forma alguma. Como não pedimos CPF nem fazemos consultas aos birôs de crédito, nenhuma busca é registrada." },
              { question: "O resultado é uma aprovação?", answer: "Não. Este é um simulador com fins educativos e estimativos. A aprovação real depende das políticas internas e análises específicas de cada instituição financeira." },
              { question: "Como interpretar o comprometimento da renda?", answer: "Compare a parcela estimada com sua renda e considere também outras dívidas e despesas. Cada instituição adota critérios próprios; este simulador não calcula chance de aprovação." },
            ].map((item, index) => (
              <div key={item.question} className="border-b border-gray-200/80 pb-4">
                <button
                  type="button"
                  className="faq-btn w-full flex justify-between items-center text-left text-sm sm:text-base font-semibold text-brand-dark focus:outline-none py-2"
                  aria-expanded={openFaq === index}
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                >
                  <span>{item.question}</span>
                  <span className="faq-icon text-xl text-emerald-800 transition-transform font-bold">+</span>
                </button>
                {openFaq === index && (
                  <div className="text-xs sm:text-sm text-gray-600 pt-2 leading-relaxed">{item.answer}</div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="bg-brand-dark rounded-3xl p-8 sm:p-14 text-center text-white space-y-6">
            <h2 className="text-3xl sm:text-5xl font-serif font-bold">Teste quantas vezes quiser.</h2>
            <p className="text-emerald-100/80 text-sm sm:text-base max-w-xl mx-auto">
              Ninguém está olhando. Nada fica gravado.
            </p>
            <div>
              <a href="#simulador-principal" className="inline-block bg-brand-accent hover:bg-emerald-300 text-brand-dark font-semibold px-8 py-3.5 rounded-full text-sm sm:text-base transition-all shadow-md">
                Fazer minha simulação
              </a>
            </div>
          </div>

          <p className="text-center text-[11px] sm:text-xs text-gray-500 mt-6 max-w-2xl mx-auto">
            Estimativa educativa. Não é oferta nem garantia de crédito. Taxas de referência entre 1,9% e 2,8% a.m.
          </p>
        </section>
      </main>

      <footer className="border-t border-gray-200 mt-12 py-6 text-center text-xs text-gray-500">
        <p>© 2026 SimulaLivre. Simulador financeiro estático e privativo.</p>
      </footer>
    </div>
  );
}
