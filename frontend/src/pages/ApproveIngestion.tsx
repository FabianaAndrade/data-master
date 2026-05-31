import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../hooks/use-auth";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

interface PendingIngestion {
  id: number;
  tabela: string;
  status: string;
  detalhe?: string;
  responsavel?: string;
}

interface IngestionDetailData {
  id: number;
  tabela_nome: string;
  sigla: string;
  aprovador: string;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const ApproveIngestion = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [pendingList, setPendingList] = useState<PendingIngestion[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [selectedDetail, setSelectedDetail] = useState<IngestionDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [parecer, setParecer] = useState("");

  useEffect(() => {
    async function fetchPending() {
      if (!user?.token) return;
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/list`, {
          headers: { "Authorization": `Bearer ${user.token}` },
        });
        if (response.ok) {
          const data: PendingIngestion[] = await response.json();
          // Filter only PENDING_APPROVAL status
          const filtered = data.filter((ing) => ing.status === "PENDING_APPROVAL");
          setPendingList(filtered);
        }
      } catch (error) {
        console.error("Erro ao carregar ingestões pendentes:", error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchPending();
  }, [user]);

  useEffect(() => {
    async function fetchDetail() {
      if (!user?.token || !selectedId) {
        setSelectedDetail(null);
        return;
      }
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/detail/${selectedId}`, {
          headers: { "Authorization": `Bearer ${user.token}` },
        });
        if (response.ok) {
          const data = await response.json();
          setSelectedDetail(data);
        }
      } catch (error) {
        console.error("Erro ao carregar detalhes da ingestão:", error);
      }
    }
    fetchDetail();
  }, [selectedId, user]);

  const handleAction = async (action: "aprovar" | "reprovar") => {
    if (!selectedId || !user?.token) return;
    setIsSubmitting(true);
    try {
      const endpoint = action === "aprovar" ? "approve" : "reject";
      const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/${endpoint}/${selectedId}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${user.token}` },
      });

      if (response.ok) {
        toast.success(`Ingestão ${action === "aprovar" ? "aprovada" : "reprovada"} com sucesso!`);
        navigate("/");
      } else {
        toast.error("Erro ao processar ação.");
      }
    } catch (error) {
      console.error(error);
      toast.error("Erro ao tentar processar ação.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-3xl py-12 px-4">
        <h1 className="text-2xl font-bold text-foreground mb-8">Ingestões pendentes de aprovação</h1>

        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : pendingList.length === 0 ? (
          <div className="rounded-lg border border-border bg-background p-12 text-center text-muted-foreground">
            Não há nenhuma ingestão pendente de aprovação no momento.
          </div>
        ) : (
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">Selecionar Ingestão Pendente</label>
              <Select value={selectedId} onValueChange={setSelectedId}>
                <SelectTrigger><SelectValue placeholder="Selecione uma ingestão para revisar" /></SelectTrigger>
                <SelectContent>
                  {pendingList.map((ing) => (
                    <SelectItem key={ing.id} value={ing.id.toString()}>
                      #{ing.id} - {ing.tabela} (por {ing.responsavel})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedDetail && (
              <div className="space-y-6 border border-border bg-muted/10 p-6 rounded-lg">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Sigla</label>
                  <Input value={selectedDetail.sigla || ""} readOnly className="bg-muted font-medium" />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Usuário criador da ingestão</label>
                  <Input value={pendingList.find(i => i.id.toString() === selectedId)?.responsavel || ""} readOnly className="bg-muted" />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Nome da tabela</label>
                  <Input value={selectedDetail.tabela_nome || ""} readOnly className="bg-muted font-mono" />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Parecer do Aprovador</label>
                  <Input
                    placeholder="Digite um parecer de aprovação ou rejeição (opcional)"
                    value={parecer}
                    onChange={(e) => setParecer(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2">
                  <Button size="lg" disabled={isSubmitting} onClick={() => handleAction("aprovar")}>
                    {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Aprovar Ingestão
                  </Button>
                  <Button variant="secondary" size="lg" disabled={isSubmitting} onClick={() => handleAction("reprovar")}>
                    Reprovar Ingestão
                  </Button>
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
