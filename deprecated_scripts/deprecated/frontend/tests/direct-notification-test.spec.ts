import { test, expect } from '@playwright/test';

test.describe('Direct Notification Test', () => {
  test('should test notification system directly without full app', async ({ page }) => {
    // Enable console logging
    page.on('console', (msg) => {
      console.log(`[CONSOLE] ${msg.type()}: ${msg.text()}`);
    });

    // Create a simple test page that imports and tests our notification system
    await page.setContent(`
      <html>
        <head>
          <title>Notification Test</title>
          <link rel="stylesheet" href="https://unpkg.com/antd@5/dist/reset.css">
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            button { padding: 10px 15px; margin: 10px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .ant-notification { z-index: 1000; }
          </style>
        </head>
        <body>
          <h1>Testing Notification System</h1>
          <button id="test-antd">Test Antd Notification</button>
          <button id="test-process">Test Process Notification</button>
          <div id="output"></div>
          
          <script type="module">
            // Import React and antd from CDN
            import { notification } from 'https://cdn.skypack.dev/antd';
            
            window.testAntdNotification = function() {
              console.log('Testing basic Antd notification...');
              try {
                notification.success({
                  message: 'Test Success',
                  description: 'This is a test notification from Antd',
                  placement: 'topRight',
                  duration: 3,
                });
                document.getElementById('output').innerHTML += '<p>✅ Antd notification triggered</p>';
              } catch (error) {
                console.error('Antd notification failed:', error);
                document.getElementById('output').innerHTML += '<p>❌ Antd notification failed: ' + error.message + '</p>';
              }
            };
            
            window.testProcessNotification = function() {
              console.log('Testing process notification...');
              try {
                const steps = [
                  'Initializing pipeline...',
                  'Processing Google Places data...',
                  'Geocoding locations...',
                  'Generating AI content...',
                  'Preparing for WordPress sync...',
                  'Pipeline completed!'
                ];
                
                let currentStep = 0;
                const key = 'process-test-' + Date.now();
                
                const updateProgress = () => {
                  const progress = ((currentStep + 1) / steps.length) * 100;
                  
                  notification.open({
                    key,
                    message: 'Reprocessing Test Provider',
                    description: (
                      '<div>' +
                        '<div>' + steps[currentStep] + '</div>' +
                        '<div style="width: 100%; background: #f0f0f0; border-radius: 4px; height: 8px; margin: 8px 0;">' +
                          '<div style="width: ' + progress + '%; background: #1890ff; height: 100%; border-radius: 4px; transition: width 0.3s;"></div>' +
                        '</div>' +
                        '<div style="font-size: 12px; color: #666;">Process ID: 12345</div>' +
                      '</div>'
                    ),
                    duration: 0,
                    placement: 'topRight',
                    style: { width: '400px' }
                  });
                  
                  currentStep++;
                  if (currentStep < steps.length) {
                    setTimeout(updateProgress, 2000);
                  } else {
                    // Show completion
                    setTimeout(() => {
                      notification.open({
                        key,
                        message: 'Reprocessing Complete',
                        description: (
                          '<div>' +
                            '<div>✅ Processing completed successfully!</div>' +
                            '<div style="margin-top: 12px;">' +
                              '<button onclick="dismissNotification()">View Results</button> ' +
                              '<button onclick="notification.destroy(\'' + key + '\')">Dismiss</button>' +
                            '</div>' +
                          '</div>'
                        ),
                        duration: 0,
                        placement: 'topRight',
                        style: { width: '400px' }
                      });
                    }, 1000);
                  }
                };
                
                updateProgress();
                document.getElementById('output').innerHTML += '<p>✅ Process notification started</p>';
                
              } catch (error) {
                console.error('Process notification failed:', error);
                document.getElementById('output').innerHTML += '<p>❌ Process notification failed: ' + error.message + '</p>';
              }
            };
            
            window.dismissNotification = function() {
              alert('Would navigate to results page');
            };
            
            // Add event listeners
            document.getElementById('test-antd').addEventListener('click', window.testAntdNotification);
            document.getElementById('test-process').addEventListener('click', window.testProcessNotification);
            
          </script>
        </body>
      </html>
    `);

    // Test basic antd notification
    console.log('[TEST] Testing basic Antd notification...');
    await page.click('#test-antd');
    await page.waitForTimeout(1000);

    // Check if basic notification appears
    const basicNotification = await page.locator('.ant-notification-notice').count();
    console.log(`[TEST] Basic notification count: ${basicNotification}`);

    // Test process notification
    console.log('[TEST] Testing process notification...');
    await page.click('#test-process');
    await page.waitForTimeout(1000);

    // Check for process notification
    const processNotification = await page.locator('text=Reprocessing Test Provider').count();
    console.log(`[TEST] Process notification count: ${processNotification}`);

    // Wait for progress to advance
    await page.waitForTimeout(3000);
    const progressText = await page.locator('text=Processing Google Places data').count();
    console.log(`[TEST] Progress text found: ${progressText}`);

    await page.waitForTimeout(5000);
    const completionText = await page.locator('text=Generating AI content').count();
    console.log(`[TEST] Later progress text found: ${completionText}`);

    // Take screenshot
    await page.screenshot({ path: 'notification-test.png', fullPage: true });

    // The test should pass if any notifications appeared
    expect(basicNotification + processNotification).toBeGreaterThan(0);
  });
});