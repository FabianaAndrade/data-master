import { useState, useEffect } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "../../hooks/use-auth";

interface StepFonteProps {
  data: { sistemaOrigem: string; formatoArquivo: string };
  onChange: (data: StepFonteProps["data"]) => void;
  onNext: () => void;
  onBack?: () => void;
}

interface Option {
  value: string;
  label: string;
}

const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

const StepFonte = ({ data, onChange, onNext, onBack }: StepFonteProps) => {
  const { user } = useAuth();
  const [fontes, setFontes] = useState<Option[]>([]);
  const [formatos, setFormatos] = useState<Option[]>([]);
  const [isLoadingFontes, setIsLoadingFontes] = useState(false);
  const [isLoadingFormatos, setIsLoadingFormatos] = useState(false);

  useEffect(() => {
    async function fetchFontes() {
      if (!user?.token) return;
      setIsLoadingFontes(true);
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/fontes`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (response.ok) {
          const resData = await response.json();
          setFontes(resData.fontes || []);
        }
      } catch (error) {
        console.error("Error fetching fontes:", error);
      } finally {
        setIsLoadingFontes(false);
      }
    }
    fetchFontes();
  }, [user]);


  useEffect(() => {
    async function fetchFormatos() {
      if (!user?.token || !data.sistemaOrigem) {
        setFormatos([]);
        return;
      }
      setIsLoadingFormatos(true);
      try {
        const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/tabelas/formato/${data.sistemaOrigem}`, {
          headers: { Authorization: `Bearer ${user.token}` },
        });
        if (response.ok) {
          const resData = await response.json();
          setFormatos(resData.opcoes || []);
        }
      } catch (error) {
        console.error("Error fetching formatos:", error);
      } finally {
        setIsLoadingFormatos(false);
      }
    }
    fetchFormatos();
  }, [user, data.sistemaOrigem]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Criando nova ingestão de dados</h2>
        <p className="text-sm text-muted-foreground">Defina a fonte dos dados</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Sistema Origem</label>
          <Select
            value={data.sistemaOrigem}
            onValueChange={(v) => onChange({ ...data, sistemaOrigem: v })}
          >
            <SelectTrigger disabled={isLoadingFontes}>
              <SelectValue placeholder={isLoadingFontes ? "Carregando..." : "Selecione o sistema"} />
            </SelectTrigger>
            <SelectContent>
              {fontes.map((fonte) => (
                <SelectItem key={fonte.value} value={fonte.value}>{fonte.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>



        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Formato arquivo origem</label>
          <Select
            value={data.formatoArquivo}
            onValueChange={(v) => onChange({ ...data, formatoArquivo: v })}
            disabled={!data.sistemaOrigem || isLoadingFormatos}
          >
            <SelectTrigger>
              <SelectValue placeholder={isLoadingFormatos ? "Carregando..." : (!data.sistemaOrigem ? "Selecione a origem primeiro" : "Selecione o formato")} />
            </SelectTrigger>
            <SelectContent>
              {formatos.map((formato) => (
                <SelectItem key={formato.value} value={formato.value}>{formato.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>


      </div>

      <div className="flex gap-4 pt-4">
        {onBack && <Button variant="outline" className="w-1/3 border-primary/50 hover:bg-primary/10" onClick={onBack}>Voltar</Button>}
        <Button className="flex-1" size="lg" onClick={onNext} disabled={!data.sistemaOrigem}>Continue</Button>
      </div>
    </div>
  );
};

export default StepFonte;
