import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";

/**
 * Envolve rotas que exigem autenticação.
 * Redireciona para /login se o usuário não estiver logado.
 */
export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated } = useAuth();
    return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}
