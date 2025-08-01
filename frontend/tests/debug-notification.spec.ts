import { test, expect } from '@playwright/test';

test.describe('Debug Notification System', () => {
  test('should debug notification system step by step', async ({ page }) => {
    // Enable console logging
    page.on('console', (msg) => {
      console.log(`[BROWSER LOG] ${msg.type()}: ${msg.text()}`);
    });

    // Capture network requests
    page.on('request', (request) => {
      if (request.url().includes('api/')) {
        console.log(`[REQUEST] ${request.method()} ${request.url()}`);
      }
    });

    page.on('response', (response) => {
      if (response.url().includes('api/')) {
        console.log(`[RESPONSE] ${response.status()} ${response.url()}`);
      }
    });

    // Mock auth
    await page.route('**/api/auth/check', async route => {
      await route.fulfill({
        json: { authenticated: true, user: { username: 'test' } }
      });
    });

    // Mock providers API with a provider that has missing data
    await page.route('**/api/providers*', async route => {
      await route.fulfill({
        json: {
          success: true,
          providers: [
            {
              id: 411,
              provider_name: 'Tokyo International Dental clinic Roppongi',
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

    // Mock the reprocess API
    await page.route('**/api/pipeline/providers/reprocess', async route => {
      console.log('[API MOCK] Reprocess endpoint called');
      await route.fulfill({
        json: {
          success: true,
          message: 'Reprocessing initiated for 1 providers',
          provider_ids: [411],
          provider_count: 1,
          process_id: 12345
        }
      });
    });

    // Navigate to providers page
    await page.goto('http://localhost:3001/providers');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Look for the provider
    console.log('[TEST] Looking for provider...');
    await expect(page.getByText('Tokyo International Dental clinic Roppongi')).toBeVisible({ timeout: 10000 });

    // Click on the provider to open modal
    console.log('[TEST] Clicking provider...');
    await page.getByText('Tokyo International Dental clinic Roppongi').click();

    // Wait for modal
    await page.waitForTimeout(1000);
    
    // Look for the reprocess button
    console.log('[TEST] Looking for reprocess button...');
    const reprocessButton = page.getByRole('button', { name: /re-process provider/i });
    await expect(reprocessButton).toBeVisible({ timeout: 5000 });

    console.log('[TEST] Clicking reprocess button...');
    await reprocessButton.click();

    // Wait a moment and check for any notifications
    await page.waitForTimeout(2000);

    // Check if any notification elements exist
    const notifications = await page.locator('.ant-notification').count();
    const notificationNotices = await page.locator('.ant-notification-notice').count();
    const anyNotifications = await page.locator('[data-testid*="notification"], [class*="notification"], .ant-message').count();

    console.log(`[TEST] Found ${notifications} ant-notification elements`);
    console.log(`[TEST] Found ${notificationNotices} ant-notification-notice elements`);
    console.log(`[TEST] Found ${anyNotifications} any notification-like elements`);

    // Try to find our specific notification content
    const reprocessingText = await page.locator('text=Reprocessing').count();
    const progressElements = await page.locator('.ant-progress, [class*="progress"]').count();

    console.log(`[TEST] Found ${reprocessingText} "Reprocessing" text elements`);
    console.log(`[TEST] Found ${progressElements} progress elements`);

    // Take a screenshot for debugging
    await page.screenshot({ path: 'debug-notification.png', fullPage: true });

    // Test if antd notification system is available at all
    const notificationTest = await page.evaluate(() => {
      try {
        // Check if antd notification is available globally
        if (window.antd && window.antd.notification) {
          window.antd.notification.success({
            message: 'Test',
            description: 'Test notification from Playwright'
          });
          return 'antd notification available globally';
        }
        
        // Try to import notification from antd
        if (window.notification) {
          window.notification.success({
            message: 'Test',
            description: 'Test notification from window.notification'
          });
          return 'window.notification available';
        }
        
        return 'No notification system found';
      } catch (error) {
        return 'Error: ' + error.message;
      }
    });

    console.log(`[TEST] Notification system test: ${notificationTest}`);

    // This test will fail - that's expected since we're debugging
    expect(notifications + notificationNotices).toBeGreaterThan(0);
  });
});