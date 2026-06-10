import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Activity, Boxes, BrainCircuit, GitCompareArrows, LayoutDashboard, LogOut, Menu, PanelLeftClose, ServerCog, Settings, ShieldCheck, UserCog, WandSparkles, Workflow } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { BACKEND_ORIGIN, BACKEND_START_COMMAND } from '../services/api/config';
import { roleLabels, type PermissionCode, type RoleCode } from '../types/domain';
import { IconButton, InlineError, LoadingBlock, StatusBadge } from './ui';
import { getLandingPathForRole } from '../utils/roleRoutes';

interface NavItem {
  path: string;
  label: string;
  icon: React.ElementType;
  permission: PermissionCode;
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: '工作台', icon: LayoutDashboard, permission: 'dashboard:view' },
  { path: '/projects', label: '项目场景', icon: Boxes, permission: 'project:read' },
  { path: '/tasks', label: '任务编排', icon: Workflow, permission: 'task:dispatch' },
  { path: '/multimodal', label: '智能交互', icon: BrainCircuit, permission: 'multimodal:execute' },
  { path: '/simulation', label: '仿真分析', icon: Activity, permission: 'simulation:run' },
  { path: '/audit', label: '审计版本', icon: GitCompareArrows, permission: 'audit:read' },
  { path: '/settings', label: '系统设置', icon: Settings, permission: 'settings:write' },
];

const roleNavItems: Record<RoleCode, NavItem[]> = {
  modeler: [
    { path: '/modeler', label: '建模师门户', icon: WandSparkles, permission: 'project:read' },
    ...navItems.filter((item) => ['project:read', 'task:dispatch', 'multimodal:execute', 'audit:read'].includes(item.permission)),
  ],
  analyst: [
    { path: '/analyst', label: '分析师门户', icon: Activity, permission: 'simulation:run' },
    ...navItems.filter((item) => ['simulation:run', 'multimodal:execute', 'task:dispatch', 'project:read', 'audit:read'].includes(item.permission)),
  ],
  admin: [
    { path: '/admin', label: '管理员门户', icon: UserCog, permission: 'settings:write' },
    ...navItems.filter((item) => ['audit:read', 'settings:write', 'project:read', 'task:dispatch', 'simulation:run'].includes(item.permission)),
  ],
};

export function AppLayout() {
  const { session, logout, hasPermission, switchDemoRole } = useSession();
  const {
    projects,
    scenes,
    selectedProjectId,
    selectedSceneId,
    selectedProject,
    selectedScene,
    setSelectedProjectId,
    setSelectedSceneId,
    isLoading,
    error,
    clearError,
    health,
  } = useWorkspace();
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const activeRole = session?.user.role ?? 'modeler';
  const availableNav = useMemo(
    () => roleNavItems[activeRole].filter((item) => hasPermission(item.permission)),
    [activeRole, hasPermission],
  );
  const projectScenes = scenes.filter((scene) => scene.projectId === selectedProjectId);
  const isSettingsRoute = location.pathname.includes('/settings');

  return (
    <div className={`app-shell ${isSidebarOpen ? '' : 'sidebar-collapsed'}`}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SC</div>
          <div>
            <strong>智能城市生成系统</strong>
            <span>控制平面前端</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="主导航">
          {availableNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.path} to={item.path} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <div className="health-mini">
            {health.slice(0, 3).map((item) => (
              <span key={item.id} title={`${item.name} ${item.successRate}%`}>
                <i className={`dot dot-${item.status}`} />
                {item.name}
              </span>
            ))}
          </div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <IconButton label={isSidebarOpen ? '收起导航' : '展开导航'} onClick={() => setSidebarOpen((value) => !value)}>
              {isSidebarOpen ? <PanelLeftClose size={18} /> : <Menu size={18} />}
            </IconButton>
            <div className="context-selectors">
              <label>
                <span>当前项目</span>
                <select value={selectedProjectId ?? ''} onChange={(event) => setSelectedProjectId(event.target.value)}>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>当前场景</span>
                <select value={selectedSceneId ?? ''} onChange={(event) => setSelectedSceneId(event.target.value)}>
                  {projectScenes.map((scene) => (
                    <option key={scene.id} value={scene.id}>
                      {scene.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>
          <div className="topbar-right">
            {selectedProject ? <StatusBadge status={selectedProject.status} /> : null}
            {selectedScene ? <span className="version-pill">{selectedScene.version}</span> : null}
            <div className="user-menu">
              <div>
                <strong>{session?.user.name}</strong>
                <span>{session ? roleLabels[session.user.role] : ''}</span>
              </div>
              <select
                value={session?.user.role}
                onChange={(event) => {
                  const nextRole = event.target.value as RoleCode;
                  void switchDemoRole(nextRole).then(() => navigate(getLandingPathForRole(nextRole)));
                }}
                title="切换演示角色"
              >
                <option value="modeler">建模师</option>
                <option value="analyst">分析师</option>
                <option value="admin">管理员</option>
              </select>
              <IconButton
                label="退出登录"
                onClick={() => {
                  logout();
                  navigate('/login');
                }}
              >
                <LogOut size={18} />
              </IconButton>
            </div>
          </div>
        </header>

        <div className="workspace-ribbon">
          <span>
            <ShieldCheck size={16} />
            RBAC 已装配：{session ? roleLabels[session.user.role] : '未登录'}
          </span>
          <span>
            <ServerCog size={16} />
            后端服务：{BACKEND_ORIGIN}
          </span>
          <span className={isSettingsRoute ? 'ribbon-focus' : ''} title={BACKEND_START_COMMAND}>
            默认连接真实后端
          </span>
        </div>

        <main className="content">
          {error ? <InlineError message={error} onDismiss={clearError} /> : null}
          {isLoading && projects.length === 0 ? (
            <LoadingBlock label="正在从后端加载工作区数据" />
          ) : (
            <Outlet />
          )}
        </main>
      </div>
    </div>
  );
}
