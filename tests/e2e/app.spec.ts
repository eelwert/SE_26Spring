import { expect, test, type Page } from '@playwright/test';

type RoleCode = 'modeler' | 'analyst' | 'admin';

const permissionsByRole: Record<RoleCode, string[]> = {
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

const workspaceBundle = {
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
  tasks: [],
  commands: [],
  simulations: [],
  auditLogs: [],
  versions: [],
  functions: [
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

const makeUser = (role: RoleCode) => ({
  id: `usr-${role}`,
  name: namesByRole[role],
  email: `${role}@nku.city`,
  role,
  department: departmentsByRole[role],
  permissions: permissionsByRole[role],
});

async function mockBackendApi(page: Page) {
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url());

    if (url.pathname === '/api/auth/login') {
      const body = route.request().postDataJSON() as { role?: RoleCode; email?: string };
      const role = body.role ?? (body.email?.split('@')[0] as RoleCode | undefined) ?? 'modeler';
      await route.fulfill({
        json: {
          traceId: 'trace-login',
          data: {
            token: `jwt-${role}-test`,
            user: makeUser(role),
            expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
          },
        },
      });
      return;
    }

    if (url.pathname === '/api/workspace/bundle') {
      await route.fulfill({ json: { traceId: 'trace-workspace', data: workspaceBundle } });
      return;
    }

    if (url.pathname === '/api/dashboard/summary') {
      await route.fulfill({
        json: {
          traceId: 'trace-summary',
          data: {
            projectTotal: 1,
            runningTasks: 0,
            failedTasks: 0,
            auditWarnings: 0,
            simulationSuccessRate: 100,
            pluginHealthRate: 99,
          },
        },
      });
      return;
    }

    await route.fulfill({ status: 404, json: { detail: `Unhandled mock route: ${url.pathname}` } });
  });
}

async function loginAs(page: Page, role: RoleCode) {
  await mockBackendApi(page);
  await page.goto('/login');

  if (role === 'analyst') {
    await page.getByRole('button', { name: /行业分析师/ }).click();
  }
  if (role === 'admin') {
    await page.getByRole('button', { name: /系统管理员/ }).click();
  }

  await page.getByRole('button', { name: /进入系统/ }).click();
}

test('loads the login page', async ({ page }) => {
  await page.goto('/login');

  await expect(page.getByRole('heading', { name: '登录工作台' })).toBeVisible();
  await expect(page.getByRole('button', { name: /进入系统/ })).toBeVisible();
});

test('logs in as modeler and opens the modeler portal', async ({ page }) => {
  await loginAs(page, 'modeler');

  await expect(page.getByRole('heading', { name: '场景建模师门户' })).toBeVisible();
  await expect(page.getByText('津湾河岸复合街区 / 主河岸日间运营场景')).toBeVisible();
});

test('logs in as analyst and opens the analyst portal', async ({ page }) => {
  await loginAs(page, 'analyst');

  await expect(page.getByRole('heading', { name: '行业分析师门户' })).toBeVisible();
  await expect(page.getByRole('button', { name: /启动交通灯仿真/ })).toBeVisible();
});

test('logs in as admin and opens the admin portal', async ({ page }) => {
  await loginAs(page, 'admin');

  await expect(page.getByRole('heading', { name: '系统管理员门户' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '审核插件' })).toBeVisible();
});

test('redirects modeler away from admin settings route', async ({ page }) => {
  await loginAs(page, 'modeler');
  await page.goto('/settings');

  await expect(page.getByRole('heading', { name: '场景建模师门户' })).toBeVisible();
});
