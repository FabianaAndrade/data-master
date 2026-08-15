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
    camada: string;
    usage: string;
    limitacoes: string;
    classificacaoSeguranca: string;
    retencao: string;
  };

  onChange: (data: StepMetadadosProps["data"]) => void;
  onNext: () => void;
  onBack?: () => void;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

/** Retorna a data de hoje no formato YYYY-MM-DD (compatível com input[type=date]) */
const todayISO = () => new Date().toISOString().split("T")[0];

const StepMetadados = ({ data, onChange, onNext, onBack }: StepMetadadosProps) => {
  const { user } = useAuth();
  const [opcoes, setOpcoes] = useState({
    periodicidade: [] as string[],
    tipoIngestao: [] as string[],
    atualizacao: [] as string[],
    incluirColunaDataRef: [] as string[],
  });
  const [isLoading, setIsLoading] = useState(false);

  // ── Validação de datas ────────────────────────────────────────────────────
  const today = todayISO();
  const errCriacao =
    data.dataCriacao && data.dataCriacao < today
      ? "A data de criação deve ser maior ou igual à data atual."
      : "";
  const errAtualizacao =
    data.dataAtualizacao && data.dataCriacao && data.dataAtualizacao <= data.dataCriacao
      ? "A data de início de atualizações deve ser maior que a data de criação."
      : "";
  const datesValid = !errCriacao && !errAtualizacao;

  useEffect(() => {
    async function fetchMetadados() {
      const targetTabela = data.nomeTabela || "default";
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
  }, [user]);

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
          <label className="text-sm font-medium text-foreground">Camada</label>
          <Select value={data.camada} onValueChange={(v) => onChange({ ...data, camada: v })}>
            <SelectTrigger disabled={isLoading}><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="bronze">bronze</SelectItem>
              <SelectItem value="silver">silver</SelectItem>
              <SelectItem value="gold">gold</SelectItem>
            </SelectContent>
          </Select>
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
          <Input
            type="date"
            min={today}
            value={data.dataCriacao}
            onChange={(e) => onChange({ ...data, dataCriacao: e.target.value })}
            className={errCriacao ? "border-destructive focus-visible:ring-destructive" : ""}
          />
          {errCriacao && <p className="text-xs text-destructive">{errCriacao}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Data inicio de atualizações</label>
          <Input
            type="date"
            min={data.dataCriacao ? (() => { const d = new Date(data.dataCriacao); d.setDate(d.getDate() + 1); return d.toISOString().split("T")[0]; })() : today}
            value={data.dataAtualizacao}
            onChange={(e) => onChange({ ...data, dataAtualizacao: e.target.value })}
            className={errAtualizacao ? "border-destructive focus-visible:ring-destructive" : ""}
            disabled={!data.dataCriacao}
          />
          {!data.dataCriacao && <p className="text-xs text-muted-foreground">Preencha a data de criação primeiro.</p>}
          {errAtualizacao && <p className="text-xs text-destructive">{errAtualizacao}</p>}
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

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Uso (Usage)</label>
          <textarea
            placeholder="Descreva o uso previsto para esses dados"
            value={data.usage || ""}
            onChange={(e) => onChange({ ...data, usage: e.target.value })}
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Limitações</label>
          <textarea
            placeholder="Descreva as limitações conhecidas dos dados"
            value={data.limitacoes || ""}
            onChange={(e) => onChange({ ...data, limitacoes: e.target.value })}
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Classificação de Segurança</label>
          <Select value={data.classificacaoSeguranca || "Internal"} onValueChange={(v) => onChange({ ...data, classificacaoSeguranca: v })}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="Internal">Internal</SelectItem>
              <SelectItem value="Confidencial">Confidencial</SelectItem>
              <SelectItem value="Restrito">Restrito</SelectItem>
              <SelectItem value="Secreto">Secreto</SelectItem>
              <SelectItem value="Público">Público</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Retenção</label>
          <Select value={data.retencao || "Não se aplica"} onValueChange={(v) => onChange({ ...data, retencao: v })}>
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

      <div className="flex gap-4 pt-4">
        {onBack && <Button variant="outline" className="w-1/3 border-primary/50 hover:bg-primary/10" onClick={onBack}>Voltar</Button>}
        <Button className="flex-1" size="lg" onClick={onNext} disabled={!data.nomeTabela || !datesValid}>Continue</Button>
      </div>
    </div>
  );
};

export default StepMetadados;
