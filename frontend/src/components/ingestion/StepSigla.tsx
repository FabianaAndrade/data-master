import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useIngestion } from "@/hooks/user-ingestion";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";

interface StepSiglaProps {
  data: { sigla: string; gestorAprovador: string };
  onChange: (data: { sigla: string; gestorAprovador: string }) => void;
  onNext: () => void;
}

const StepSigla = ({ data, onChange, onNext }: StepSiglaProps) => {
  const { siglas, isLoading, error } = useIngestion();

  // Handle auto-updating the owner if the data.sigla changes programmatically or if the list loads
  useEffect(() => {
    if (data.sigla && siglas.length > 0) {
      const selected = siglas.find((s) => s.id === data.sigla);
      if (selected && data.gestorAprovador !== selected.owner) {
        onChange({ ...data, gestorAprovador: selected.owner });
      }
    }
  }, [data.sigla, siglas, data.gestorAprovador, onChange]);

  const handleSiglaChange = (value: string) => {
    const selected = siglas.find((s) => s.id === value);
    if (selected) {
      onChange({ sigla: selected.id, gestorAprovador: selected.owner });
    } else {
      onChange({ ...data, sigla: value });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Criando nova ingestão de dados</h2>
        <p className="text-sm text-muted-foreground">Defina sua sigla</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Sigla</label>
          <Select 
            value={data.sigla} 
            onValueChange={handleSiglaChange}
            disabled={isLoading}
          >
            <SelectTrigger>
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  <span className="text-muted-foreground text-sm">Carregando siglas...</span>
                </div>
              ) : (
                <SelectValue placeholder="Selecione a sigla associada ao seu perfil" />
              )}
            </SelectTrigger>
            <SelectContent>
              {error ? (
                <div className="p-2 text-sm text-destructive">Erro ao carregar siglas.</div>
              ) : siglas.length === 0 && !isLoading ? (
                <div className="p-2 text-sm text-muted-foreground">Nenhuma sigla encontrada.</div>
              ) : (
                siglas.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.id}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Gestor Aprovador</label>
          <Input
            placeholder="Aguardando seleção..."
            value={data.gestorAprovador}
            disabled
            className="bg-muted/50 cursor-not-allowed"
          />
          <p className="text-xs text-muted-foreground mt-1">Este campo é preenchido automaticamente de acordo com o diretório LDAP da sigla escolhida.</p>
        </div>
      </div>

      <Button className="w-full" size="lg" onClick={onNext} disabled={!data.sigla || isLoading}>
        Continue
      </Button>
    </div>
  );
};

export default StepSigla;
