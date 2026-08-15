import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface StepRevisaoProps {
  formData: any;
  onSubmit: () => void;
  onBack?: () => void;
}

const StepRevisao = ({ formData, onSubmit, onBack }: StepRevisaoProps) => {
  const { sigla, fonte, metadados, colunas, dicionarizacao, qualidade } = formData;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-foreground">Criando nova ingestão de dados</h2>
        <p className="text-sm text-muted-foreground">Revise todos os dados antes de enviar</p>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Sigla</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{sigla.sigla || "-"}</div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Nome Tabela (Destino)</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{metadados.nomeTabela || "-"}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Sistema Origem</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{fonte.sistemaOrigem || "-"}</div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Formato Origem</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{fonte.formatoArquivo || "-"}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Periodicidade</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{metadados.periodicidade || "-"}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Horário</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{metadados.horario || "-"}</div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Coluna de partição</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{colunas.colunaParticao || "-"}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Tipo Atualização</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{metadados.atualizacao || "-"}</div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Data Criação</label>
            <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{metadados.dataCriacao || "-"}</div>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Descrição da Tabela</label>
          <div className="text-sm p-3 bg-muted rounded-md border min-h-[60px] break-words whitespace-pre-wrap">{dicionarizacao.descricaoTabela || "Nenhuma descrição"}</div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Uso (Usage)</label>
            <div className="text-sm p-3 bg-muted rounded-md border min-h-[60px] break-words whitespace-pre-wrap">{metadados.usage || "Não informado"}</div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Limitações</label>
            <div className="text-sm p-3 bg-muted rounded-md border min-h-[60px] break-words whitespace-pre-wrap">{metadados.limitacoes || "Não informado"}</div>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Classificação de Segurança</label>
          <div className="text-sm p-2.5 bg-muted rounded-md border min-h-[40px] flex items-center">{metadados.classificacaoSeguranca || "Internal"}</div>
        </div>

        {colunas.colunas.length > 0 && (
          <div className="space-y-3 pt-4 border-t">
            <h3 className="text-sm font-semibold text-foreground">Definição das Colunas</h3>
            <div className="grid grid-cols-5 gap-3 text-xs font-medium text-muted-foreground">
              <span>Colunas</span>
              <span>Descrição</span>
              <span>PII</span>
              <span>Tipo PII</span>
              <span>Regras de Qualidade de Dados</span>
            </div>
            {colunas.colunas.filter((c: any) => c.nome).map((col: any, i: number) => (
              <div key={i} className="grid grid-cols-5 gap-3">
                <div className="text-xs p-2 bg-muted rounded-md border flex items-center break-all">
                  {col.nome}({col.dataType}){col.chavePrimaria === 'Sim' ? '_PK' : ''}
                </div>
                <div className="text-xs p-2 bg-muted rounded-md border break-words">
                  {dicionarizacao.colunas[i]?.descricao || "-"}
                </div>
                <div className="text-xs p-2 bg-muted rounded-md border flex items-center break-words">
                  {col.pii === 'Sim' ? 'SIM' : 'NÃO'}
                </div>
                <div className="text-xs p-2 bg-muted rounded-md border flex items-center break-words">
                  {col.piiType || "-"}
                </div>
                <div className="text-xs p-2 bg-muted rounded-md border flex break-words">
                  {qualidade.colunas[i]?.regras?.join(", ") || "-"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-4 pt-4">
        {onBack && <Button variant="outline" className="w-1/3 border-primary/50 hover:bg-primary/10" onClick={onBack}>Voltar e Editar</Button>}
        <Button className="flex-1" size="lg" onClick={onSubmit}>ENVIAR</Button>
      </div>
    </div>
  );
};

export default StepRevisao;
