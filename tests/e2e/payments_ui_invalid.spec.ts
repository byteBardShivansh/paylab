import { test, expect, Page } from '@playwright/test';

/**
 * E2E tests for Payments UI with invalid data submission
 * 
 * These tests verify that the frontend properly handles invalid payment data
 * and displays appropriate error messages when the API returns 4xx errors.
 */

// Test configuration
const BASE_URL = 'http://localhost:8000';
const API_KEY = 'dev-secret';

test.describe('Payments UI - Invalid Data Submission', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the payments frontend
    await page.goto(`${BASE_URL}/app/frontend/index.html`);
    
    // Wait for the page to load completely
    await expect(page.locator('h1')).toContainText('Payments API Test');
    
    // Set up API key in localStorage to avoid prompts during tests
    await page.evaluate((apiKey) => {
      localStorage.setItem('payments_api_key', apiKey);
    }, API_KEY);
  });

  test('should show validation error for negative amount', async ({ page }) => {
    // Fill out the form with invalid negative amount
    await page.fill('#orderId', 'ORD-NEGATIVE-001');
    await page.fill('#amount', '-10.50');
    await page.selectOption('#currency', 'USD');

    // Set up network interception to capture API call
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/payments') && response.request().method() === 'POST'
    );

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for the API response
    const response = await responsePromise;
    
    // Assert that API returns 4xx error (422 for validation error)
    expect(response.status()).toBe(422);
    
    // Verify the response contains validation error details
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('detail');
    expect(Array.isArray(responseBody.detail)).toBe(true);
    
    // Check that the error is related to amount validation
    const amountError = responseBody.detail.find((error: any) => 
      error.loc && error.loc.includes('amount')
    );
    expect(amountError).toBeDefined();
    expect(amountError.type).toContain('greater_than');

    // Verify UI shows error response
    await expect(page.locator('#responseArea')).toBeVisible();
    await expect(page.locator('#responseArea')).toHaveClass(/error/);
    
    // Check that the response content shows the error
    const responseContent = await page.locator('#responseContent').textContent();
    expect(responseContent).toContain('422');
    expect(responseContent).toContain('detail');
  });

  test('should show validation error for zero amount', async ({ page }) => {
    // Fill out the form with zero amount
    await page.fill('#orderId', 'ORD-ZERO-001');
    await page.fill('#amount', '0');
    await page.selectOption('#currency', 'USD');

    // Set up network interception
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/payments') && response.request().method() === 'POST'
    );

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for the API response
    const response = await responsePromise;
    
    // Assert 4xx error
    expect(response.status()).toBe(422);
    
    // Verify validation error for amount
    const responseBody = await response.json();
    expect(responseBody.detail).toBeDefined();
    
    // Verify UI shows error
    await expect(page.locator('#responseArea')).toHaveClass(/error/);
  });

  test('should show validation error for empty order ID', async ({ page }) => {
    // Fill out the form with empty order ID
    await page.fill('#orderId', '');
    await page.fill('#amount', '10.50');
    await page.selectOption('#currency', 'USD');

    // Set up network interception
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/payments') && response.request().method() === 'POST'
    );

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for the API response
    const response = await responsePromise;
    
    // Assert 4xx error
    expect(response.status()).toBe(422);
    
    // Verify validation error
    const responseBody = await response.json();
    expect(responseBody.detail).toBeDefined();
    
    const orderIdError = responseBody.detail.find((error: any) => 
      error.loc && error.loc.includes('order_id')
    );
    expect(orderIdError).toBeDefined();

    // Verify UI shows error
    await expect(page.locator('#responseArea')).toHaveClass(/error/);
  });

  test('should show validation error for extremely large amount', async ({ page }) => {
    // Fill out the form with extremely large amount (beyond reasonable limits)
    await page.fill('#orderId', 'ORD-LARGE-001');
    await page.fill('#amount', '999999999999.99');
    await page.selectOption('#currency', 'USD');

    // Set up network interception
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/payments') && response.request().method() === 'POST'
    );

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for the API response
    const response = await responsePromise;
    
    // Assert that we get some kind of error response (could be 422 or 400)
    expect(response.status()).toBeGreaterThanOrEqual(400);
    expect(response.status()).toBeLessThan(500);

    // Verify UI shows error
    await expect(page.locator('#responseArea')).toHaveClass(/error/);
  });

  test('should show error when API key is missing', async ({ page }) => {
    // Clear the API key from localStorage
    await page.evaluate(() => {
      localStorage.removeItem('payments_api_key');
    });

    // Fill out valid form data
    await page.fill('#orderId', 'ORD-NO-KEY-001');
    await page.fill('#amount', '10.50');
    await page.selectOption('#currency', 'USD');

    // Mock the prompt to return null (user cancels)
    await page.evaluate(() => {
      window.prompt = () => null;
    });

    // Submit the form
    await page.click('button[type="submit"]');

    // Verify that an error is shown for missing API key
    await expect(page.locator('#responseArea')).toBeVisible();
    await expect(page.locator('#responseArea')).toHaveClass(/error/);
    
    const responseContent = await page.locator('#responseContent').textContent();
    expect(responseContent).toContain('API key required');
  });

  test('should show 401 error for invalid API key', async ({ page }) => {
    // Set invalid API key
    await page.evaluate(() => {
      localStorage.setItem('payments_api_key', 'invalid-key');
    });

    // Fill out valid form data
    await page.fill('#orderId', 'ORD-BAD-KEY-001');
    await page.fill('#amount', '10.50');
    await page.selectOption('#currency', 'USD');

    // Set up network interception
    const responsePromise = page.waitForResponse(response => 
      response.url().includes('/payments') && response.request().method() === 'POST'
    );

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for the API response
    const response = await responsePromise;
    
    // Assert 401 Unauthorized
    expect(response.status()).toBe(401);
    
    // Verify error response
    const responseBody = await response.json();
    expect(responseBody.detail).toContain('Invalid or missing API key');

    // Verify UI shows error
    await expect(page.locator('#responseArea')).toHaveClass(/error/);
    
    const responseContent = await page.locator('#responseContent').textContent();
    expect(responseContent).toContain('401');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Fill out valid form data
    await page.fill('#orderId', 'ORD-NETWORK-001');
    await page.fill('#amount', '10.50');
    await page.selectOption('#currency', 'USD');

    // Simulate network failure by going offline
    await page.context().setOffline(true);

    // Submit the form
    await page.click('button[type="submit"]');

    // Verify that a network error is shown
    await expect(page.locator('#responseArea')).toBeVisible();
    await expect(page.locator('#responseArea')).toHaveClass(/error/);
    
    const responseContent = await page.locator('#responseContent').textContent();
    expect(responseContent).toContain('Network Error');
  });

  test('should reset button state after error', async ({ page }) => {
    // Fill out form with invalid data
    await page.fill('#orderId', 'ORD-BUTTON-001');
    await page.fill('#amount', '-5.00');
    await page.selectOption('#currency', 'USD');

    const submitButton = page.locator('button[type="submit"]');
    
    // Verify initial button state
    await expect(submitButton).toHaveText('Create Payment');
    await expect(submitButton).toBeEnabled();

    // Submit the form
    await submitButton.click();

    // Wait for the response to complete
    await expect(page.locator('#responseArea')).toBeVisible();

    // Verify button is reset to original state
    await expect(submitButton).toHaveText('Create Payment');
    await expect(submitButton).toBeEnabled();
  });
});

/**
 * Helper function to verify error response structure
 */
async function verifyErrorResponse(page: Page, expectedStatus: number) {
  await expect(page.locator('#responseArea')).toBeVisible();
  await expect(page.locator('#responseArea')).toHaveClass(/error/);
  
  const responseContent = await page.locator('#responseContent').textContent();
  expect(responseContent).toContain(expectedStatus.toString());
}