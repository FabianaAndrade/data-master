import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../hooks/use-auth";
import { toast } from "sonner";
import { Loader2, XOctagon, Trash2 } from "lucide-react";

interface ColumnDetail {
  nome: string;
  descricao: string;
  pii: string;
  pii_tipo: string;
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

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const IngestionDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [detail, setDetail] = useState<IngestionDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleCancel = async () => {
    if (!user?.token || !id) return;
    if (!confirm("Tem certeza que deseja cancelar esta ingestão?")) return;
    setIsCancelling(true);
    try {
      const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/cancel/${id}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${user.token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        toast.success("Ingestão cancelada com sucesso.");
        navigate("/");
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail ?? "Erro ao cancelar ingestão.");
      }
    } catch {
      toast.error("Erro ao tentar cancelar ingestão.");
    } finally {
      setIsCancelling(false);
    }
  };

  const handleDelete = async () => {
    if (!user?.token || !id) return;
    if (!confirm("Tem certeza que deseja solicitar a exclusão desta ingestão? A solicitação precisará ser aprovada pelo gestor.")) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/delete/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${user.token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        toast.success("Solicitação de exclusão enviada para aprovação.");
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
    async function fetchDetail() {
      if (!user?.token || !id) return;
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/detail/${id}`, {
          headers: {
            "Authorization": `Bearer ${user.token}`,
          },
        });
        if (response.status === 401) {
          localStorage.removeItem("auth_user");
          window.location.href = "/login";
          return;
        }
        if (response.ok) {
          const data = await response.json();
          setDetail(data);
        } else {
          toast.error("Ingestão não encontrada.");
          navigate("/");
        }
      } catch (error) {
        console.error("Erro ao carregar detalhes:", error);
        toast.error("Erro ao carregar detalhes da ingestão.");
      } finally {
        setIsLoading(false);
      }
    }

    fetchDetail();
  }, [id, user, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[calc(100vh-3.5rem)]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!detail) return null;

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "APPROVED": return "Aprovada";
      case "REJECTED": return "Rejeitada";
      case "PENDING_DELETE": return "Exclusão Pendente";
      case "DELETED": return "Excluída";
      case "CANCELLED": return "Cancelada";
      default: return "Pendente de Aprovação";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-4xl py-12 px-4">
        <h1 className="text-2xl font-bold text-foreground mb-1">
          #{detail.id} - {detail.tabela_nome}
        </h1>
        <p className="text-sm text-muted-foreground mb-8">
          Criado em: {detail.criado_em ? new Date(detail.criado_em).toLocaleDateString("pt-BR") : "N/A"}
        </p>

        <div className="space-y-6">
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
              <Input value={detail.data_criacao ? new Date(detail.data_criacao).toLocaleDateString("pt-BR") : "N/A"} readOnly className="bg-muted" />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground">Início das Atualizações</label>
              <Input value={detail.inicio_ingestao ? new Date(detail.inicio_ingestao).toLocaleDateString("pt-BR") : "N/A"} readOnly className="bg-muted" />
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

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground">Status</label>
              <Input value={getStatusLabel(detail.status)} readOnly className="bg-muted font-semibold" />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground">Gestor / Aprovador Responsável</label>
              <Input value={detail.aprovador || "N/A"} readOnly className="bg-muted font-medium" />
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

          <div className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Estrutura de Colunas
            </h3>
            <div className="grid grid-cols-6 gap-3 text-xs font-semibold text-muted-foreground px-2">
              <span>Coluna</span>
              <span>Tipo de Dado</span>
              <span>Descrição</span>
              <span>PII / LGPD</span>
              <span>Tipo PII</span>
              <span>Partição</span>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {detail.colunas && detail.colunas.length > 0 ? (
                detail.colunas.map((col, i) => (
                  <div key={i} className="grid grid-cols-6 gap-3">
                    <Input value={col.nome} readOnly className="bg-muted text-xs font-mono" />
                    <Input value={col.tipo_dado || "N/A"} readOnly className="bg-muted text-xs font-mono" />
                    <Input value={col.descricao || "Sem descrição"} readOnly className="bg-muted text-xs" />
                    <Input value={col.pii || "N/A"} readOnly className="bg-muted text-xs font-medium" />
                    <Input value={col.pii_tipo || "N/A"} readOnly className="bg-muted text-xs" />
                    <Input value={col.particao || "Não"} readOnly className="bg-muted text-xs font-medium" />
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground p-2">Nenhuma coluna cadastrada.</p>
              )}
            </div>
          </div>

          <div className="flex gap-4 justify-end pt-4">
            {/* Excluir: disponível para o criador/owner */}
            {detail.status !== "CANCELLED" && detail.status !== "PENDING_DELETE" && detail.status !== "DELETED" && (
              <Button
                variant="destructive"
                className="gap-2"
                disabled={isDeleting}
                onClick={handleDelete}
              >
                {isDeleting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Solicitar exclusão
              </Button>
            )}
            {/* Cancelar: apenas se não for APPROVED nem CANCELLED */}
            {detail.status !== "APPROVED" && detail.status !== "CANCELLED" && (
              <Button
                variant="destructive"
                className="gap-2"
                disabled={isCancelling}
                onClick={handleCancel}
              >
                {isCancelling ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <XOctagon className="w-4 h-4" />
                )}
                Cancelar ingestão
              </Button>
            )}
            <Button variant="outline" className="border-primary/50 hover:bg-primary/10" onClick={() => navigate("/")}>
              Voltar ao Início
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IngestionDetail;

