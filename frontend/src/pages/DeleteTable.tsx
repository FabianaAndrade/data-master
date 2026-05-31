import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import StepIndicator from "@/components/StepIndicator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const TOTAL_STEPS = 4;

const mockOverview = {
  sigla: "MKTI",
  dataCriacao: "01/05/2026",
  size: "10GB",
  tabela: "TABE_ORAC_ANUNCIOS",
  descricao: "Tabela com informacoes de clientes devedores em 2025",
  periodicidade: "Diaria",
  horario: "14h30",
  datRefCarga: "SIM",
  tipoAtualizacao: "Batch",
  colunas: [
    { nome: "CD_CLIE(INTEGER)_PK", descricao: "CD_CLIE", pii: "CPF", dqRule: "VALIDA_NULOS" },
    { nome: "CD_BAND_CAR(INTEGER_PK)", descricao: "CD_BAND_CART", pii: "NÃO", dqRule: "VALIDA_BANDEIRA_CARTAO" },
  ],
};

const DeleteTable = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [sigla, setSigla] = useState("");
  const [gestorAprovador, setGestorAprovador] = useState("");
  const [dataExclusao, setDataExclusao] = useState("");
  const [tabela, setTabela] = useState("");
  const [siglaConsumidor, setSiglaConsumidor] = useState("");

  const next = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div className="rounded-lg border border-border p-8 space-y-6">
            <h2 className="text-xl font-bold text-foreground">Tabela: Dados Fictícios</h2>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Sigla</label>
                <Select value={sigla} onValueChange={setSigla}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MKTI">MKTI - Marketing Interno</SelectItem>
                    <SelectItem value="FINS">FINS - Financeiro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Gestor Aprovador</label>
                <Input placeholder="Rubens Silva" value={gestorAprovador} onChange={(e) => setGestorAprovador(e.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Data para executar a exclusão</label>
                <Input placeholder="13/12/2027" value={dataExclusao} onChange={(e) => setDataExclusao(e.target.value)} />
              </div>
            </div>
            <Button className="w-full" size="lg" onClick={next}>Excluir</Button>
          </div>
        );

      case 1:
        return (
          <div className="rounded-lg border border-border p-8 space-y-6">
            <h2 className="text-xl font-bold text-foreground">Excluir base</h2>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Tabela</label>
                <Select value={tabela} onValueChange={setTabela}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MKTI_TABE_ORAC_VENDAS">MKTI_TABE_ORAC_VENDAS</SelectItem>
                    <SelectItem value="MKTI_TABE_CLIENTES">MKTI_TABE_CLIENTES</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Data para executar a exclusão</label>
                <Input placeholder="13/12/2027" value={dataExclusao} onChange={(e) => setDataExclusao(e.target.value)} />
              </div>
            </div>
            <Button className="w-full" size="lg" onClick={next}>Excluir</Button>
          </div>
        );

      case 2: {
        const o = mockOverview;
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">Excluindo tabela</h2>
              <p className="text-lg font-bold text-foreground">Overview Base</p>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Sigla</label>
                <Input value={o.sigla} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Data Criação tabela</label>
                <Input value={o.dataCriacao} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Size</label>
                <Input value={o.size} readOnly className="bg-muted" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Tabela</label>
                <Input value={o.tabela} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Descrição</label>
                <Input value={o.descricao} readOnly className="bg-muted" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Periodicidade</label>
                <Input value={o.periodicidade} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Horario</label>
                <Input value={o.horario} readOnly className="bg-muted" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">DAT_REF_CARGA</label>
                <Input value={o.datRefCarga} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Tipo Atualização</label>
                <Input value={o.tipoAtualizacao} readOnly className="bg-muted" />
              </div>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-4 gap-3 text-xs font-medium text-muted-foreground">
                <span>Colunas</span><span>Descrição</span><span>PII</span><span>DQ_RULE</span>
              </div>
              {o.colunas.map((col, i) => (
                <div key={i} className="grid grid-cols-4 gap-3">
                  <Input value={col.nome} readOnly className="bg-muted text-xs" />
                  <Input value={col.descricao} readOnly className="bg-muted text-xs" />
                  <Input value={col.pii} readOnly className="bg-muted text-xs" />
                  <Input value={col.dqRule} readOnly className="bg-muted text-xs" />
                </div>
              ))}
            </div>

            <Button className="w-full" size="lg" onClick={next}>Continuar</Button>
          </div>
        );
      }

      case 3:
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-foreground">Resumo Edicoes</h2>

            <div className="space-y-2">
              <p className="text-lg font-bold text-foreground">
                Atenção! A tabela escolhida possui usuários consumidores.
                Ao seguir com a exclusão as seguintes siglas serão notificadas
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Sigla</label>
              <Select value={siglaConsumidor} onValueChange={setSiglaConsumidor}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="RHDP">RHDP - Recursos humanos e Depatamento pessoal</SelectItem>
                  <SelectItem value="FINS">FINS - Financeiro</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button className="w-full" size="lg" onClick={() => {
              const id = `DATAEXC${Math.floor(Math.random() * 900) + 100}`;
              navigate(`/delete-success/${id}`);
            }}>
              Submeter
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-3xl py-12">
        {renderStep()}
        {step >= 2 && <StepIndicator totalSteps={TOTAL_STEPS} currentStep={step} />}
      </div>
    </div>
  );
};

export default DeleteTable;
