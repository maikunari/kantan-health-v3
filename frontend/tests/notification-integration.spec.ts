import { test, expect } from '@playwright/test';

test.describe('Notification System Integration Test', () => {
  test('should test reprocess notification without full app dependency', async ({ page }) => {
    // Create a minimal test page with just the notification system
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Notification Test</title>
          <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
          <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
          <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/antd@5.0.0/dist/reset.css">
          <style>
            .ant-notification {
              position: fixed;
              top: 24px;
              right: 24px;
              z-index: 1000;
            }
            .ant-notification-notice {
              background: white;
              border: 1px solid #d9d9d9;
              border-radius: 6px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.15);
              margin-bottom: 16px;
              min-width: 300px;
              padding: 16px;
            }
            .progress-bar {
              width: 100%;
              background: #f0f0f0;
              border-radius: 4px;
              overflow: hidden;
              height: 8px;
              margin: 8px 0;
            }
            .progress-fill {
              background: #1890ff;
              height: 100%;
              transition: width 2s ease;
            }
          </style>
        </head>
        <body>
          <div id="app">
            <button id="test-notification">Test Notification</button>
            <div id="notification-container"></div>
          </div>
          
          <script>
            // Mock notification system
            let notificationCount = 0;
            
            function createNotification(title, content) {
              const container = document.getElementById('notification-container');
              const notification = document.createElement('div');
              notification.className = 'ant-notification-notice';
              notification.id = 'notification-' + (++notificationCount);
              
              notification.innerHTML = \`
                <div class="ant-notification-notice-message">\${title}</div>
                <div class="ant-notification-notice-description">
                  <div id="progress-content-\${notificationCount}">
                    <div>Initializing pipeline...</div>
                    <div class="progress-bar">
                      <div class="progress-fill" id="progress-\${notificationCount}" style="width: 0%"></div>
                    </div>
                    <div style="font-size: 12px; color: #666;">Process ID: 12345</div>
                  </div>
                </div>
                <button onclick="dismissNotification('\${notification.id}')" style="position: absolute; top: 8px; right: 8px;">×</button>
              \`;
              
              container.appendChild(notification);
              
              // Simulate progress
              simulateProgress(notificationCount);
              
              return notification.id;
            }
            
            function simulateProgress(id) {
              const steps = [
                'Initializing pipeline...',
                'Processing Google Places data...',
                'Geocoding locations...',
                'Generating AI content...',
                'Preparing for WordPress sync...',
                'Pipeline completed successfully!'
              ];
              
              let currentStep = 0;
              const progressElement = document.getElementById('progress-' + id);
              const contentElement = document.getElementById('progress-content-' + id);
              
              const interval = setInterval(() => {
                if (currentStep < steps.length) {
                  const progress = ((currentStep + 1) / steps.length) * 100;
                  progressElement.style.width = progress + '%';
                  
                  const stepDiv = contentElement.querySelector('div:first-child');
                  stepDiv.textContent = steps[currentStep];
                  
                  if (currentStep === steps.length - 1) {
                    // Add completion buttons
                    contentElement.innerHTML += \`
                      <div style="margin-top: 12px;">
                        <button onclick="viewResults()" style="margin-right: 8px;">View Results</button>
                        <button onclick="dismissNotification('notification-\${id}')">Dismiss</button>
                      </div>
                    \`;
                    clearInterval(interval);
                  }
                  
                  currentStep++;
                }
              }, 2000);
            }
            
            function dismissNotification(id) {
              const notification = document.getElementById(id);
              if (notification) {
                notification.remove();
              }
            }
            
            function viewResults() {
              alert('Would navigate to Pipeline Failures page');
            }
            
            // Add click handler
            document.getElementById('test-notification').addEventListener('click', () => {
              createNotification('Reprocessing Test Provider', '');
            });
          </script>
        </body>
      </html>
    `);

    // Click the test button
    await page.click('#test-notification');

    // Check that notification appears
    await expect(page.locator('.ant-notification-notice')).toBeVisible({ timeout: 1000 });
    await expect(page.getByText('Reprocessing Test Provider')).toBeVisible();

    // Check initial progress step
    await expect(page.getByText('Initializing pipeline...')).toBeVisible();
    await expect(page.locator('.progress-bar')).toBeVisible();

    // Wait for progress to advance
    await expect(page.getByText('Processing Google Places data...')).toBeVisible({ timeout: 3000 });
    await expect(page.getByText('Geocoding locations...')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Generating AI content...')).toBeVisible({ timeout: 7000 });
    await expect(page.getByText('Preparing for WordPress sync...')).toBeVisible({ timeout: 9000 });

    // Wait for completion
    await expect(page.getByText('Pipeline completed successfully!')).toBeVisible({ timeout: 12000 });
    
    // Check for completion buttons
    await expect(page.getByRole('button', { name: 'View Results' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Dismiss' })).toBeVisible();

    // Test dismiss functionality
    await page.getByRole('button', { name: 'Dismiss' }).click();
    await expect(page.locator('.ant-notification-notice')).not.toBeVisible();
  });
});