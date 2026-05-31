import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import StepIndicator from "@/components/StepIndicator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Pencil, PlusCircle } from "lucide-react";
import { toast } from "sonner";

const TOTAL_STEPS = 4;

const mockTableData = {
  sigla: "MKTI",
  dataInicio: "01/05/2026",
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

const EditTable = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);

  // Step 1
  const [sigla, setSigla] = useState("");
  const [gestorAprovador, setGestorAprovador] = useState("");

  // Step 2
  const [tabela, setTabela] = useState("");
  const [gestorAprovador2, setGestorAprovador2] = useState("");

  // Step 3 - editable fields
  const [editData, setEditData] = useState(mockTableData);
  const [editingColunas, setEditingColunas] = useState(false);

  const next = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div className="rounded-lg border border-border p-8 space-y-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">Editando ingestao de dados</h2>
              <p className="text-sm text-muted-foreground">Defina sua sigla</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Sigla</label>
                <Select value={sigla} onValueChange={setSigla}>
                  <SelectTrigger><SelectValue placeholder="Selecione a sigla" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MKTI">MKTI - Marketing Interno</SelectItem>
                    <SelectItem value="FINS">FINS - Financeiro</SelectItem>
                    <SelectItem value="RHUM">RHUM - Recursos Humanos</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Gestor Aprovador</label>
                <Input placeholder="Rubens Silva" value={gestorAprovador} onChange={(e) => setGestorAprovador(e.target.value)} />
              </div>
            </div>
            <Button className="w-full" size="lg" onClick={next}>Continue</Button>
          </div>
        );

      case 1:
        return (
          <div className="rounded-lg border border-border p-8 space-y-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">Editando tabela</h2>
              <p className="text-sm text-muted-foreground">Escolha a tabela para adição</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Tabela</label>
                <Select value={tabela} onValueChange={setTabela}>
                  <SelectTrigger><SelectValue placeholder="Selecione a tabela" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MKTI_TABE_ORAC_VENDAS">MKTI_TABE_ORAC_VENDAS</SelectItem>
                    <SelectItem value="MKTI_TABE_CLIENTES">MKTI_TABE_CLIENTES</SelectItem>
                    <SelectItem value="MKTI_TABE_ORAC_ANUNCIOS">MKTI_TABE_ORAC_ANUNCIOS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Gestor Aprovador</label>
                <Input placeholder="Rubens Silva" value={gestorAprovador2} onChange={(e) => setGestorAprovador2(e.target.value)} />
              </div>
            </div>
            <Button className="w-full" size="lg" onClick={next}>Continue</Button>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-foreground">Editando tabela</h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Sigla</label>
                <Input value={editData.sigla} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  Data Inicio <Pencil className="h-3 w-3" />
                </label>
                <Input
                  value={editData.dataInicio}
                  onChange={(e) => setEditData({ ...editData, dataInicio: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  Tabela <Pencil className="h-3 w-3" />
                </label>
                <Input value={editData.tabela} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  Descrição <Pencil className="h-3 w-3" />
                </label>
                <Input
                  value={editData.descricao}
                  onChange={(e) => setEditData({ ...editData, descricao: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Periodicidade</label>
                <Input value={editData.periodicidade} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Horario</label>
                <Input value={editData.horario} readOnly className="bg-muted" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">DAT_REF_CARGA</label>
                <Input value={editData.datRefCarga} readOnly className="bg-muted" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Tipo Atualização</label>
                <Input value={editData.tipoAtualizacao} readOnly className="bg-muted" />
              </div>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-4 gap-3 text-xs font-medium text-muted-foreground">
                <span className="flex items-center gap-1">Colunas <Pencil className="h-3 w-3" /></span>
                <span className="flex items-center gap-1">Descrição <Pencil className="h-3 w-3" /></span>
                <span className="flex items-center gap-1">PII <Pencil className="h-3 w-3" /></span>
                <span className="flex items-center gap-1">DQ_RULE <Pencil className="h-3 w-3" /></span>
              </div>
              {editData.colunas.map((col, i) => (
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

      case 3:
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-foreground">Resumo Edicoes</h2>

            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Sigla</label>
              <Input value={editData.sigla} readOnly className="bg-muted w-64" />
            </div>

            <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Tabela</label>
                <Input value={editData.tabela} readOnly className="bg-muted" />
              </div>
              <PlusCircle className="h-6 w-6 text-primary mt-5" />
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Tabela</label>
                <Input value={editData.tabela} readOnly className="bg-muted" />
              </div>
            </div>

            <div className="grid grid-cols-[1fr_1fr] gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Colunas</label>
                <Input value="CD_CLIE(INTEGER)_PK" readOnly className="bg-muted text-xs" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Colunas</label>
                <Input value="DELETED" readOnly className="bg-muted text-xs" />
              </div>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-[1fr_1fr_1fr_1fr_auto] gap-3 text-xs font-medium text-muted-foreground">
                <span className="flex items-center gap-1">Colunas <Pencil className="h-3 w-3" /></span>
                <span className="flex items-center gap-1">Descrição <Pencil className="h-3 w-3" /></span>
                <span className="flex items-center gap-1">PII <Pencil className="h-3 w-3" /></span>
                <span className="flex items-center gap-1">DQ_RULE <Pencil className="h-3 w-3" /></span>
                <span></span>
              </div>
              {editData.colunas.map((col, i) => (
                <div key={i} className="grid grid-cols-[1fr_1fr_1fr_1fr_auto] gap-3 items-center">
                  <Input value={col.nome} readOnly className="bg-muted text-xs" />
                  <Input value={col.descricao} readOnly className="bg-muted text-xs" />
                  <Input value={col.pii} readOnly className="bg-muted text-xs" />
                  <Input value={col.dqRule} readOnly className="bg-muted text-xs" />
                  {i === editData.colunas.length - 1 && (
                    <PlusCircle className="h-6 w-6 text-primary" />
                  )}
                </div>
              ))}
            </div>

            <Button className="w-full" size="lg" onClick={() => {
              toast.success("Edição enviada com sucesso!");
              navigate("/");
            }}>
              Continuar
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
      <div className="container max-w-4xl py-12">
        {renderStep()}
        <StepIndicator totalSteps={TOTAL_STEPS} currentStep={step} />
      </div>
    </div>
  );
};

export default EditTable;
