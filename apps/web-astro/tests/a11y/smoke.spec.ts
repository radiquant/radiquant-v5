import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('login page has no critical a11y violations', async ({ page }) => {
  await page.goto('/login');
  const results = await new AxeBuilder({ page }).analyze();
  const critical = results.violations.filter((v: any) => v.impact === 'critical');
  expect(critical).toHaveLength(0);
});
