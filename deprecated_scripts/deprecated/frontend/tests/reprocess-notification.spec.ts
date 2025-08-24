import { test, expect } from '@playwright/test';

test.describe('Provider Reprocess Notification System', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the API responses
    await page.route('**/api/auth/check', async route => {
      await route.fulfill({
        json: { authenticated: true, user: { username: 'test' } }
      });
    });

    await page.route('**/api/providers*', async route => {
      await route.fulfill({
        json: {
          success: true,
          providers: [
            {
              id: 1,
              provider_name: 'Test Provider',
              status: 'pending',
              city: 'Tokyo',
              address: '123 Test St',
              // Missing fields to trigger the reprocess button
              ai_description: null,
              seo_title: null,
              featured_image_url: null,
              latitude: null,
              longitude: null,
              business_hours: null,
              rating: null
            }
          ],
          total: 1,
          page: 1,
          per_page: 20,
          total_pages: 1
        }
      });
    });

    // Mock the reprocess API endpoint
    await page.route('**/api/pipeline/providers/reprocess', async route => {
      await route.fulfill({
        json: {
          success: true,
          message: 'Reprocessing initiated for 1 providers',
          provider_ids: [1],
          provider_count: 1,
          process_id: 12345
        }
      });
    });

    // Navigate to providers page
    await page.goto('/providers');
    await expect(page).toHaveTitle(/Healthcare Directory/);
  });

  test('should show reprocess notification when clicking reprocess provider button', async ({ page }) => {
    // Wait for the providers table to load
    await expect(page.getByText('Test Provider')).toBeVisible();

    // Click on the provider to open the detail modal
    await page.getByText('Test Provider').click();

    // Wait for the modal to open
    await expect(page.getByRole('dialog')).toBeVisible();

    // Look for the Data Completeness section and the Re-process Provider button
    await expect(page.getByText('Data Completeness')).toBeVisible();
    
    // Click the Re-process Provider button
    const reprocessButton = page.getByRole('button', { name: /re-process provider/i });
    await expect(reprocessButton).toBeVisible();
    await reprocessButton.click();

    // Check that the notification appears
    await expect(page.locator('.ant-notification')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Reprocessing Test Provider')).toBeVisible();

    // Check for the progress elements
    await expect(page.getByText('Initializing')).toBeVisible({ timeout: 2000 });
    await expect(page.locator('.ant-progress')).toBeVisible();

    // Wait for the progress to advance through steps
    await expect(page.getByText(/Processing Google Places data/)).toBeVisible({ timeout: 3000 });
    await expect(page.getByText(/Geocoding locations/)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Generating AI content/)).toBeVisible({ timeout: 7000 });
    
    // Wait for completion
    await expect(page.getByText(/Pipeline completed/)).toBeVisible({ timeout: 12000 });
    
    // Check for completion actions
    await expect(page.getByRole('button', { name: /view results/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /dismiss/i })).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Override the reprocess API to return an error
    await page.route('**/api/pipeline/providers/reprocess', async route => {
      await route.fulfill({
        status: 500,
        json: {
          success: false,
          error: 'Internal server error'
        }
      });
    });

    // Navigate and open provider modal
    await page.goto('/providers');
    await page.getByText('Test Provider').click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click the Re-process Provider button
    const reprocessButton = page.getByRole('button', { name: /re-process provider/i });
    await reprocessButton.click();

    // Check that an error message appears
    await expect(page.getByText(/Failed to start pipeline/)).toBeVisible({ timeout: 5000 });
  });

  test('should show loading state on reprocess button', async ({ page }) => {
    // Navigate and open provider modal
    await page.goto('/providers');
    await page.getByText('Test Provider').click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click the Re-process Provider button
    const reprocessButton = page.getByRole('button', { name: /re-process provider/i });
    await reprocessButton.click();

    // Check that the button shows loading state briefly
    await expect(reprocessButton.locator('.anticon-loading')).toBeVisible({ timeout: 1000 });
  });
});