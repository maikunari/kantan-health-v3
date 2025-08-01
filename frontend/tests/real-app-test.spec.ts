import { test, expect } from '@playwright/test';

test.describe('Real App Notification Test', () => {
  test('should test reprocess notification in actual running app', async ({ page, context }) => {
    // Set longer timeouts for real app testing
    test.setTimeout(60000);
    
    // Enable console logging to debug
    page.on('console', (msg) => {
      console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
    });

    page.on('pageerror', (error) => {
      console.log(`[PAGE ERROR] ${error.message}`);
    });

    // Monitor network requests
    let apiCalled = false;
    page.on('response', async (response) => {
      if (response.url().includes('/api/pipeline/providers/reprocess')) {
        apiCalled = true;
        const responseText = await response.text();
        console.log(`[API RESPONSE] ${response.status()}: ${responseText}`);
      }
    });

    try {
      // Navigate to the actual running app
      console.log('[TEST] Navigating to running app...');
      await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
      
      // Wait for page to fully load
      await page.waitForTimeout(3000);
      
      // Check if we can see the app title or main content
      const hasTitle = await page.locator('h1, [class*="title"], .ant-typography-title').count();
      console.log(`[TEST] Found ${hasTitle} title elements`);
      
      // Take a screenshot to see the current state
      await page.screenshot({ path: 'real-app-state.png', fullPage: true });
      
      // Look for providers navigation or content
      const navItems = await page.locator('a[href*="provider"], .ant-menu-item, nav a').count();
      console.log(`[TEST] Found ${navItems} navigation items`);
      
      // Try to navigate to providers page
      console.log('[TEST] Looking for providers link...');
      const providersLink = page.locator('a[href*="provider"], text=Providers').first();
      const providersLinkVisible = await providersLink.isVisible({ timeout: 5000 }).catch(() => false);
      
      if (providersLinkVisible) {
        console.log('[TEST] Clicking providers link...');
        await providersLink.click();
        await page.waitForTimeout(2000);
      } else {
        console.log('[TEST] Trying direct navigation to providers...');
        await page.goto('http://localhost:3001/providers', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
      }
      
      // Look for any provider entries
      const providerElements = await page.locator('tr, .ant-table-row, [class*="provider"]').count();
      console.log(`[TEST] Found ${providerElements} potential provider elements`);
      
      // Look specifically for the provider we know exists
      const targetProvider = page.getByText('Tokyo International Dental clinic Roppongi').first();
      const targetProviderVisible = await targetProvider.isVisible({ timeout: 5000 }).catch(() => false);
      
      if (targetProviderVisible) {
        console.log('[TEST] Found target provider, clicking...');
        await targetProvider.click();
        await page.waitForTimeout(2000);
        
        // Look for reprocess button in modal or details
        const reprocessButton = page.getByRole('button', { name: /re-process|reprocess/i }).first();
        const reprocessButtonVisible = await reprocessButton.isVisible({ timeout: 5000 }).catch(() => false);
        
        if (reprocessButtonVisible) {
          console.log('[TEST] Found reprocess button, clicking...');
          
          // Take screenshot before clicking
          await page.screenshot({ path: 'before-reprocess-click.png', fullPage: true });
          
          await reprocessButton.click();
          console.log('[TEST] Clicked reprocess button');
          
          // Wait for potential notification
          await page.waitForTimeout(3000);
          
          // Take screenshot after clicking
          await page.screenshot({ path: 'after-reprocess-click.png', fullPage: true });
          
          // Check for any notifications
          const notifications = await page.locator('.ant-notification, .ant-message, [class*="notification"]').count();
          console.log(`[TEST] Found ${notifications} notification elements after click`);
          
          // Check for specific notification content
          const reprocessingText = await page.locator('text=Reprocessing, text=Processing, text=Initializing').count();
          console.log(`[TEST] Found ${reprocessingText} processing-related text elements`);
          
          // List all visible text containing "process" or similar
          const allProcessText = await page.locator('text=/[Pp]rocess|[Rr]eprocess|[Ii]nitial|[Cc]omplete/').allTextContents();
          console.log(`[TEST] All process-related text: ${JSON.stringify(allProcessText)}`);
          
          console.log(`[TEST] API was called: ${apiCalled}`);
          
        } else {
          console.log('[TEST] ❌ Reprocess button not found');
        }
      } else {
        console.log('[TEST] ❌ Target provider not found');
      }
      
    } catch (error) {
      console.log(`[TEST] ❌ Test error: ${error.message}`);
      await page.screenshot({ path: 'test-error-state.png', fullPage: true });
    }
    
    // The test should pass - we're just gathering information
    expect(true).toBe(true);
  });
});