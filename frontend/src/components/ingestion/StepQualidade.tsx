import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { useAuth } from "../../hooks/use-auth";
import { Check } from "lucide-react";

interface ColRule {
  coluna: string;
  regras: string[];
}

interface StepQualidadeProps {
  data: { configurar: string; colunas: ColRule[] };
  tabelaOrigem?: string;
  onChange: (data: StepQualidadeProps["data"]) => void;
  onNext: () => void;
  onBack?: () => void;
}

interface OptionRule {
  nome: string;
  descricao: string;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const StepQualidade = ({ data, tabelaOrigem, onChange, onNext, onBack }: StepQualidadeProps) => {
  const { user } = useAuth();
  const [regrasDisponiveis, setRegrasDisponiveis] = useState<OptionRule[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function fetchRules() {
      if (!user?.token) return;
      setIsLoading(true);
      try {
        const targetTabela = tabelaOrigem || "global";
        const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/quality_rules/${targetTabela}`, {
           headers: { Authorization: `Bearer ${user.token}` }
        });
        if (res.ok) {
           const json = await res.json();
           if (json.regras) setRegrasDisponiveis(json.regras);
        }
      } catch (err) {
        console.error("Failed to fetch quality rules", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchRules();
  }, [tabelaOrigem, user]);

  const toggleRule = (colIndex: number, regra: string) => {
    const colunas = [...data.colunas];
    const currentRules = colunas[colIndex].regras || [];
    if (currentRules.includes(regra)) {
      colunas[colIndex].regras = currentRules.filter(r => r !== regra);
    } else {
      colunas[colIndex].regras = [...currentRules, regra];
    }
    onChange({ ...data, colunas });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Criando nova ingestão de dados</h2>
        <p className="text-sm text-muted-foreground">Regras de Qualidade de dados para {tabelaOrigem}</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Configurar regras de qualidade de dados?</label>
          <Select value={data.configurar} onValueChange={(v) => onChange({ ...data, configurar: v })}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="Sim">Sim</SelectItem>
              <SelectItem value="Não">Não</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {data.configurar === "Sim" && (
          <div className="space-y-6 mt-4">
            {data.colunas.map((col, i) => (
              <div key={i} className="space-y-2 border border-border p-4 rounded-md bg-muted/20">
                <Input value={col.coluna || "Coluna não informada"} readOnly className="font-mono text-sm font-bold bg-muted" />
                <div className="flex flex-wrap gap-2 pt-2">
                  {regrasDisponiveis.map((rule) => {
                    const isSelected = (col.regras || []).includes(rule.nome);
                    return (
                      <button
                        key={rule.nome}
                        onClick={() => toggleRule(i, rule.nome)}
                        className={`text-xs px-3 py-1.5 rounded-full border flex items-center gap-1 transition-colors ${
                          isSelected 
                            ? "bg-primary text-primary-foreground border-primary" 
                            : "bg-background text-muted-foreground hover:bg-muted"
                        }`}
                        title={rule.descricao}
                      >
                        {isSelected && <Check className="w-3 h-3" />}
                        {rule.descricao}
                      </button>
                    );
                  })}
                  {regrasDisponiveis.length === 0 && isLoading && <span className="text-xs text-muted-foreground">Carregando regras...</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-4 pt-4">
        {onBack && <Button variant="outline" className="w-1/3 border-primary/50 hover:bg-primary/10" onClick={onBack}>Voltar</Button>}
        <Button className="flex-1" size="lg" onClick={onNext}>Continue</Button>
      </div>
    </div>
  );
};

export default StepQualidade;
