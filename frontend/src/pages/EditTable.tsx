import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import StepIndicator from "@/components/StepIndicator";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "../hooks/use-auth";
import { toast } from "sonner";
import { Loader2, Pencil, PlusCircle, Trash2, ArrowLeft, Save, Users } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";
const TOTAL_STEPS = 5;

interface Ingestion { id: number; tabela: string; status: string; detalhe: string; responsavel: string; sigla: string; }

interface ColumnDetail {
  nome: string; descricao: string; pii: string; pii_tipo: string; dq_rule: string;
  tipo_dado: string; particao: string;
}

interface IngestionDetailData {
  id: number; tabela_nome: string; criado_em: string; sigla: string;
  inicio_ingestao: string; data_criacao: string; descricao: string;
  periodicidade: string; formato_origem: string; tipo_atualizacao: string;
  status: string; aprovador: string; camada: string; sistema_origem: string;
  usage: string; limitacoes: string; classificacao_seguranca: string;
  retencao: string;
  colunas: ColumnDetail[];
}

interface EditableColumn {
  column_name: string; data_type: string; column_description: string;
  pii: boolean; pii_type_id: string; partition_column: boolean;
}

const DATA_TYPES = ["STRING", "INTEGER", "BIGINT", "FLOAT", "DATE", "TIMESTAMP", "BOOLEAN"];

const EditTable = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);

  const [ingestions, setIngestions] = useState<Ingestion[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<IngestionDetailData | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [consumers, setConsumers] = useState<{name?: string, email?: string}[]>([]);
  const [isLoadingConsumers, setIsLoadingConsumers] = useState(false);

  // Editable fields
  const [tableName, setTableName] = useState("");
  const [tableDescription, setTableDescription] = useState("");
  const [originFormat, setOriginFormat] = useState("");
  const [periodicity, setPeriodicity] = useState("");
  const [ingestionType, setIngestionType] = useState("");
  const [layer, setLayer] = useState("RAW");
  const [dataCriacao, setDataCriacao] = useState("");
  const [dataAtualizacao, setDataAtualizacao] = useState("");
  const [horario, setHorario] = useState("");
  const [columns, setColumns] = useState<EditableColumn[]>([]);
  const [partitionColumn, setPartitionColumn] = useState("Nenhuma");
  const [usage, setUsage] = useState("");
  const [limitations, setLimitations] = useState("");
  const [securityClassification, setSecurityClassification] = useState("Internal");
  const [retencao, setRetencao] = useState("Não se aplica");

  const piiTypes = ["N/A", "CPF", "CNPJ", "Email", "Nome", "RG", "Telefone", "Endereço"];

  useEffect(() => {
    async function fetchIngestions() {
      if (!user?.token) return;
      try {
        const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/list`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (res.status === 401) { localStorage.removeItem("auth_user"); window.location.href = "/login"; return; }
        if (res.ok) { const data = await res.json(); setIngestions(data.ingestions || []); }
      } catch { toast.error("Erro ao carregar ingestões."); }
      finally { setIsLoadingList(false); }
    }
    fetchIngestions();
  }, [user]);

  const handleSelectIngestion = async (id: number) => {
    if (!user?.token) return;
    setSelectedId(id);
    setIsLoadingDetail(true);
    setStep(1);
    try {
      const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/detail/${id}`, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
        if (res.ok) {
          const data: IngestionDetailData = await res.json();
          setDetail(data);
          setTableName(data.tabela_nome || "");
          setTableDescription(data.descricao || "");
          setOriginFormat(data.formato_origem || "");
          setPeriodicity(data.periodicidade || "");
          setIngestionType(data.tipo_atualizacao || "");
          setLayer(data.camada || "RAW");
          setDataCriacao(data.data_criacao ? data.data_criacao.split("T")[0] : "");
          setDataAtualizacao(data.inicio_ingestao ? data.inicio_ingestao.split("T")[0] : "");
          setHorario(""); // horario is not in db schema
          setColumns((data.colunas || []).map(c => ({
            column_name: c.nome,
            data_type: c.tipo_dado || "STRING",
            column_description: c.descricao || "",
            pii: (c.pii && c.pii !== "N/A" && c.pii !== "Não") ? true : false,
            pii_type_id: c.pii_tipo || "N/A",
            partition_column: c.particao === "Sim",
          })));
          const partitionCol = data.colunas?.find(c => c.particao === "Sim");
          setPartitionColumn(partitionCol ? partitionCol.nome : "Nenhuma");
          setUsage(data.usage || "");
          setLimitations(data.limitacoes || "");
          setSecurityClassification(data.classificacao_seguranca || "Internal");
          setRetencao(data.retencao || "Não se aplica");
        } else { toast.error("Erro ao carregar detalhes."); setStep(0); }
    } catch { toast.error("Erro ao carregar detalhes."); setStep(0); }
    finally { setIsLoadingDetail(false); }
  };

  useEffect(() => {
    if (detail?.id) {
      setIsLoadingConsumers(true);
      fetch(`${INGESTION_SERVICE_URL}/ingestion/impact-analysis/${detail.id}`, {
        headers: { Authorization: `Bearer ${user?.token}` },
      })
        .then(res => {
          if (!res.ok) throw new Error('Erro ao buscar análise de impacto');
          return res.json();
        })
        .then(data => {
          setConsumers(data.consumers || []);
        })
        .catch(err => {
          console.warn('Erro ao buscar consumidores:', err);
          setConsumers([]);
        })
        .finally(() => setIsLoadingConsumers(false));
    }
  }, [detail]);

  const addColumn = () => {
    setColumns([...columns, { column_name: "", data_type: "STRING", column_description: "", pii: false, pii_type_id: "N/A", partition_column: false }]);
  };

  const removeColumn = (idx: number) => {
    setColumns(columns.filter((_, i) => i !== idx));
  };

  const updateColumn = (idx: number, field: keyof EditableColumn, value: any) => {
    const updated = [...columns];
    (updated[idx] as any)[field] = value;
    setColumns(updated);
  };

  const handleSubmit = async () => {
    if (!user?.token || !selectedId) return;
    if (columns.length === 0) { toast.error("Adicione ao menos uma coluna."); return; }
    if (columns.some(c => !c.column_name)) { toast.error("Todas as colunas precisam de um nome."); return; }

    setIsSubmitting(true);
    try {
      const body = {
        table_metadata: {
          table_name: tableName,
          table_description: tableDescription,
          layer: layer,
          origin_id: 1,
          origin_format: originFormat,
          periodicity: periodicity,
          ingestion_type: ingestionType,
          inicio_atualizacao: dataAtualizacao,
          data_criacao: dataCriacao,
          horario: horario,
          tipo_atualizacao: ingestionType,
          usage: usage,
          limitations: limitations,
           security_classification: securityClassification,
           retention_months: retencao,
         },
         columns: columns.map(c => ({
          ...c,
          partition_column: c.column_name === partitionColumn,
          pii_type_id: c.pii ? c.pii_type_id : "N/A"
        })),
      };

      const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/edit/${selectedId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${user.token}`,
        },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        toast.success("Edição submetida para aprovação!");
        setStep(0);
        setSelectedId(null);
      } else {
        const err = await res.json();
        toast.error(err.detail || "Erro ao submeter edição.");
      }
    } catch (err) {
      toast.error("Erro de conexão com o servidor.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case "SUCCESS": return "bg-blue-500/10 text-blue-500 border-blue-500/20";
      case "APPROVED": return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
      case "FAILED":
      case "REJECTED": return "bg-destructive/10 text-destructive border-destructive/20";
      case "CANCELLED": return "bg-gray-500/10 text-gray-500 border-gray-500/20";
      case "PENDING_DELETE": return "bg-rose-500/10 text-rose-500 border-rose-500/20";
      case "DELETED": return "bg-gray-500/10 text-gray-400 border-gray-400/20";
      default: return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    }
  };
  const getStatusLabel = (s: string) => {
    switch (s?.toUpperCase()) { case "SUCCESS": return "Implantado com Sucesso"; case "APPROVED": return "Aprovada"; case "FAILED": return "Falhou"; case "REJECTED": return "Rejeitada"; case "CANCELLED": return "Cancelada"; case "PENDING_DELETE": return "Exclusão Pendente"; case "DELETED": return "Excluída"; default: return "Pendente"; }
  };

  const renderStep = () => {
    switch (step) {
      // ===== STEP 0: Lista de ingestões =====
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">Editar Ingestão</h2>
              <p className="text-sm text-muted-foreground mt-1">Selecione a ingestão que deseja editar.</p>
            </div>
            {isLoadingList ? (
              <div className="rounded-lg border border-border bg-background p-8 text-center text-muted-foreground">
                <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
                Carregando ingestões...
              </div>
            ) : ingestions.length === 0 ? (
              <div className="rounded-lg border border-border bg-background p-8 text-center text-muted-foreground">
                Nenhuma ingestão encontrada.
              </div>
            ) : (
              <div className="space-y-3">
                {ingestions.map((ing) => (
                  <button key={ing.id} onClick={() => handleSelectIngestion(ing.id)}
                    className="w-full text-left rounded-lg border border-border bg-background p-5 transition-all hover:bg-accent hover:border-primary/40 hover:shadow-sm group">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-base font-bold text-foreground mb-1">#{ing.id} - {ing.tabela}</h3>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground mt-2">
                          {ing.sigla && <span>Sigla: <strong>{ing.sigla}</strong></span>}
                          <span>Responsável: <strong>{ing.responsavel || "N/A"}</strong></span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-xs px-2.5 py-1 rounded-full border font-semibold ${getStatusColor(ing.status)}`}>
                          {getStatusLabel(ing.status)}
                        </span>
                        <Pencil className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
            <Button variant="outline" className="w-full" onClick={() => navigate("/")}>
              <ArrowLeft className="w-4 h-4 mr-2" /> Voltar ao Início
            </Button>
          </div>
        );

      // ===== STEP 1: Detalhes (leitura) =====
      case 1: {
        if (isLoadingDetail) {
          return (<div className="rounded-lg border border-border bg-background p-8 text-center text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" /> Carregando detalhes...
          </div>);
        }
        if (!detail) return null;
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">Detalhes da Ingestão #{detail.id}</h2>
              <p className="text-sm text-muted-foreground mt-1">Revise os dados atuais antes de editar.</p>
            </div>
            <div className="rounded-lg border border-border p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Sigla</label>
                  <Input value={detail.sigla || "N/A"} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Sistema de Origem</label>
                  <Input value={detail.sistema_origem || "N/A"} readOnly className="bg-muted" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Data para Criação da Tabela</label>
                  <Input value={detail.data_criacao ? new Date(detail.data_criacao).toLocaleDateString("pt-BR") : "N/A"} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Início das Atualizações</label>
                  <Input value={detail.inicio_ingestao ? new Date(detail.inicio_ingestao).toLocaleDateString("pt-BR") : "N/A"} readOnly className="bg-muted" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Tabela</label>
                  <Input value={detail.tabela_nome || "N/A"} readOnly className="bg-muted font-mono" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Descrição</label>
                  <Input value={detail.descricao || "N/A"} readOnly className="bg-muted" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Periodicidade</label>
                  <Input value={detail.periodicidade || "N/A"} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Formato de Origem</label>
                  <Input value={detail.formato_origem || "N/A"} readOnly className="bg-muted" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Tipo de Atualização / Ingestão</label>
                  <Input value={detail.tipo_atualizacao || "N/A"} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Camada</label>
                  <Input value={detail.camada || "RAW"} readOnly className="bg-muted font-mono" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Status</label>
                  <Input value={getStatusLabel(detail.status)} readOnly className="bg-muted font-semibold" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Gestor / Aprovador Responsável</label>
                  <Input value={detail.aprovador || "N/A"} readOnly className="bg-muted" /></div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground">Classificação de Segurança</label>
                  <Input value={detail.classificacao_seguranca || "Internal"} readOnly className="bg-muted font-semibold" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground">Retenção</label>
                  <Input value={detail.retencao || "Não se aplica"} readOnly className="bg-muted font-semibold" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground">Uso (Usage)</label>
                  <div className="text-sm p-3 bg-muted rounded-md border min-h-[60px] break-words whitespace-pre-wrap">{detail.usage || "Não informado"}</div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground">Limitações</label>
                  <div className="text-sm p-3 bg-muted rounded-md border min-h-[60px] break-words whitespace-pre-wrap">{detail.limitacoes || "Não informado"}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Hora da Ingestão (Criado em)</label>
                  <Input value={detail.criado_em ? new Date(detail.criado_em).toLocaleString("pt-BR") : "N/A"} readOnly className="bg-muted" /></div>
              </div>
              {detail.colunas && detail.colunas.length > 0 && (
                <div className="space-y-2 pt-2">
                  <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Estrutura de Colunas</p>
                  <div className="grid grid-cols-6 gap-3 text-xs font-medium text-muted-foreground">
                    <span>Coluna</span><span>Tipo de Dado</span><span>Descrição</span><span>PII / LGPD</span><span>Tipo PII</span><span>Partição</span>
                  </div>
                  {detail.colunas.map((col, i) => (
                    <div key={i} className="grid grid-cols-6 gap-3">
                      <Input value={col.nome} readOnly className="bg-muted text-xs font-mono" />
                      <Input value={col.tipo_dado || "N/A"} readOnly className="bg-muted text-xs" />
                      <Input value={col.descricao || ""} readOnly className="bg-muted text-xs" />
                      <Input value={col.pii || "N/A"} readOnly className="bg-muted text-xs" />
                      <Input value={col.pii_tipo || "N/A"} readOnly className="bg-muted text-xs" />
                      <Input value={col.particao || "Não"} readOnly className="bg-muted text-xs" />
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="flex gap-4">
              <Button variant="outline" className="flex-1" onClick={() => { setStep(0); setDetail(null); }}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
              </Button>
              <Button className="flex-1" size="lg" onClick={() => setStep(2)}>
                <Pencil className="w-4 h-4 mr-2" /> Editar esta ingestão
              </Button>
            </div>
          </div>
        );
      }

      // ===== STEP 2: Formulário de edição =====
      case 2:
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-foreground">Editando Ingestão #{selectedId}</h2>

            <div className="rounded-lg border border-border p-6 space-y-4">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Metadados da Tabela</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Tabela <Pencil className="h-3 w-3" /></label>
                  <Input value={tableName} onChange={(e) => setTableName(e.target.value)} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Descrição <Pencil className="h-3 w-3" /></label>
                  <Input value={tableDescription} onChange={(e) => setTableDescription(e.target.value)} />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Periodicidade <Pencil className="h-3 w-3" /></label>
                  <Select value={periodicity} onValueChange={setPeriodicity}>
                    <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                    <SelectContent>
                      {["Diária", "Semanal", "Mensal", "Tempo Real", "Unica"].map(v => (
                        <SelectItem key={v} value={v}>{v}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Formato Origem <Pencil className="h-3 w-3" /></label>
                  <Select value={originFormat} onValueChange={setOriginFormat}>
                    <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                    <SelectContent>
                      {["csv", "json", "JSON API", "xml", "parquet", "orc", "Tabela relacional", "N/A"].map(v => (
                        <SelectItem key={v} value={v}>{v}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                 <div className="space-y-1">
                   <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Tipo Ingestão <Pencil className="h-3 w-3" /></label>
                  <Select value={ingestionType} onValueChange={setIngestionType}>
                    <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                    <SelectContent>
                      {["Batch", "Micro-Batch", "Streaming"].map(v => (
                        <SelectItem key={v} value={v}>{v}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Horário <Pencil className="h-3 w-3" /></label>
                  <Input type="time" value={horario} onChange={(e) => setHorario(e.target.value)} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Data Criação da Tabela <Pencil className="h-3 w-3" /></label>
                  <Input type="date" value={dataCriacao} onChange={(e) => setDataCriacao(e.target.value)} />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Data Início Atualizações <Pencil className="h-3 w-3" /></label>
                  <Input type="date" value={dataAtualizacao} onChange={(e) => setDataAtualizacao(e.target.value)} />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Classificação de Segurança <Pencil className="h-3 w-3" /></label>
                <Select value={securityClassification} onValueChange={setSecurityClassification}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {["Internal", "Confidencial", "Restrito", "Secreto", "Público"].map(v => (
                      <SelectItem key={v} value={v}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Uso (Usage) <Pencil className="h-3 w-3" /></label>
                  <textarea value={usage} onChange={(e) => setUsage(e.target.value)}
                    placeholder="Descreva o uso previsto para esses dados"
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Limitações <Pencil className="h-3 w-3" /></label>
                  <textarea value={limitations} onChange={(e) => setLimitations(e.target.value)}
                    placeholder="Descreva as limitações conhecidas"
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" />
                </div>
              </div>
              <div className="space-y-2 mt-4">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">Retenção <Pencil className="h-3 w-3" /></label>
                <Select value={retencao} onValueChange={setRetencao}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Não se aplica">Não se aplica</SelectItem>
                    {Array.from({ length: 120 }, (_, i) => i + 1).map(m => (
                      <SelectItem key={m} value={String(m)}>{m} {m === 1 ? 'mês' : 'meses'}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Colunas editáveis */}
            <div className="rounded-lg border border-border p-6 space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Colunas</p>
                <Button variant="outline" size="sm" onClick={addColumn} className="gap-1">
                  <PlusCircle className="w-4 h-4" /> Adicionar coluna
                </Button>
              </div>

              {columns.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">Nenhuma coluna. Clique em "Adicionar coluna".</p>
              ) : (
                <div className="space-y-3">
                  <div className="grid grid-cols-[1fr_120px_1fr_80px_120px_40px] gap-2 text-xs font-medium text-muted-foreground px-1">
                    <span>Nome</span><span>Tipo</span><span>Descrição</span><span>PII</span><span>Tipo PII</span><span></span>
                  </div>
                  {columns.map((col, i) => (
                    <div key={i} className="grid grid-cols-[1fr_120px_1fr_80px_120px_40px] gap-2 items-center">
                      <Input value={col.column_name} onChange={(e) => updateColumn(i, "column_name", e.target.value)}
                        placeholder="nome_coluna" className="text-xs font-mono" />
                      <Select value={col.data_type} onValueChange={(v) => updateColumn(i, "data_type", v)}>
                        <SelectTrigger className="text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {DATA_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                        </SelectContent>
                      </Select>
                      <Input value={col.column_description} onChange={(e) => updateColumn(i, "column_description", e.target.value)}
                        placeholder="Descrição" className="text-xs" />
                      <Select value={col.pii ? "Sim" : "Não"} onValueChange={(v) => {
                          updateColumn(i, "pii", v === "Sim");
                          if (v === "Não") updateColumn(i, "pii_type_id", "N/A");
                        }}>
                        <SelectTrigger className="text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Sim">Sim</SelectItem>
                          <SelectItem value="Não">Não</SelectItem>
                        </SelectContent>
                      </Select>
                      <Select value={col.pii_type_id} onValueChange={(v) => updateColumn(i, "pii_type_id", v)} disabled={!col.pii}>
                        <SelectTrigger className="text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {piiTypes.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                        </SelectContent>
                      </Select>
                      <button onClick={() => removeColumn(i)} className="text-destructive hover:text-destructive/80 transition-colors mx-auto">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  
                  <div className="pt-4 space-y-2 border-t mt-4">
                    <label className="text-sm font-medium text-foreground">Coluna de partição</label>
                    <Select value={partitionColumn} onValueChange={setPartitionColumn}>
                      <SelectTrigger className="max-w-[300px]"><SelectValue placeholder="Selecione" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Nenhuma">Nenhuma</SelectItem>
                        {columns.filter(c => c.column_name).map((c, idx) => (
                          <SelectItem key={idx} value={c.column_name}>{c.column_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <Button variant="outline" className="flex-1" onClick={() => setStep(1)}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
              </Button>
              <Button className="flex-1" size="lg" onClick={() => setStep(3)}>
                Revisar alterações
              </Button>
            </div>
          </div>
        );

      // ===== STEP 3: Resumo e enviar =====
      case 3:
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-foreground">Resumo das Edições</h2>

            <div className="rounded-lg border border-border p-6 space-y-4">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Metadados</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Tabela</label>
                  <Input value={tableName} readOnly className="bg-muted font-mono" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Descrição</label>
                  <Input value={tableDescription} readOnly className="bg-muted" /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Periodicidade</label>
                  <Input value={periodicity} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Formato</label>
                  <Input value={originFormat} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Tipo Ingestão</label>
                  <Input value={ingestionType} readOnly className="bg-muted" /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Horário</label>
                  <Input value={horario || "N/A"} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Data Criação</label>
                  <Input value={dataCriacao ? new Date(dataCriacao).toLocaleDateString("pt-BR", { timeZone: "UTC" }) : "N/A"} readOnly className="bg-muted" /></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Data Atualizações</label>
                  <Input value={dataAtualizacao ? new Date(dataAtualizacao).toLocaleDateString("pt-BR", { timeZone: "UTC" }) : "N/A"} readOnly className="bg-muted" /></div>
              </div>
              <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Classificação de Segurança</label>
                <Input value={securityClassification || "Internal"} readOnly className="bg-muted font-semibold" /></div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Uso (Usage)</label>
                  <div className="text-sm p-3 bg-muted rounded-md border min-h-[60px] break-words whitespace-pre-wrap">{usage || "Não informado"}</div></div>
                <div className="space-y-1"><label className="text-xs font-medium text-muted-foreground">Limitações</label>
                  <div className="text-sm p-3 bg-muted rounded-md border min-h-[60px] break-words whitespace-pre-wrap">{limitations || "Não informado"}</div></div>
              </div>
            </div>

            <div className="rounded-lg border border-border p-6 space-y-4">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Colunas ({columns.length})</p>
              {columns.length > 0 && (
                <>
                  <div className="grid grid-cols-[1fr_100px_1fr_60px_100px_60px] gap-2 text-xs font-medium text-muted-foreground">
                    <span>Nome</span><span>Tipo</span><span>Descrição</span><span>PII</span><span>Tipo PII</span><span>Partição</span>
                  </div>
                  {columns.map((col, i) => {
                    const isPartition = col.column_name === partitionColumn;
                    return (
                      <div key={i} className="grid grid-cols-[1fr_100px_1fr_60px_100px_60px] gap-2">
                        <Input value={col.column_name} readOnly className="bg-muted text-xs font-mono" />
                        <Input value={col.data_type} readOnly className="bg-muted text-xs" />
                        <Input value={col.column_description || "—"} readOnly className="bg-muted text-xs" />
                        <Input value={col.pii ? "Sim" : "Não"} readOnly className="bg-muted text-xs text-center" />
                        <Input value={col.pii ? col.pii_type_id : "N/A"} readOnly className="bg-muted text-xs text-center" />
                        <Input value={isPartition ? "Sim" : "Não"} readOnly className="bg-muted text-xs text-center" />
                      </div>
                    );
                  })}
                </>
              )}
            </div>

            <div className="flex gap-4">
              <Button variant="outline" className="flex-1" onClick={() => setStep(2)}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Voltar para edição
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button className="flex-1 gap-2" size="lg" disabled={isSubmitting}>
                    {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Submeter edição
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle className="flex items-center gap-2 text-foreground">
                        <Users className="w-5 h-5 text-amber-500" />
                        Impacto da Edição
                      </AlertDialogTitle>
                      <AlertDialogDescription asChild>
                        <div className="space-y-3 pt-2 text-sm text-muted-foreground">
                          <p>
                            As alterações na tabela  <strong className="text-foreground">#{detail.id} - {detail.tabela_nome}</strong>  impactarão os seguintes usuários consumidores da base de dados. A submissão desta edição enviará uma notificação para que eles fiquem cientes das mudanças propostas.:
                          </p>
                        <div className="rounded-md border border-border bg-muted/40 p-3 space-y-1">
                          {isLoadingConsumers ? (
                            <div className="flex items-center gap-2 text-xs text-muted-foreground italic">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Carregando consumidores...
                            </div>
                          ) : consumers.length > 0 ? (
                            <>
                              <p className="text-xs font-semibold text-foreground">usuários afetados:</p>
                              <div className="flex flex-wrap gap-1.5 pt-1">
                                {consumers.map((c, i) => (
                                  <span key={i} className="bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded text-xs font-mono">
                                    {c.email || c.name}
                                  </span>
                                ))}
                              </div>
                            </>
                          ) : (
                            <p className="text-xs text-muted-foreground italic">Nenhum consumidor encontrado para esta tabela.</p>
                          )}
                        </div>
                          <p className="text-xs text-muted-foreground">
                            Deseja confirmar a submissão destas alterações?
                          </p>
                        </div>
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancelar</AlertDialogCancel>
                      <AlertDialogAction onClick={handleSubmit} className="bg-primary text-primary-foreground hover:bg-primary/90 gap-2">
                        <Save className="w-4 h-4" />
                        Confirmar e Submeter
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
            </div>
          </div>
        );

      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-4xl py-12">
        {renderStep()}
        {step >= 1 && <StepIndicator totalSteps={TOTAL_STEPS} currentStep={step} />}
      </div>
    </div>
  );
};

export default EditTable;
