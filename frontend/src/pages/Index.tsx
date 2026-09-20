import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Plus, Pencil, Trash2, CheckCircle, ArrowRight, Activity, Shield } from "lucide-react";
import Navbar from "@/components/Navbar";
import { useAuth } from "../hooks/use-auth";

const actions = [
  { icon: Plus, label: "Criar nova ingestão", href: "/create-ingestion" },
  { icon: Pencil, label: "Editar tabela", href: "/edit-table" },
  { icon: Trash2, label: "Excluir tabela", href: "/delete-table" },
  { icon: CheckCircle, label: "Aprovar ingestão de dados", href: "/approve-ingestion" },
];

interface Ingestion {
  id: number;
  tabela: string;
  status: string;
  detalhe: string;
  responsavel: string;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const Index = () => {
  const { user } = useAuth();
  const [ingestions, setIngestions] = useState<Ingestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchIngestions() {
      if (!user?.token) return;
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/list?username=${encodeURIComponent(user.username)}`, {
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
          setIngestions(data.ingestions || []);
        }
      } catch (error) {
        console.error("Erro ao carregar ingestões:", error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchIngestions();
  }, [user]);

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case "SUCCESS":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20";
      case "APPROVED":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
      case "FAILED":
      case "REJECTED":
        return "bg-destructive/10 text-destructive border-destructive/20";
      default:
        return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status?.toUpperCase()) {
      case "SUCCESS":
        return "Implantado com Sucesso";
      case "APPROVED":
        return "Aprovada";
      case "FAILED":
        return "Falhou";
      case "REJECTED":
        return "Rejeitada";
      default:
        return "Pendente";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="bg-muted/50 min-h-[calc(100vh-3.5rem)] py-12">
        <div className="container max-w-4xl px-4">
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold text-foreground mb-2 tracking-tight">
              Bem-vindo ao Aggron!
            </h1>
            <p className="text-lg text-muted-foreground">
              Governe de ponta a ponta o ciclo de vida dos seus dados.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Actions Sidebar */}
            <div className="md:col-span-1 space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Ações
              </h2>
              <div className="space-y-2">
                {actions.map((action) => (
                  <Link
                    key={action.label}
                    to={action.href}
                    className="flex items-center gap-3 rounded-lg border border-border bg-background p-4 text-foreground transition-all hover:bg-accent hover:border-primary/50 group"
                  >
                    <action.icon className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    <span className="text-sm font-medium">{action.label}</span>
                  </Link>
                ))}
              </div>
            </div>

            {/* Ingestions List */}
            <div className="md:col-span-2 space-y-4">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                  Minhas ingestões
                </h2>
                <Link to="/ingestions" className="text-xs text-primary hover:underline flex items-center gap-1">
                  Ver histórico <ArrowRight className="w-3 h-3" />
                </Link>
              </div>

              {isLoading ? (
                <div className="rounded-lg border border-border bg-background p-8 text-center text-muted-foreground">
                  <Activity className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
                  Carregando ingestões do banco...
                </div>
              ) : ingestions.length === 0 ? (
                <div className="rounded-lg border border-border bg-background p-8 text-center text-muted-foreground">
                  Nenhuma ingestão encontrada no banco.
                </div>
              ) : (
                <div className="space-y-3">
                  {ingestions.map((ing) => (
                    <Link
                      key={ing.id}
                      to={`/ingestion-detail/${ing.id}`}
                      className="block rounded-lg border border-border bg-background p-5 transition-all hover:bg-accent hover:border-primary/30 hover:shadow-sm"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-base font-bold text-foreground mb-1">
                            #{ing.id} - {ing.tabela}
                          </h3>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground mt-2">
                            <span>Responsável: <strong>{ing.responsavel || "N/A"}</strong></span>
                            {ing.detalhe && (
                              <span>• Última operação: <strong>{ing.detalhe}</strong></span>
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
        </div>
      </div>
    </div>
  );
};

export default Index;
