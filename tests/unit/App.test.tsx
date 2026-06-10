import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import { SessionProvider } from '../../src/context/SessionContext';
import { WorkspaceProvider } from '../../src/context/WorkspaceContext';
import type { LoginRequest, RoleCode, User, WorkspaceBundle } from '../../src/types/domain';

const permissionsByRole: Record<RoleCode, User['permissions']> = {
  modeler: [
    'dashboard:view',
    'project:read',
    'project:write',
    'asset:replace',
    'layout:edit',
    'task:dispatch',
    'multimodal:execute',
    'audit:read',
  ],
  analyst: ['dashboard:view', 'project:read', 'task:dispatch', 'multimodal:execute', 'simulation:run', 'audit:read'],
  admin: [
    'dashboard:view',
    'project:read',
    'project:write',
    'asset:replace',
    'layout:edit',
    'task:dispatch',
    'multimodal:execute',
    'simulation:run',
    'audit:read',
    'version:rollback',
    'settings:write',
  ],
};

const namesByRole: Record<RoleCode, string> = {
  modeler: '林知远',
  analyst: '沈迭青',
  admin: '陈明策',
};

const departmentsByRole: Record<RoleCode, string> = {
  modeler: '场景建模组',
  analyst: '城市仿真分析组',
  admin: '平台治理与运维',
};

const makeUser = (role: RoleCode): User => ({
  id: `usr-${role}`,
  name: namesByRole[role],
  email: `${role}@nku.city`,
  role,
  department: departmentsByRole[role],
  permissions: permissionsByRole[role],
});

const demoUsers = (['modeler', 'analyst', 'admin'] as RoleCode[]).map(makeUser);

const pluginReviews = [
  {
    id: 'review-dispatch-blender-job',
    functionName: 'dispatch_blender_job',
    title: 'Blender 插件下发',
    risk: 'high' as const,
    status: 'pending' as const,
    requestedBy: '插件系统',
    reviewedBy: '',
    note: '',
    createdAt: '2026-06-10T10:00:00+08:00',
  },
];

const workspaceBundle: WorkspaceBundle = {
  projects: [
    {
      id: 'prj-riverside',
      name: '津湾河岸复合街区',
      owner: '林知远',
      status: 'active',
      cityScaleKm2: 1.2,
      coordinateSystem: 'CGCS2000 / Tianjin Local Grid',
      currentVersion: 'v18',
      updatedAt: '2026-05-24T15:20:00+08:00',
      sceneCount: 1,
      tags: ['滨水'],
    },
  ],
  scenes: [
    {
      id: 'scn-river-main',
      projectId: 'prj-riverside',
      name: '主河岸日间运营场景',
      status: 'editing',
      version: 'v18',
      templateId: 'tpl-waterfront',
      roadType: '慢行优先断面',
      treeType: '国槐 + 银杏混植',
      seatType: '滨水木质长椅',
      treeDensity: 72,
      roadWidth: 8,
      weather: '多云',
      timeOfDay: '16:30',
      objectCount: 4218,
      issueCount: 2,
    },
  ],
  assets: [
    {
      id: 'asset-seat-wood',
      name: '滨水木质长椅',
      type: '3d-model',
      format: 'FBX',
      status: 'available',
      license: 'Internal',
      sizeMb: 17,
    },
  ],
  templates: [
    {
      id: 'tpl-waterfront',
      name: '滨水活力街区',
      style: '亲水慢行 + 商业外摆',
      rulesVersion: 'tpl-r4.2',
      recommendedTree: '国槐 + 银杏混植',
      recommendedRoad: '慢行优先断面',
      recommendedSeat: '滨水木质长椅',
      densityRange: [50, 85],
      conflictHints: [],
    },
  ],
  tasks: [
    {
      id: 'task-1001',
      traceId: 'trace-1001',
      projectId: 'prj-riverside',
      sceneId: 'scn-river-main',
      title: '道路宽度设置',
      functionName: 'set_street_width',
      status: 'success',
      priority: 3,
      progress: 100,
      createdBy: '林知远',
      createdAt: '2026-05-24T15:11:00+08:00',
      elapsedMs: 914,
      dependsOn: [],
      retryable: false,
      params: { width: 8 },
      resultObjects: [],
      logs: [],
    },
  ],
  commands: [],
  simulations: [],
  auditLogs: [],
  versions: [],
  functions: [
    {
      name: 'apply_road_texture',
      title: '道路纹理',
      category: 'asset',
      description: '切换道路纹理材质',
      enabled: true,
      risk: 'low',
      schemaSummary: 'texture_id',
      averageMs: 400,
    },
    {
      name: 'place_furniture',
      title: '放置城市家具',
      category: 'asset',
      description: '在城市对象周围放置3D家具',
      enabled: true,
      risk: 'low',
      schemaSummary: 'asset_id, count, spacing',
      averageMs: 600,
    },
    {
      name: 'set_street_width',
      title: '道路宽度设置',
      category: 'layout',
      description: '调整城市道路宽度',
      enabled: true,
      risk: 'low',
      schemaSummary: 'width',
      averageMs: 310,
    },
  ],
  settings: [
    {
      id: 'set-llm-confidence',
      title: '低置信度澄清阈值',
      description: '低于阈值时禁止自动执行',
      value: 0.72,
      category: 'llm',
      locked: false,
    },
  ],
  health: [
    {
      id: 'health-api',
      name: '控制平面 API',
      status: 'healthy',
      latencyMs: 42,
      successRate: 99.8,
      description: '认证、项目、任务编排入口',
    },
  ],
};

const apiMock = vi.hoisted(() => ({
  login: vi.fn(),
  getWorkspaceBundle: vi.fn(),
  getDashboardSummary: vi.fn(),
  getAdminUsers: vi.fn(),
  getPluginReviews: vi.fn(),
}));

vi.mock('../../src/services/api', () => ({ api: apiMock }));

function renderApp(initialPath = '/login') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <SessionProvider>
        <WorkspaceProvider>
          <App />
        </WorkspaceProvider>
      </SessionProvider>
    </MemoryRouter>,
  );
}

async function loginAs(role: RoleCode) {
  const user = userEvent.setup();
  renderApp('/login');

  if (role !== 'modeler') {
    await user.click(await screen.findByRole('button', { name: new RegExp(`${role === 'analyst' ? '行业分析师' : '系统管理员'}`) }));
  }
  await user.click(screen.getByRole('button', { name: /进入系统/ }));
}

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    localStorage.clear();
    apiMock.login.mockImplementation(async (request: LoginRequest) => {
      const role = request.role ?? 'modeler';
      return {
        traceId: 'trace-login',
        data: {
          token: `jwt-${role}-test`,
          user: makeUser(role),
          expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
        },
      };
    });
    apiMock.getWorkspaceBundle.mockResolvedValue({ traceId: 'trace-workspace', data: workspaceBundle });
    apiMock.getDashboardSummary.mockResolvedValue({
      traceId: 'trace-summary',
      data: {
        projectTotal: 1,
        runningTasks: 0,
        failedTasks: 0,
        auditWarnings: 0,
        simulationSuccessRate: 100,
        pluginHealthRate: 99,
      },
    });
    apiMock.getAdminUsers.mockResolvedValue({ traceId: 'trace-users', data: demoUsers });
    apiMock.getPluginReviews.mockResolvedValue({ traceId: 'trace-plugin-reviews', data: pluginReviews });
    vi.spyOn(window, 'fetch').mockResolvedValue({
      json: async () => ({ data: workspaceBundle }),
    } as Response);
  });

  it('renders the login page for unauthenticated users', async () => {
    renderApp('/login');

    expect(await screen.findByRole('heading', { name: '登录工作台' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /进入系统/ })).toBeInTheDocument();
  });

  it('redirects protected routes to login when unauthenticated', async () => {
    renderApp('/modeler');

    expect(await screen.findByRole('heading', { name: '登录工作台' })).toBeInTheDocument();
  });

  it('logs in as modeler and opens the modeler portal', async () => {
    await loginAs('modeler');

    expect(await screen.findByRole('heading', { name: '场景建模师门户' })).toBeInTheDocument();
    expect(screen.getByText('津湾河岸复合街区 / 主河岸日间运营场景')).toBeInTheDocument();
  });

  it('logs in as analyst and opens the analyst portal', async () => {
    await loginAs('analyst');

    expect(await screen.findByRole('heading', { name: '行业分析师门户' })).toBeInTheDocument();
    expect(screen.getByText(/多模态方案推演/)).toBeInTheDocument();
  });

  it('logs in as admin and opens the admin portal', async () => {
    await loginAs('admin');

    expect(await screen.findByRole('heading', { name: '系统管理员门户' })).toBeInTheDocument();
    expect(screen.getByText('管理用户、审核插件、维护白名单与审计证据链。')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '用户权限分配' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '审核插件' })).toBeInTheDocument();
  });

  it('redirects a modeler away from admin-only settings', async () => {
    const session = {
      token: 'jwt-modeler-test',
      user: makeUser('modeler'),
      expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    };
    localStorage.setItem('smart-city-session', JSON.stringify(session));

    renderApp('/settings');

    await waitFor(() => expect(screen.queryByRole('heading', { name: '登录工作台' })).not.toBeInTheDocument());
    expect(await screen.findByRole('heading', { name: '场景建模师门户' })).toBeInTheDocument();
  });

  it('redirects a modeler away from the admin route and hides admin-only actions', async () => {
    const session = {
      token: 'jwt-modeler-test',
      user: makeUser('modeler'),
      expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    };
    localStorage.setItem('smart-city-session', JSON.stringify(session));

    renderApp('/admin');

    expect(await screen.findByRole('heading', { name: '场景建模师门户' })).toBeInTheDocument();
    expect(screen.queryByText('删除用户')).not.toBeInTheDocument();
    expect(screen.queryByText('审核通过')).not.toBeInTheDocument();
    expect(screen.queryByText('审核拒绝')).not.toBeInTheDocument();
  });

  it('clears an invalid stored session and returns to login', async () => {
    localStorage.setItem(
      'smart-city-session',
      JSON.stringify({
        token: 'jwt-invalid-test',
        user: {
          id: 'usr-invalid',
          name: '非法角色',
          email: 'invalid@nku.city',
          role: 'owner',
          department: '测试',
        },
        expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      }),
    );

    renderApp('/admin');

    expect(await screen.findByRole('heading', { name: '登录工作台' })).toBeInTheDocument();
    expect(localStorage.getItem('smart-city-session')).toBeNull();
  });

  it('opens the Blender plugin entry dialog from the modeler portal', async () => {
    const user = userEvent.setup();
    await loginAs('modeler');

    await user.click(await screen.findByRole('button', { name: /进入 Blender 插件系统/ }));

    expect(await screen.findByRole('dialog', { name: /进入 Blender 插件系统/ })).toBeInTheDocument();
    expect(screen.getByText(/View3D > Sidebar > LLM City Generator/)).toBeInTheDocument();
    expect(screen.getByText(/主系统已授权/)).toBeInTheDocument();
  });
});
