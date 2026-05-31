import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { useAuth } from "../hooks/use-auth";
import { Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Ingestion {
  id: number;
  tabela: string;
  status: string;
  detalhe?: string;
  responsavel?: string;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const IngestionHistory = () => {
  const { user } = useAuth();
  const [ingestions, setIngestions] = useState<Ingestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchIngestions() {
      if (!user?.token) return;
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/list`, {
          headers: {
            "Authorization": `Bearer ${user.token}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setIngestions(data);
        }
      } catch (error) {
        console.error("Erro ao carregar histórico:", error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchIngestions();
  }, [user]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
      case "REJECTED":
        return "bg-destructive/10 text-destructive border-destructive/20";
      default:
        return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "Aprovada";
      case "REJECTED":
        return "Rejeitada";
      default:
        return "Pendente";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-3xl py-12 px-4">
        <div className="flex items-center gap-4 mb-8">
          <Link to="/">
            <Button variant="outline" size="icon" className="h-9 w-9">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-foreground">Histórico de ingestões</h1>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : ingestions.length === 0 ? (
          <div className="rounded-lg border border-border bg-background p-12 text-center text-muted-foreground">
            Nenhuma ingestão cadastrada no banco de dados.
          </div>
        ) : (
          <div className="space-y-4">
            {ingestions.map((ing) => (
              <Link
                key={ing.id}
                to={`/ingestion-detail/${ing.id}`}
                className="block rounded-lg border border-border bg-background p-6 transition-all hover:bg-accent hover:border-primary/30"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-foreground">
                      #{ing.id} - {ing.tabela}
                    </h3>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mt-2">
                      <span>Responsável: <strong>{ing.responsavel || "N/A"}</strong></span>
                      {ing.detalhe && (
                        <span>• Operação: <strong>{ing.detalhe}</strong></span>
                      )}
                    </div>
                  </div>
                  <span className={`text-xs px-2.5 py-1 rounded-full border font-semibold ${getStatusColor(ing.status)}`}>
                    {getStatusLabel(ing.status)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default IngestionHistory;
