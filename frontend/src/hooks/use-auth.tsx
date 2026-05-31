import { createContext, useContext, useState, useEffect, ReactNode } from "react";

// ── Tipos ─────────────────────────────────────────────────────────────────────
interface AuthUser {
    username: string;
    token: string;
}

interface AuthContextType {
    user: AuthUser | null;
    login: (username: string, password: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
}

// ── Configuração ───────────────────────────────────────────────────────────────
const AUTH_SERVICE_URL = (import.meta as any).env.VITE_AUTH_SERVICE_URL ?? "http://localhost:8000";
const STORAGE_KEY = "auth_user";

// ── Context ───────────────────────────────────────────────────────────────────
const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? (JSON.parse(stored) as AuthUser) : null;
        } catch {
            return null;
        }
    });

    // Persiste no localStorage sempre que o usuário muda
    useEffect(() => {
        if (user) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
        } else {
            localStorage.removeItem(STORAGE_KEY);
        }
    }, [user]);

    async function login(username: string, password: string): Promise<void> {
        const res = await fetch(`${AUTH_SERVICE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw new Error(body?.detail ?? "Credenciais inválidas");
        }

        const data = await res.json();
        setUser({ username: data.user, token: data.token });
    }

    function logout() {
        setUser(null);
    }

    return (
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
            {children}
        </AuthContext.Provider>
    );
}

// ── Hook público ───────────────────────────────────────────────────────────────
export function useAuth(): AuthContextType {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
    return ctx;
}
