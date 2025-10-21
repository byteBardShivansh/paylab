import { test, expect } from '@playwright/test';

test('basic API health check', async ({ request }) => {
  const response = await request.get('http://localhost:8000/health');
  expect(response.ok()).toBeTruthy();
  
  const data = await response.json();
  expect(data.status).toBe('ok');
});

test('basic frontend page loads', async ({ page }) => {
  await page.goto('http://localhost:8000/app/frontend/index.html');
  await expect(page.locator('h1')).toContainText('Payments API Test');
});