import { test, expect } from '@playwright/test';

test('root page loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('body')).toBeVisible();
});

test('workflow new redirects or shows content', async ({ page }) => {
  const response = await page.goto('/workflow/new');
  // Either 200 with content or 302 redirect is acceptable
  expect([200, 302]).toContain(response?.status());
});
