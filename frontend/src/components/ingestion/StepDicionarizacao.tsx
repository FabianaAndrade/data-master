import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../../hooks/use-auth";
import { Sparkles } from "lucide-react";

interface ColDesc {
  coluna: string;
  descricao: string;
}

interface StepDicionarizacaoProps {
  data: { descricaoTabela: string; colunas: ColDesc[] };
  onChange: (data: StepDicionarizacaoProps["data"]) => void;
  onNext: () => void;
  onBack?: () => void;
  columnNames: string[];
  tabelaOrigem?: string;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const StepDicionarizacao = ({ data, onChange, onNext, onBack, columnNames, tabelaOrigem }: StepDicionarizacaoProps) => {
  const { user } = useAuth();
  const [isGenerating, setIsGenerating] = useState(false);

  const updateCol = (i: number, field: keyof ColDesc, value: string) => {
    const colunas = [...data.colunas];
    colunas[i] = { ...colunas[i], [field]: value };
    onChange({ ...data, colunas });
  };

  const generateSuggestions = async () => {
    if (!user?.token) return;
    setIsGenerating(true);

    try {
      const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/dicionario/sugerir`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${user.token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          tabela: tabelaOrigem || "TABELA_DESCONHECIDA",
          colunas: columnNames
        })
      });

      if (response.ok) {
        const resData = await response.json();

        // Merge AI suggestions with the current state appropriately
        const aiDescTabela = resData.descricaoTabela || "";
        const aiColDesc = resData.colunas || [];

        const newColunas = data.colunas.map((col) => {
          const aiMatch = aiColDesc.find((aiCol: any) => aiCol.nome === col.coluna);
          return aiMatch ? { ...col, descricao: aiMatch.descricao } : col;
        });

        // Use AI suggestion for table description if the current one is empty
        onChange({
          ...data,
          descricaoTabela: data.descricaoTabela || aiDescTabela,
          colunas: newColunas
        });
      }
    } catch (err) {
      console.error("Error generating dictionaries:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Criando nova ingestão de dados</h2>
        <p className="text-sm text-muted-foreground">Defina a dicionarização de {tabelaOrigem}</p>
      </div>

      <div className="space-y-4">

        <div className="flex justify-end">
          <Button
            variant="outline"
            onClick={generateSuggestions}
            disabled={isGenerating}
            className="flex items-center gap-2 border-primary/50 hover:bg-primary/10"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            {isGenerating ? "Gerando Sugestões..." : "Melhorar Descrições com IA"}
          </Button>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Descrição Tabela
          </label>
          <Input
            placeholder="Digite a descrição da tabela..."
            value={data.descricaoTabela}
            onChange={(e) => onChange({ ...data, descricaoTabela: e.target.value })}
            disabled={isGenerating}
          />
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
            <span>Coluna</span>
            <span>Descrição</span>
          </div>
          {data.colunas.map((col, i) => (
            <div key={i} className="grid grid-cols-2 gap-4 items-center">
              <Input value={col.coluna} readOnly className="bg-muted font-mono text-sm" />
              <Input
                placeholder="Descrição clara e de negócios da coluna"
                value={col.descricao}
                onChange={(e) => updateCol(i, "descricao", e.target.value)}
                disabled={isGenerating}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-4 pt-4">
        {onBack && <Button variant="outline" className="w-1/3 border-primary/50 hover:bg-primary/10" onClick={onBack}>Voltar</Button>}
        <Button className="flex-1" size="lg" onClick={onNext} disabled={isGenerating}>Continue</Button>
      </div>
    </div>
  );
};

export default StepDicionarizacao;
