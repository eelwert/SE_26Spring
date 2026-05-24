import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { useSession } from './context/SessionContext';
import { AuditPage } from './pages/AuditPage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { MultimodalPage } from './pages/MultimodalPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SimulationPage } from './pages/SimulationPage';
import { TasksPage } from './pages/TasksPage';
import { LoadingBlock } from './components/ui';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isRestoring } = useSession();
  if (isRestoring) {
    return <LoadingBlock label="正在恢复会话" />;
  }
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function RoleAwareLanding() {
  const { session } = useSession();
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  if (session.user.role === 'analyst') {
    return <Navigate to="/simulation" replace />;
  }
  if (session.user.role === 'admin') {
    return <Navigate to="/audit" replace />;
  }
  return <Navigate to="/dashboard" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<RoleAwareLanding />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="tasks" element={<TasksPage />} />
        <Route path="multimodal" element={<MultimodalPage />} />
        <Route path="simulation" element={<SimulationPage />} />
        <Route path="audit" element={<AuditPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
