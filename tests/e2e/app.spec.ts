import { expect, test } from '@playwright/test';

test('loads the login workflow', async ({ page }) => {
  await page.goto('/login');

  await expect(page.getByRole('heading', { name: '登录工作台' })).toBeVisible();
  await expect(page.getByRole('button', { name: /进入系统/ })).toBeVisible();
});
