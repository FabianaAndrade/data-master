import { useState, useEffect } from "react";
import { useAuth } from "./use-auth";

interface Sigla {
    id: string; // example: "FINS - Financeiro"
    owner: string;
}

export function useIngestion() {
    const { user } = useAuth();
    const [siglas, setSiglas] = useState<Sigla[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const INGESTION_SERVICE_URL = (import.meta as any).env.VITE_INGESTION_SERVICE_URL ?? "http://localhost:8001";

    useEffect(() => {
        let isMounted = true;

        async function fetchSiglas() {
            if (!user?.token) return;

            setIsLoading(true);
            setError(null);
            try {
                const response = await fetch(`${INGESTION_SERVICE_URL}/ingestion/siglas`, {
                    headers: {
                        "Authorization": `Bearer ${user.token}`,
                    },
                });

                if (response.status === 401) {
                    localStorage.removeItem("auth_user");
                    window.location.href = "/login";
                    return;
                }

                if (!response.ok) {
                    throw new Error("Failed to fetch siglas");
                }

                const data = await response.json();
                if (isMounted) {
                    setSiglas(data.siglas || []);
                }
            } catch (err: any) {
                if (isMounted) {
                    setError(err.message || "An error occurred while fetching siglas.");
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        fetchSiglas();

        return () => {
            isMounted = false;
        };
    }, [user, INGESTION_SERVICE_URL]);

    return { siglas, isLoading, error };
}
