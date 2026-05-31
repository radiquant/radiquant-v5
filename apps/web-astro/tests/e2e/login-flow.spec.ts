import { test, expect } from '@playwright/test';

test('shows login page', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: /Anmelden/i })).toBeVisible();
});

test('login form accepts input', async ({ page }) => {
  await page.goto('/login');
  // LoginIsland uses these fields
  await page.locator('input[type="email"]').fill('therapist@example.com');
  await page.locator('input[type="password"]').fill('safe-password-123');
  await page.getByRole('button', { name: /Anmelden/ }).click();
});
