import { useState, useEffect } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../../hooks/use-auth";

interface ColumnDef {
  nome: string;
  dataType: string;
  chavePrimaria: string;
  pii: string;
  piiType: string;
}

interface StepColunasProps {
  data: { numColunas: string; colunas: ColumnDef[]; colunaParticao: string };
  tabelaOrigem?: string;
  incluirDataRef?: boolean;
  onChange: (data: StepColunasProps["data"]) => void;
  onNext: () => void;
  onBack?: () => void;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const StepColunas = ({ data, tabelaOrigem, incluirDataRef, onChange, onNext, onBack }: StepColunasProps) => {
  const { user } = useAuth();
  const numCols = parseInt(data.numColunas) || 3;
  const [opcoes, setOpcoes] = useState({
    dataTypes: ["STRING", "INTEGER", "DATE", "FLOAT", "BOOLEAN"],
    chavePrimaria: ["Sim", "Não"],
    pii: ["Sim", "Não"],
    piiTypes: ["N/A", "CPF", "CNPJ", "Email", "Nome"]
  });
  const [opcoesParticao, setOpcoesParticao] = useState<string[]>(["Nenhuma"]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function fetchColunas() {
      const targetTabela = tabelaOrigem || "default";
      if (!user?.token) return;

      setIsLoading(true);
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/colunas/${targetTabela}`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });

        if (response.ok) {
          const resData = await response.json();
          if (resData.opcoes) setOpcoes(resData.opcoes);

          // Apenas auto-preenche se as colunas vieram da API
          if (resData.colunas && resData.colunas.length > 0 && data.colunas.every(c => !c.nome)) {
            onChange({
              ...data,
              numColunas: String(resData.colunas.length),
              colunas: resData.colunas
            });
          }
        }
      } catch (error) {
        console.error("Error fetching colunas:", error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchColunas();
  }, [tabelaOrigem, user]);

  const baseColNames = data.colunas.slice(0, numCols).map((c) => c.nome).filter(Boolean);
  if (incluirDataRef) {
    baseColNames.push("dat_ref_carga");
  }
  const colNamesString = baseColNames.join(",");

  useEffect(() => {
    if (!colNamesString) {
      setOpcoesParticao(["Nenhuma"]);
      return;
    }
    async function fetchParticao() {
      try {
          const targetTabela = tabelaOrigem || "default";
          const res = await fetch(`${INGESTION_SERVICE_URL}/ingestion/coluna/particao/${targetTabela}`, {
            method: "POST",
            headers: { 
              "Content-Type": "application/json",
              Authorization: `Bearer ${user?.token || ""}`
            },
            body: JSON.stringify({ tabela: targetTabela, colunas: colNamesString.split(",") })
          });
          if (res.ok) {
            const resData = await res.json();
            if (resData.opcoes?.colunas) {
              setOpcoesParticao(resData.opcoes.colunas);
            }
          }
      } catch (error) {
        console.error(error);
      }
    }
    
    // Add small debounce
    const timer = setTimeout(fetchParticao, 500);
    return () => clearTimeout(timer);
  }, [colNamesString, tabelaOrigem, user]);

  const handleNumChange = (v: string) => {
    const n = parseInt(v) || 3;
    const colunas = [...data.colunas];
    while (colunas.length < n) colunas.push({ nome: "", dataType: "", chavePrimaria: "", pii: "", piiType: "" });
    onChange({ ...data, numColunas: v, colunas: colunas.slice(0, n) });
  };

  const updateCol = (i: number, field: keyof ColumnDef, value: string) => {
    const colunas = [...data.colunas];
    colunas[i] = { ...colunas[i], [field]: value };
    // Se PII for Não, garante que Type reseta
    if (field === "pii" && value === "Não") colunas[i].piiType = "N/A";
    onChange({ ...data, colunas });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Criando nova ingestão de dados</h2>
        <p className="text-sm text-muted-foreground">Defina os metadados das colunas da tabela {tabelaOrigem}</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Número de colunas</label>
          <Input 
            type="number" 
            min="1" 
            max="100" 
            value={data.numColunas} 
            onChange={(e) => handleNumChange(e.target.value)} 
            disabled={isLoading} 
          />
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-5 gap-2 text-xs font-medium text-muted-foreground">
            <span>Colunas</span>
            <span>Data Type</span>
            <span>Chave primária</span>
            <span>PII</span>
            <span>Tipo PII</span>
          </div>
          {data.colunas.slice(0, numCols).map((col, i) => (
            <div key={i} className="grid grid-cols-5 gap-2">
              <Input placeholder="Nome da coluna" value={col.nome} onChange={(e) => updateCol(i, "nome", e.target.value.replace(/[^a-zA-Z0-9_]/g, ''))} disabled={isLoading} />

              <Select value={col.dataType} onValueChange={(v) => updateCol(i, "dataType", v)}>
                <SelectTrigger disabled={isLoading}><SelectValue /></SelectTrigger>
                <SelectContent>
                  {opcoes.dataTypes.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                </SelectContent>
              </Select>

              <Select value={col.chavePrimaria} onValueChange={(v) => updateCol(i, "chavePrimaria", v)}>
                <SelectTrigger disabled={isLoading}><SelectValue /></SelectTrigger>
                <SelectContent>
                  {opcoes.chavePrimaria.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                </SelectContent>
              </Select>

              <Select value={col.pii} onValueChange={(v) => updateCol(i, "pii", v)}>
                <SelectTrigger disabled={isLoading}><SelectValue /></SelectTrigger>
                <SelectContent>
                  {opcoes.pii.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                </SelectContent>
              </Select>

              <Select value={col.piiType} onValueChange={(v) => updateCol(i, "piiType", v)} disabled={col.pii === "Não" || isLoading}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {opcoes.piiTypes.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          ))}
          
          {incluirDataRef && (
            <div className="grid grid-cols-5 gap-2 opacity-70">
              <Input placeholder="Nome da coluna" value="dat_ref_carga" disabled />
              <Select value="DATE" disabled><SelectTrigger disabled><SelectValue /></SelectTrigger></Select>
              <Select value="Não" disabled><SelectTrigger disabled><SelectValue /></SelectTrigger></Select>
              <Select value="Não" disabled><SelectTrigger disabled><SelectValue /></SelectTrigger></Select>
              <Select value="N/A" disabled><SelectTrigger disabled><SelectValue /></SelectTrigger></Select>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Coluna de partição</label>
          <Select value={data.colunaParticao} onValueChange={(v) => onChange({ ...data, colunaParticao: v })}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {opcoesParticao.map((opt) => (
                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex gap-4 pt-4">
        {onBack && <Button variant="outline" className="w-1/3 border-primary/50 hover:bg-primary/10" onClick={onBack}>Voltar</Button>}
        <Button className="flex-1" size="lg" onClick={onNext} disabled={isLoading || data.colunas.some((c, index) => index < numCols && !c.nome)}>Continue</Button>
      </div>
    </div>
  );
};

export default StepColunas;
