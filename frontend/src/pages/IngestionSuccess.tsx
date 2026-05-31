import { useParams, Link } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";

const IngestionSuccess = () => {
  const { id } = useParams();

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <h1 className="text-2xl font-bold text-foreground mb-4">
          Ingestão #{id} Criada com sucesso!
        </h1>
        <p className="text-muted-foreground mb-6">Acompanhe o status na aba</p>
        <Button asChild>
          <Link to="/ingestions">Minhas Ingestões</Link>
        </Button>
      </div>
    </div>
  );
};

export default IngestionSuccess;
