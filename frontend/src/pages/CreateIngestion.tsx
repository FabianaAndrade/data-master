import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import StepIndicator from "@/components/StepIndicator";
import StepSigla from "@/components/ingestion/StepSigla";
import StepFonte from "@/components/ingestion/StepFonte";
import StepMetadados from "@/components/ingestion/StepMetadados";
import StepColunas from "@/components/ingestion/StepColunas";
import StepDicionarizacao from "@/components/ingestion/StepDicionarizacao";
import StepQualidade from "@/components/ingestion/StepQualidade";
import StepRevisao from "@/components/ingestion/StepRevisao";

import { useAuth } from "../hooks/use-auth";
import { toast } from "sonner";

const TOTAL_STEPS = 7;
const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const CreateIngestion = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [sigla, setSigla] = useState({ sigla: "", gestorAprovador: "" });
  const [fonte, setFonte] = useState({ sistemaOrigem: "", formatoArquivo: "" });
  const [metadados, setMetadados] = useState({
    nomeTabela: "", periodicidade: "", tipoIngestao: "",
    horario: "", dataCriacao: "", dataAtualizacao: "", atualizacao: "", incluirColunaDataRef: "", camada: "",
    usage: "", limitacoes: "", classificacaoSeguranca: "Internal",
    retencao: "Não se aplica",
  });
  const [colunas, setColunas] = useState({
    numColunas: "3",
    colunas: [
      { nome: "", dataType: "", chavePrimaria: "", pii: "", piiType: "" },
      { nome: "", dataType: "", chavePrimaria: "", pii: "", piiType: "" },
      { nome: "", dataType: "", chavePrimaria: "", pii: "", piiType: "" },
    ],
    colunaParticao: "",
  });
  const [dicionarizacao, setDicionarizacao] = useState({
    descricaoTabela: "",
    colunas: [] as { coluna: string, descricao: string }[],
  });
  const [qualidade, setQualidade] = useState({
    configurar: "Sim",
    colunas: [] as { coluna: string, regras: string[] }[],
  });

  const next = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));

  const handleSubmit = async () => {
    if (!user?.token) {
      toast.error("Usuário não autenticado.");
      return;
    }
    setIsSubmitting(true);
    try {
      const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${user.token}`,
        },
        body: JSON.stringify({
          sigla: {
            sigla: sigla.sigla,
            gestorAprovador: sigla.gestorAprovador,
          },
          fonte: {
            sistemaOrigem: fonte.sistemaOrigem,
            formatoArquivo: fonte.formatoArquivo,
          },
          metadados: {
            nomeTabela: metadados.nomeTabela,
            periodicidade: metadados.periodicidade,
            tipoIngestao: metadados.tipoIngestao,
            horario: metadados.horario,
            dataCriacao: metadados.dataCriacao,
            dataAtualizacao: metadados.dataAtualizacao,
            atualizacao: metadados.atualizacao,
            incluirColunaDataRef: metadados.incluirColunaDataRef,
            camada: metadados.camada,
            usage: metadados.usage,
            limitacoes: metadados.limitacoes,
            classificacaoSeguranca: metadados.classificacaoSeguranca,
            retencao: metadados.retencao,
          },
          colunas: {
            numColunas: colunas.numColunas,
            colunas: getEffectiveColunas(),
            colunaParticao: colunas.colunaParticao,
          },
          dicionarizacao: {
            descricaoTabela: dicionarizacao.descricaoTabela,
            colunas: dicionarizacao.colunas.map((c) => ({
              coluna: c.coluna,
              descricao: c.descricao,
            })),
          },
          qualidade: {
            configurar: qualidade.configurar,
            colunas: qualidade.colunas,
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Falha ao submeter ingestão");
      }

      const resData = await response.json();
      toast.success("Ingestão submetida com sucesso!");
      navigate(`/ingestion-success/${resData.ingestion_id}`);
    } catch (err: any) {
      toast.error(`Erro ao submeter: ${err.message}`);
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const prev = () => setStep((s) => Math.max(s - 1, 0));

  const getEffectiveColunas = () => {
    let base = colunas.colunas.filter((c) => c.nome);
    if (metadados.incluirColunaDataRef === "Sim") {
      base.push({ nome: "dat_ref_carga", dataType: "DATE", chavePrimaria: "Não", pii: "Não", piiType: "N/A" });
    }
    return base;
  };

  const syncDicionarizacao = () => {
    const cols = getEffectiveColunas().map((c) => {
      const existing = dicionarizacao.colunas.find((d) => d.coluna === c.nome);
      return existing || { coluna: c.nome, descricao: "" };
    });
    setDicionarizacao((d) => ({ ...d, colunas: cols }));
  };

  const syncQualidade = () => {
    const cols = getEffectiveColunas().map((c) => {
      const existing = qualidade.colunas.find((q) => q.coluna === c.nome);
      return existing || { coluna: c.nome, regras: [] };
    });
    setQualidade((q) => ({ ...q, colunas: cols }));
  };

  const renderStep = () => {
    switch (step) {
      case 0: return <StepSigla data={sigla} onChange={setSigla} onNext={next} />;
      case 1: return <StepFonte data={fonte} onChange={setFonte} onNext={next} onBack={prev} />;
      case 2: return <StepMetadados data={metadados} onChange={setMetadados} onNext={next} onBack={prev} />;
      case 3: return <StepColunas data={colunas} onChange={setColunas} onNext={() => { syncDicionarizacao(); next(); }} onBack={prev} tabelaOrigem={metadados.nomeTabela} incluirDataRef={metadados.incluirColunaDataRef === "Sim"} />;
      case 4: return <StepDicionarizacao data={dicionarizacao} onChange={setDicionarizacao} onNext={() => { syncQualidade(); next(); }} onBack={prev} columnNames={getEffectiveColunas().map((c) => c.nome)} tabelaOrigem={metadados.nomeTabela} />;
      case 5: return <StepQualidade data={qualidade} onChange={setQualidade} onNext={next} onBack={prev} tabelaOrigem={metadados.nomeTabela} />;
      case 6: return <StepRevisao formData={{ sigla, fonte, metadados, colunas: { ...colunas, colunas: getEffectiveColunas() }, dicionarizacao, qualidade }} onSubmit={handleSubmit} onBack={prev} />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-3xl py-12">
        <div className="rounded-lg border border-border p-8">
          {renderStep()}
        </div>
        <StepIndicator totalSteps={TOTAL_STEPS} currentStep={step} />
      </div>
    </div>
  );
};

export default CreateIngestion;
