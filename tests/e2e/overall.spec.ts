import { expect, test, type Page } from '@playwright/test';

const API_BASE_URL = 'http://127.0.0.1:18000/api';

async function loginAsModeler(page: Page) {
  await page.goto('/login');
  await page.locator('form.login-form button[type="submit"]').click();
  await expect(page).toHaveURL(/\/modeler$/);
  await expect(page.locator('.role-hero')).toBeVisible();
}

test('runs a real frontend/backend flow with fallback LLM and fake Blender acknowledgements', async ({ page, request }) => {
  await loginAsModeler(page);

  await expect
    .poll(async () => {
      const response = await request.get(`${API_BASE_URL}/health`);
      expect(response.ok()).toBeTruthy();
      const body = (await response.json()) as { frontend: string };
      return body.frontend;
    })
    .toBe('connected');

  await page.goto('/multimodal');
  await expect(page).toHaveURL(/\/multimodal$/);
  await expect(page.locator('form.mmi-form')).toBeVisible();

  const commandText = '道路宽度调到10米，增加到4车道，傍晚小雨';
  await page.locator('form.mmi-form textarea').fill(commandText);
  await page.locator('form.mmi-form button[type="submit"]').click();

  await expect(page.getByText('set_weather_lighting')).toBeVisible();
  await expect(page.getByText('set_street_width')).toBeVisible();
  await expect(page.getByText('set_lane_amount')).toBeVisible();

  await page.locator('section:has(.plan-board) .section-header button').click();

  const relatedTasks = page.locator('.table-row.task-row');
  await expect(relatedTasks).toHaveCount(3);
  await expect(relatedTasks.locator('.status-queued')).toHaveCount(3);

  const blenderRegister = await request.post(`${API_BASE_URL}/blender/register`, {
    data: { version: 'playwright-fake-blender', blender: 'fake-blender-4.3' },
  });
  expect(blenderRegister.ok()).toBeTruthy();

  const pendingResponse = await request.get(`${API_BASE_URL}/tasks/pending`);
  expect(pendingResponse.ok()).toBeTruthy();
  const pendingData = (await pendingResponse.json()) as {
    data: { tasks: Array<{ id: string; functionName: string }> };
  };
  expect(pendingData.data.tasks).toHaveLength(3);

  for (const task of pendingData.data.tasks) {
    const resultResponse = await request.post(`${API_BASE_URL}/tasks/${task.id}/result`, {
      data: {
        status: 'success',
        results: [`fake blender executed ${task.functionName}`],
      },
    });
    expect(resultResponse.ok()).toBeTruthy();
  }

  await expect(relatedTasks.locator('.status-success')).toHaveCount(3);

  await expect
    .poll(async () => {
      const response = await request.get(`${API_BASE_URL}/health`);
      expect(response.ok()).toBeTruthy();
      const body = (await response.json()) as { blender: string };
      return body.blender;
    })
    .toBe('connected');

  await page.goto('/tasks');
  await expect(page).toHaveURL(/\/tasks$/);
  await expect(page.locator('.task-table')).toBeVisible();
  await expect(page.getByText('fake blender executed set_weather_lighting')).toBeVisible();
  await expect(page.getByText('fake blender executed set_street_width')).toBeVisible();
  await expect(page.getByText('fake blender executed set_lane_amount')).toBeVisible();
});
