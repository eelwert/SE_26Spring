import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { useSession } from './context/SessionContext';
import { AdminPortalPage } from './pages/AdminPortalPage';
import { AuditPage } from './pages/AuditPage';
import { AnalystPortalPage } from './pages/AnalystPortalPage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { ModelerPortalPage } from './pages/ModelerPortalPage';
import { MultimodalPage } from './pages/MultimodalPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SimulationPage } from './pages/SimulationPage';
import { TasksPage } from './pages/TasksPage';
import { LoadingBlock } from './components/ui';
import type { PermissionCode, RoleCode } from './types/domain';
import { getLandingPathForRole } from './utils/roleRoutes';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isRestoring } = useSession();
  if (isRestoring) {
    return <LoadingBlock label="正在恢复会话" />;
  }
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function RoleRoute({ allowedRole, children }: { allowedRole: RoleCode; children: React.ReactNode }) {
  const { session, isAuthenticated, isRestoring } = useSession();
  if (isRestoring) {
    return <LoadingBlock label="正在检查角色权限" />;
  }
  if (!isAuthenticated || !session) {
    return <Navigate to="/login" replace />;
  }
  if (session.user.role !== allowedRole) {
    return <Navigate to={getLandingPathForRole(session.user.role)} replace />;
  }
  return <>{children}</>;
}

function PermissionRoute({ permission, children }: { permission: PermissionCode; children: React.ReactNode }) {
  const { session, isAuthenticated, isRestoring, hasPermission } = useSession();
  if (isRestoring) {
    return <LoadingBlock label="正在检查访问权限" />;
  }
  if (!isAuthenticated || !session) {
    return <Navigate to="/login" replace />;
  }
  if (!hasPermission(permission)) {
    return <Navigate to={getLandingPathForRole(session.user.role)} replace />;
  }
  return <>{children}</>;
}

function RoleAwareLanding() {
  const { session } = useSession();
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  return <Navigate to={getLandingPathForRole(session.user.role)} replace />;
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
        <Route
          path="/modeler"
          element={
            <RoleRoute allowedRole={"modeler"}>
              <ModelerPortalPage />
            </RoleRoute>
          }
        />
        <Route
          path="/analyst"
          element={
            <RoleRoute allowedRole={"analyst"}>
              <AnalystPortalPage />
            </RoleRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <RoleRoute allowedRole={"admin"}>
              <AdminPortalPage />
            </RoleRoute>
          }
        />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route
          path="/projects"
          element={
            <PermissionRoute permission="project:read">
              <ProjectsPage />
            </PermissionRoute>
          }
        />
        <Route
          path="/tasks"
          element={
            <PermissionRoute permission="task:dispatch">
              <TasksPage />
            </PermissionRoute>
          }
        />
        <Route
          path="/multimodal"
          element={
            <PermissionRoute permission="multimodal:execute">
              <MultimodalPage />
            </PermissionRoute>
          }
        />
        <Route
          path="/simulation"
          element={
            <PermissionRoute permission="simulation:run">
              <SimulationPage />
            </PermissionRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <PermissionRoute permission="audit:read">
              <AuditPage />
            </PermissionRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <PermissionRoute permission="settings:write">
              <SettingsPage />
            </PermissionRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
