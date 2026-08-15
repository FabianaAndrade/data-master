import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../hooks/use-auth";
import { toast } from "sonner";
import { Loader2, CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react";

// ── Tipos ─────────────────────────────────────────────────────────────────────

interface PendingIngestion {
  ingestion_id: number;
  table_name: string;
  status: string;
  sigla_name: string;
  solicitante: string;
  created_at: string;
  should_be_approved_until: string;
}

interface ColumnDetail {
  nome: string;
  descricao: string;
  pii: string;
  dq_rule: string;
  tipo_dado: string;
  particao: string;
}

interface IngestionDetailData {
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
  usage: string;
  limitacoes: string;
  classificacao_seguranca: string;
  colunas: ColumnDetail[];
}

// ── Constantes ────────────────────────────────────────────────────────────────

const APPROVAL_SERVICE_URL =
  (import.meta as any).env.VITE_APPROVAL_SERVICE_URL ?? "http://localhost:8003";
const INGESTION_SERVICE_URL =
  (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmtDate = (d?: string) =>
  d ? new Date(d).toLocaleDateString("pt-BR") : "N/A";

const getDaysRemaining = (deadline: string) => {
  const diff = Math.ceil(
    (new Date(deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  );
  return diff;
};

// ── Componente ────────────────────────────────────────────────────────────────

const ApproveIngestion = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [pendingList, setPendingList] = useState<PendingIngestion[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [approvalMeta, setApprovalMeta] = useState<PendingIngestion | null>(null);
  const [detail, setDetail] = useState<IngestionDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [parecer, setParecer] = useState("");

  // Busca pendentes para o owner autenticado
  useEffect(() => {
    async function fetchPending() {
      if (!user?.token) return;
      setIsLoading(true);
      try {
        const res = await fetch(`${APPROVAL_SERVICE_URL}/api/v1/approvals/pending`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setPendingList(data.pendentes ?? []);
        } else {
          const err = await res.json().catch(() => ({}));
          toast.error(err.detail ?? "Erro ao carregar ingestões pendentes.");
        }
      } catch {
        toast.error("Não foi possível conectar ao serviço de aprovação.");
      } finally {
        setIsLoading(false);
      }
    }
    fetchPending();
  }, [user]);

  // Ao selecionar, busca detalhe completo via ingestion_service (mesmo formato do IngestionDetail)
  useEffect(() => {
    if (!selectedId || !user?.token) {
      setDetail(null);
      setApprovalMeta(null);
      return;
    }

    const meta = pendingList.find((p) => p.ingestion_id.toString() === selectedId) ?? null;
    setApprovalMeta(meta);

    async function fetchDetail() {
      setIsLoadingDetail(true);
      try {
        const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/detail/${selectedId}`, {
          headers: { Authorization: `Bearer ${user!.token}` },
        });
        if (res.ok) {
          setDetail(await res.json());
        } else {
          toast.error("Erro ao carregar detalhes da ingestão.");
        }
      } catch {
        toast.error("Erro ao carregar detalhes.");
      } finally {
        setIsLoadingDetail(false);
      }
    }
    fetchDetail();
  }, [selectedId, user, pendingList]);

  const handleAction = async (action: "approve" | "reject") => {
    if (!selectedId || !user?.token) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(
        `${APPROVAL_SERVICE_URL}/api/v1/approvals/${selectedId}/${action}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${user.token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ motivo: parecer }),
        }
      );
      if (res.ok) {
        toast.success(action === "approve" ? "Ingestão aprovada!" : "Ingestão reprovada!");
        navigate("/");
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail ?? "Erro ao processar ação.");
      }
    } catch {
      toast.error("Erro ao tentar processar ação.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-4xl py-12 px-4">
        <h1 className="text-2xl font-bold text-foreground mb-1">
          Ingestões pendentes de aprovação
        </h1>
        <p className="text-sm text-muted-foreground mb-8">
          Apenas ingestões da(s) sua(s) sigla(s) aparecem aqui. Você não pode aprovar
          solicitações que você mesmo criou.
        </p>

        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : pendingList.length === 0 ? (
          <div className="rounded-lg border border-border bg-background p-12 text-center text-muted-foreground">
            Não há nenhuma ingestão pendente de aprovação para a sua sigla no momento.
          </div>
        ) : (
          <div className="space-y-6">
            {/* Selector */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">
                Selecionar Ingestão Pendente
              </label>
              <Select value={selectedId} onValueChange={setSelectedId}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma ingestão para revisar" />
                </SelectTrigger>
                <SelectContent>
                  {pendingList.map((ing) => {
                    const days = getDaysRemaining(ing.should_be_approved_until);
                    return (
                      <SelectItem key={ing.ingestion_id} value={ing.ingestion_id.toString()}>
                        #{ing.ingestion_id} — {ing.table_name ?? "tabela"} ({ing.sigla_name}) —{" "}
                        {days > 0 ? `${days}d restantes` : "⚠️ Expirado"}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* Detalhe completo */}
            {isLoadingDetail ? (
              <div className="flex justify-center py-10">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : detail && approvalMeta && (
              <div className="space-y-6 border border-border rounded-lg p-6">

                {/* Cabeçalho */}
                <div>
                  <h2 className="text-xl font-bold text-foreground">
                    #{detail.id} - {detail.tabela_nome}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    Criado em: {fmtDate(detail.criado_em)}
                  </p>
                </div>

                {/* Alerta de prazo */}
                {getDaysRemaining(approvalMeta.should_be_approved_until) <= 2 && (
                  <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded p-3">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>
                      Prazo expira em{" "}
                      <strong>{approvalMeta.should_be_approved_until}</strong>. Após isso, a
                      solicitação será cancelada automaticamente.
                    </span>
                  </div>
                )}

                {/* Metadados — mesma grade do IngestionDetail */}
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Sigla</label>
                      <Input value={detail.sigla || "N/A"} readOnly className="bg-muted font-medium" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Sistema de Origem</label>
                      <Input value={detail.sistema_origem || "N/A"} readOnly className="bg-muted font-medium" />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Data para Criação da Tabela</label>
                      <Input value={fmtDate(detail.data_criacao)} readOnly className="bg-muted" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Início das Atualizações</label>
                      <Input value={fmtDate(detail.inicio_ingestao)} readOnly className="bg-muted" />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Tabela</label>
                      <Input value={detail.tabela_nome || "N/A"} readOnly className="bg-muted font-mono" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Descrição</label>
                      <Input value={detail.descricao || "Sem descrição informada."} readOnly className="bg-muted" />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Periodicidade</label>
                      <Input value={detail.periodicidade || "N/A"} readOnly className="bg-muted" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Formato de Origem</label>
                      <Input value={detail.formato_origem || "N/A"} readOnly className="bg-muted font-mono" />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Tipo de Atualização / Ingestão</label>
                      <Input value={detail.tipo_atualizacao || "N/A"} readOnly className="bg-muted" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Camada</label>
                      <Input value={detail.camada || "RAW"} readOnly className="bg-muted font-mono" />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground">Classificação de Segurança</label>
                    <Input value={detail.classificacao_seguranca || "Internal"} readOnly className="bg-muted font-semibold" />
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
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground">Solicitante</label>
                      <Input value={approvalMeta.solicitante || "N/A"} readOnly className="bg-muted" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Prazo de Aprovação
                      </label>
                      <Input value={approvalMeta.should_be_approved_until} readOnly className="bg-muted" />
                    </div>
                  </div>
                </div>

                {/* Estrutura de Colunas */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                    Estrutura de Colunas
                  </h3>
                  <div className="grid grid-cols-6 gap-3 text-xs font-semibold text-muted-foreground px-2">
                    <span>Coluna</span>
                    <span>Tipo de Dado</span>
                    <span>Descrição</span>
                    <span>PII / LGPD</span>
                    <span>Regra de Qualidade</span>
                    <span>Partição</span>
                  </div>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {detail.colunas && detail.colunas.length > 0 ? (
                      detail.colunas.map((col, i) => (
                        <div key={i} className="grid grid-cols-6 gap-3">
                          <Input value={col.nome} readOnly className="bg-muted text-xs font-mono" />
                          <Input value={col.tipo_dado || "N/A"} readOnly className="bg-muted text-xs font-mono" />
                          <Input value={col.descricao || "—"} readOnly className="bg-muted text-xs" />
                          <Input value={col.pii || "N/A"} readOnly className="bg-muted text-xs font-medium" />
                          <Input value={col.dq_rule || "Nenhuma"} readOnly className="bg-muted text-xs" />
                          <Input value={col.particao || "Não"} readOnly className="bg-muted text-xs font-medium" />
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-muted-foreground p-2">Nenhuma coluna cadastrada.</p>
                    )}
                  </div>
                </div>

                {/* Ações */}
                <div className="space-y-3 pt-2 border-t border-border">
                  <div className="space-y-1">
                    <label className="text-sm font-semibold text-foreground">
                      Parecer (opcional)
                    </label>
                    <Input
                      placeholder="Digite um comentário sobre a aprovação ou rejeição"
                      value={parecer}
                      onChange={(e) => setParecer(e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <Button
                      size="lg"
                      disabled={isSubmitting}
                      className="gap-2"
                      onClick={() => handleAction("approve")}
                    >
                      {isSubmitting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <CheckCircle className="w-4 h-4" />
                      )}
                      Aprovar
                    </Button>
                    <Button
                      variant="destructive"
                      size="lg"
                      disabled={isSubmitting}
                      className="gap-2"
                      onClick={() => handleAction("reject")}
                    >
                      <XCircle className="w-4 h-4" />
                      Reprovar
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApproveIngestion;
