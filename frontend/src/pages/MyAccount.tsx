import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import { useAuth } from "../hooks/use-auth";
import { Loader2, User, Building, Database, Activity } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

interface AccountStats {
  username: string;
  siglas: { id: string; owner: string }[];
  ingestoes_cadastradas: number;
  ingestoes_total_siglas: number;
}

const MyAccount = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<AccountStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      if (!user?.token) return;
      try {
        const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/account-stats`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (error) {
        console.error("Erro ao carregar estatísticas da conta:", error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchStats();
  }, [user]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container max-w-4xl py-12 px-4">
        <div className="flex items-center gap-4 mb-8">
          <Link to="/">
            <Button variant="outline" size="icon" className="h-9 w-9">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-foreground">Minha Conta</h1>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : stats ? (
          <div className="space-y-8">
            {/* Header Profiling */}
            <div className="flex items-center gap-6 p-6 border border-border rounded-lg bg-card">
              <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                <User className="h-10 w-10 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">{stats.username}</h2>
                <p className="text-muted-foreground">Usuário Satus</p>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 border border-border rounded-lg bg-card">
                <div className="flex items-center gap-3 mb-2 text-muted-foreground">
                  <Database className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-sm uppercase tracking-wider">Ingestões Cadastradas</h3>
                </div>
                <p className="text-4xl font-bold text-foreground">
                  {stats.ingestoes_cadastradas}
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Total de ingestões solicitadas por você
                </p>
              </div>

              <div className="p-6 border border-border rounded-lg bg-card">
                <div className="flex items-center gap-3 mb-2 text-muted-foreground">
                  <Activity className="w-5 h-5 text-emerald-500" />
                  <h3 className="font-semibold text-sm uppercase tracking-wider">Ingestões das Siglas</h3>
                </div>
                <p className="text-4xl font-bold text-foreground">
                  {stats.ingestoes_total_siglas}
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Total de ingestões de todas as siglas que você pertence
                </p>
              </div>
            </div>

            {/* Siglas List */}
            <div className="p-6 border border-border rounded-lg bg-card">
              <div className="flex items-center gap-3 mb-6 text-muted-foreground">
                <Building className="w-5 h-5 text-primary" />
                <h3 className="font-semibold text-sm uppercase tracking-wider">Siglas que você pertence</h3>
              </div>
              
              {stats.siglas && stats.siglas.length > 0 ? (
                <div className="space-y-3">
                  {stats.siglas.map((s, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
                      <span className="font-medium">{s.id}</span>
                      <span className="text-xs bg-primary/10 text-primary border border-primary/20 px-3 py-1 rounded-full font-semibold">
                        Owner: {s.owner}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">Você não pertence a nenhuma sigla.</p>
              )}
            </div>

          </div>
        ) : (
          <div className="text-center text-muted-foreground py-20">
            Não foi possível carregar os dados da conta.
          </div>
        )}
      </div>
    </div>
  );
};

export default MyAccount;
