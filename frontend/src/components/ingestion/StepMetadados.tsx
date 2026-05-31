import { useState, useEffect } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../../hooks/use-auth";

interface StepMetadadosProps {
  data: {
    nomeTabela: string;
    periodicidade: string;
    tipoIngestao: string;
    horario: string;
    dataCriacao: string;
    dataAtualizacao: string;
    atualizacao: string;
    incluirColunaDataRef: string;
  };
  tabelaOrigem?: string;
  onChange: (data: StepMetadadosProps["data"]) => void;
  onNext: () => void;
  onBack?: () => void;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const StepMetadados = ({ data, tabelaOrigem, onChange, onNext, onBack }: StepMetadadosProps) => {
  const { user } = useAuth();
  const [opcoes, setOpcoes] = useState({
    periodicidade: [] as string[],
    tipoIngestao: [] as string[],
    atualizacao: [] as string[],
    incluirColunaDataRef: [] as string[],
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function fetchMetadados() {
      const targetTabela = tabelaOrigem || data.nomeTabela || "default";
      if (!user?.token) return;

      setIsLoading(true);
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/metadados/${targetTabela}`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });

        if (response.ok) {
          const resData = await response.json();
          
          if (resData.opcoes) {
            setOpcoes(resData.opcoes);
          }
        }
      } catch (error) {
        console.error("Error fetching metadados options:", error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchMetadados();
  }, [tabelaOrigem, user]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Criando nova ingestão de dados</h2>
        <p className="text-sm text-muted-foreground">Defina os metadados</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Nome da tabela</label>
          <Input
            placeholder="Nome da Tabela"
            value={data.nomeTabela || ""}
            onChange={(e) => onChange({ ...data, nomeTabela: e.target.value.replace(/[^a-zA-Z0-9_]/g, '') })}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Periodicidade</label>
          <Select value={data.periodicidade} onValueChange={(v) => onChange({ ...data, periodicidade: v })}>
            <SelectTrigger disabled={isLoading}><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {opcoes.periodicidade.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Tipo ingestão</label>
          <Select value={data.tipoIngestao} onValueChange={(v) => onChange({ ...data, tipoIngestao: v })}>
            <SelectTrigger disabled={isLoading}><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {opcoes.tipoIngestao.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Horário</label>
          <Input type="time" placeholder="14:30" value={data.horario} onChange={(e) => onChange({ ...data, horario: e.target.value })} />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Data para criação da tabela</label>
          <Input type="date" placeholder="29/04/2026" value={data.dataCriacao} onChange={(e) => onChange({ ...data, dataCriacao: e.target.value })} />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Data inicio de atualizações</label>
          <Input type="date" placeholder="29/04/2026" value={data.dataAtualizacao} onChange={(e) => onChange({ ...data, dataAtualizacao: e.target.value })} />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Atualização</label>
          <Select value={data.atualizacao} onValueChange={(v) => onChange({ ...data, atualizacao: v })}>
            <SelectTrigger disabled={isLoading}><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {opcoes.atualizacao.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Incluir coluna de data referencia da carga?</label>
          <Select value={data.incluirColunaDataRef} onValueChange={(v) => onChange({ ...data, incluirColunaDataRef: v })}>
            <SelectTrigger disabled={isLoading}><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {opcoes.incluirColunaDataRef.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex gap-4 pt-4">
        {onBack && <Button variant="outline" className="w-1/3 border-primary/50 hover:bg-primary/10" onClick={onBack}>Voltar</Button>}
        <Button className="flex-1" size="lg" onClick={onNext} disabled={!data.nomeTabela}>Continue</Button>
      </div>
    </div>
  );
};

export default StepMetadados;
