import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import StepIndicator from "@/components/StepIndicator";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../hooks/use-auth";
import { toast } from "sonner";
import { Loader2, Trash2, AlertTriangle, ArrowLeft, Users } from "lucide-react";
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

const TOTAL_STEPS = 3;

interface Ingestion {
  id: number;
  tabela: string;
  status: string;
  detalhe: string;
  responsavel: string;
  sigla: string;
}

interface ColumnDetail {
  nome: string;
  descricao: string;
  pii: string;
  dq_rule: string;
  tipo_dado: string;
  particao: string;
}

interface IngestionDetail {
  id: number;
  tabela_nome: string;
  criado_em: string;
  sigla: string;
  inicio_ingestao: string;
  data_criacao: string;
  descricao: string;
  periodicidade: string;
  formato_origem: string;
  tipo_atualizacao: string;
  status: string;
  aprovador: string;
  camada: string;
  sistema_origem: string;
  colunas: ColumnDetail[];
}

const DeleteTable = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);

  // Step 0: lista de ingestões
  const [ingestions, setIngestions] = useState<Ingestion[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Step 1: detalhes da ingestão selecionada
  const [detail, setDetail] = useState<IngestionDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Step 2: exclusão
  const [isDeleting, setIsDeleting] = useState(false);
  const [consumers, setConsumers] = useState<{name?: string, email?: string}[]>([]);
  const [isLoadingConsumers, setIsLoadingConsumers] = useState(false);
  const [dataExclusao, setDataExclusao] = useState("");

  // Buscar lista de ingestões ao montar
  useEffect(() => {
    async function fetchIngestions() {
      if (!user?.token) return;
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/list`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (response.status === 401) {
          localStorage.removeItem("auth_user");
          window.location.href = "/login";
          return;
        }
        if (response.ok) {
          const data = await response.json();
          setIngestions(data.ingestions || []);
        }
      } catch (error) {
        console.error("Erro ao carregar ingestões:", error);
        toast.error("Erro ao carregar lista de ingestões.");
      } finally {
        setIsLoadingList(false);
      }
    }
    fetchIngestions();
  }, [user]);

  // Buscar detalhes ao selecionar ingestão e ir para step 1
  const handleSelectIngestion = async (id: number) => {
    if (!user?.token) return;
    setSelectedId(id);
    setIsLoadingDetail(true);
    setStep(1);
    try {
      const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/detail/${id}`, {
        headers: { Authorization: `Bearer ${user.token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setDetail(data);
      } else {
        toast.error("Erro ao carregar detalhes da ingestão.");
        setStep(0);
      }
    } catch {
      toast.error("Erro ao carregar detalhes da ingestão.");
      setStep(0);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Solicitar exclusão (soft delete)
  const handleDelete = async () => {
    if (!user?.token || !selectedId) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/delete/${selectedId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${user.token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        toast.success("Solicitação de exclusão enviada para aprovação! Aguarde o gestor aprovar.");
        navigate("/");
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail ?? "Erro ao solicitar exclusão.");
      }
    } catch {
      toast.error("Erro ao tentar solicitar exclusão.");
    } finally {
      setIsDeleting(false);
    }
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
      case "REJECTED":
        return "bg-destructive/10 text-destructive border-destructive/20";
      case "CANCELLED":
        return "bg-gray-500/10 text-gray-500 border-gray-500/20";
      case "PENDING_DELETE":
        return "bg-rose-500/10 text-rose-500 border-rose-500/20";
      case "DELETED":
        return "bg-gray-500/10 text-gray-400 border-gray-400/20";
      default:
        return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "APPROVED": return "Aprovada";
      case "REJECTED": return "Rejeitada";
      case "CANCELLED": return "Cancelada";
      case "PENDING_DELETE": return "Exclusão Pendente";
      case "DELETED": return "Excluída";
      default: return "Pendente";
    }
  };

  const renderStep = () => {
    switch (step) {
      // ========== STEP 0: Listar ingestões para seleção ==========
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">Solicitar Exclusão de Ingestão</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Selecione a ingestão que deseja solicitar exclusão. A exclusão precisa ser aprovada pelo gestor.
              </p>
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
                  <button
                    key={ing.id}
                    onClick={() => handleSelectIngestion(ing.id)}
                    className="w-full text-left rounded-lg border border-border bg-background p-5 transition-all hover:bg-accent hover:border-destructive/40 hover:shadow-sm group"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-base font-bold text-foreground mb-1">
                          #{ing.id} - {ing.tabela}
                        </h3>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground mt-2">
                          {ing.sigla && (
                            <span>Sigla: <strong>{ing.sigla}</strong></span>
                          )}
                          <span>Responsável: <strong>{ing.responsavel || "N/A"}</strong></span>
                          {ing.detalhe && (
                            <span>• Última operação: <strong>{ing.detalhe}</strong></span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-xs px-2.5 py-1 rounded-full border font-semibold ${getStatusColor(ing.status)}`}>
                          {getStatusLabel(ing.status)}
                        </span>
                        <Trash2 className="w-4 h-4 text-muted-foreground group-hover:text-destructive transition-colors" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            <Button variant="outline" className="w-full" onClick={() => navigate("/")}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Voltar ao Início
            </Button>
          </div>
        );

      // ========== STEP 1: Detalhes da ingestão selecionada ==========
      case 1: {
        if (isLoadingDetail) {
          return (
            <div className="rounded-lg border border-border bg-background p-8 text-center text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
              Carregando detalhes da ingestão...
            </div>
          );
        }
        if (!detail) return null;

        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">Confirmar Solicitação de Exclusão</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Revise os dados da ingestão <strong>#{detail.id}</strong> antes de solicitar a exclusão.
              </p>
            </div>

            <div className="rounded-lg border border-border p-6 space-y-4">
              <p className="text-lg font-bold text-foreground">Overview da Ingestão</p>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Sigla</label>
                  <Input value={detail.sigla || "N/A"} readOnly className="bg-muted" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Data Criação</label>
                  <Input value={detail.data_criacao ? new Date(detail.data_criacao).toLocaleDateString("pt-BR") : "N/A"} readOnly className="bg-muted" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Status</label>
                  <Input value={getStatusLabel(detail.status)} readOnly className="bg-muted font-semibold" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Tabela</label>
                  <Input value={detail.tabela_nome || "N/A"} readOnly className="bg-muted font-mono" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Sistema de Origem</label>
                  <Input value={detail.sistema_origem || "N/A"} readOnly className="bg-muted" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Descrição</label>
                  <Input value={detail.descricao || "Sem descrição"} readOnly className="bg-muted" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Formato de Origem</label>
                  <Input value={detail.formato_origem || "N/A"} readOnly className="bg-muted" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Periodicidade</label>
                  <Input value={detail.periodicidade || "N/A"} readOnly className="bg-muted" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Tipo Atualização</label>
                  <Input value={detail.tipo_atualizacao || "N/A"} readOnly className="bg-muted" />
                </div>
              </div>

              {/* Colunas */}
              {detail.colunas && detail.colunas.length > 0 && (
                <div className="space-y-3 pt-2">
                  <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Colunas</p>
                  <div className="grid grid-cols-4 gap-3 text-xs font-medium text-muted-foreground">
                    <span>Coluna</span><span>Tipo</span><span>PII</span><span>Regra DQ</span>
                  </div>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {detail.colunas.map((col, i) => (
                      <div key={i} className="grid grid-cols-4 gap-3">
                        <Input value={col.nome} readOnly className="bg-muted text-xs font-mono" />
                        <Input value={col.tipo_dado || "N/A"} readOnly className="bg-muted text-xs" />
                        <Input value={col.pii || "N/A"} readOnly className="bg-muted text-xs" />
                        <Input value={col.dq_rule || "Nenhuma"} readOnly className="bg-muted text-xs" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <Button variant="outline" className="flex-1" onClick={() => { setStep(0); setDetail(null); setSelectedId(null); }}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar
              </Button>
              <Button className="flex-1" size="lg" onClick={() => setStep(2)}>
                Continuar para exclusão
              </Button>
            </div>
          </div>
        );
      }

      // ========== STEP 2: Confirmação final e exclusão ==========
      case 2: {
        if (!detail) return null;
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-foreground">Confirmar Solicitação de Exclusão</h2>

            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-6 space-y-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-base font-bold text-foreground">
                    Atenção! Esta solicitação precisa de aprovação.
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Ao confirmar, a ingestão <strong>#{detail.id} - {detail.tabela_nome}</strong> será marcada como
                    <strong> pendente de exclusão</strong>. O gestor/aprovador responsável precisará aprovar
                    a solicitação para que a exclusão seja efetivada. Os dados não serão removidos até a aprovação.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Ingestão</label>
                  <Input value={`#${detail.id} - ${detail.tabela_nome}`} readOnly className="bg-muted font-mono" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">Sigla</label>
                  <Input value={detail.sigla || "N/A"} readOnly className="bg-muted" />
                </div>
              </div>

              <div className="space-y-1 pt-2">
                <label className="text-xs font-medium text-muted-foreground">Data para executar a exclusão</label>
                <Input
                  type="date"
                  placeholder="dd/mm/aaaa"
                  value={dataExclusao}
                  onChange={(e) => setDataExclusao(e.target.value)}
                />
              </div>
            </div>

            <div className="flex gap-4">
              <Button variant="outline" className="flex-1" onClick={() => setStep(1)}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="destructive"
                    className="flex-1 gap-2"
                    size="lg"
                    disabled={isDeleting}
                  >
                    {isDeleting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                    Solicitar exclusão
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle className="flex items-center gap-2 text-foreground">
                      <Users className="w-5 h-5 text-rose-500" />
                      Impacto da Exclusão
                    </AlertDialogTitle>
                    <AlertDialogDescription asChild>
                      <div className="space-y-3 pt-2 text-sm text-muted-foreground">
                        <p>
                          A exclusão da tabela <strong className="text-foreground">#{detail.id} - {detail.tabela_nome}</strong> impactará os seguintes membros da sigla <strong className="text-foreground">{detail?.sigla}</strong>:
                        </p>
                        <div className="rounded-md border border-border bg-muted/40 p-3 space-y-1">
                          {isLoadingConsumers ? (
                            <div className="flex items-center gap-2 text-xs text-muted-foreground italic">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Carregando consumidores...
                            </div>
                          ) : consumers.length > 0 ? (
                            <>
                              <p className="text-xs font-semibold text-foreground">Time(s) afetado(s):</p>
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
                          Deseja confirmar a solicitação de exclusão para aprovação?
                        </p>
                      </div>
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Voltar</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90 gap-2">
                      <Trash2 className="w-4 h-4" />
                      Confirmar Solicitação de Exclusão
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        );
      }

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-3xl py-12">
        {renderStep()}
        {step >= 1 && <StepIndicator totalSteps={TOTAL_STEPS} currentStep={step} />}
      </div>
    </div>
  );
};

export default DeleteTable;
