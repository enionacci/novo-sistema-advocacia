// src/App.js
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { CssBaseline } from '@mui/material';
import { useAuth } from './context/AuthContext';

// Components
import PrivateRoute from './components/PrivateRoute';
import AuthenticatedRoute from './components/AuthenticatedRoute';
import Layout from './components/Layout';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CreateOfficePage from './pages/CreateOfficePage';
import AcceptInvitationPage from './pages/AcceptInvitationPage';
import ClientListPage from './pages/ClientListPage';
import ClientCreatePage from './pages/ClientCreatePage';
import ClientEditPage from './pages/ClientEditPage';
import ClientDetailPage from './pages/ClientDetailPage';
import NewConsultationPage from './pages/NewConsultationPage';
import EscritorioPage from './pages/EscritorioPage';
import AuditLogListPage from './pages/AuditLogListPage';
import AuditLogDetailPage from './pages/AuditLogDetailPage';
import AuditLogStatsPage from './pages/AuditLogStatsPage';
import DocumentosPage from './pages/DocumentosPage';
import ScannerPage from './pages/ScannerPage';
import AnalysesPage from './pages/AnalysesPage';
import AnonymizePage from './pages/AnonymizePage';
import AIAnalysisPage from './pages/AIAnalysisPage';
import FerramentasPDFPage from './pages/FerramentasPDFPage';
import ProcessosListPage from './pages/ProcessosListPage';
import ProcessoCreatePage from './pages/ProcessoCreatePage';
import ProcessoDetailPage from './pages/ProcessoDetailPage';
import ProcessoEditPage from './pages/ProcessoEditPage';

function App() {
  const { user } = useAuth();

  return (
    <>
      <CssBaseline />
      <Routes>
        {/* Rotas públicas (sem layout) */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/convite/:token" element={<AcceptInvitationPage />} />
        <Route 
          path="/criar-escritorio" 
          element={
            <AuthenticatedRoute>
              <CreateOfficePage />
            </AuthenticatedRoute>
          } 
        />

        {/* Rotas privadas (com layout) */}
        <Route
          path="/*"
          element={
            user ? (
              <Layout>
                <Routes>
                  <Route 
                    path="/" 
                    element={
                      <PrivateRoute>
                        <ClientListPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/clientes/novo" 
                    element={
                      <PrivateRoute>
                        <ClientCreatePage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/clientes/:clientId/edit" 
                    element={
                      <PrivateRoute>
                        <ClientEditPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/clientes/:clientId/nova-consulta" 
                    element={
                      <PrivateRoute>
                        <NewConsultationPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/clientes/:clientId" 
                    element={
                      <PrivateRoute>
                        <ClientDetailPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/meu-escritorio" 
                    element={
                      <PrivateRoute>
                        <EscritorioPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/audit-logs" 
                    element={
                      <PrivateRoute>
                        <AuditLogListPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/audit-logs/stats" 
                    element={
                      <PrivateRoute>
                        <AuditLogStatsPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/audit-logs/:id" 
                    element={
                      <PrivateRoute>
                        <AuditLogDetailPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/scanner" 
                    element={
                      <PrivateRoute>
                        <ScannerPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/anonimizar" 
                    element={
                      <PrivateRoute>
                        <AnonymizePage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/analise-ia" 
                    element={
                      <PrivateRoute>
                        <AIAnalysisPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/documentos" 
                    element={
                      <PrivateRoute>
                        <DocumentosPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/analises" 
                    element={
                      <PrivateRoute>
                        <AnalysesPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route
                    path="/ferramentas-pdf"
                    element={
                      <PrivateRoute>
                        <FerramentasPDFPage />
                      </PrivateRoute>
                    }
                  />
                  <Route
                    path="/processos"
                    element={
                      <PrivateRoute>
                        <ProcessosListPage />
                      </PrivateRoute>
                    }
                  />
                  <Route 
                    path="/processos/novo" 
                    element={
                      <PrivateRoute>
                        <ProcessoCreatePage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/processos/:id" 
                    element={
                      <PrivateRoute>
                        <ProcessoDetailPage />
                      </PrivateRoute>
                    } 
                  />
                  <Route 
                    path="/processos/:id/editar" 
                    element={
                      <PrivateRoute>
                        <ProcessoEditPage />
                      </PrivateRoute>
                    } 
                  />
                </Routes>
              </Layout>
            ) : null
          }
        />
      </Routes>
    </>
  );
}

export default App;