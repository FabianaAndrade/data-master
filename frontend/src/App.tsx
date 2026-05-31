import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/hooks/use-auth";
import ProtectedRoute from "@/components/ProtectedRoute";
import Index from "./pages/Index";
import Login from "./pages/Login";
import CreateIngestion from "./pages/CreateIngestion";
import IngestionSuccess from "./pages/IngestionSuccess";
import IngestionHistory from "./pages/IngestionHistory";
import IngestionDetail from "./pages/IngestionDetail";
import ApproveIngestion from "./pages/ApproveIngestion";
import DeleteTable from "./pages/DeleteTable";
import DeleteSuccess from "./pages/DeleteSuccess";
import EditTable from "./pages/EditTable";
import MyAccount from "./pages/MyAccount";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><Index /></ProtectedRoute>} />
            <Route path="/create-ingestion" element={<ProtectedRoute><CreateIngestion /></ProtectedRoute>} />
            <Route path="/ingestion-success/:id" element={<ProtectedRoute><IngestionSuccess /></ProtectedRoute>} />
            <Route path="/ingestions" element={<ProtectedRoute><IngestionHistory /></ProtectedRoute>} />
            <Route path="/ingestion-detail/:id" element={<ProtectedRoute><IngestionDetail /></ProtectedRoute>} />
            <Route path="/approve-ingestion" element={<ProtectedRoute><ApproveIngestion /></ProtectedRoute>} />
            <Route path="/delete-table" element={<ProtectedRoute><DeleteTable /></ProtectedRoute>} />
            <Route path="/delete-success/:id" element={<ProtectedRoute><DeleteSuccess /></ProtectedRoute>} />
            <Route path="/edit-table" element={<ProtectedRoute><EditTable /></ProtectedRoute>} />
            <Route path="/alerts" element={<ProtectedRoute><Index /></ProtectedRoute>} />
            <Route path="/resources" element={<ProtectedRoute><Index /></ProtectedRoute>} />
            <Route path="/account" element={<ProtectedRoute><MyAccount /></ProtectedRoute>} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
