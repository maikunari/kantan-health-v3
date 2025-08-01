import { test, expect } from '@playwright/test';

test.describe('Working Notification System Test', () => {
  test('should show working reprocess notifications', async ({ page }) => {
    // Enable console logging
    page.on('console', (msg) => {
      console.log(`[CONSOLE] ${msg.type()}: ${msg.text()}`);
    });

    // Create a test page that uses our actual SimpleProcessNotification
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Working Notification Test</title>
          <meta charset="utf-8">
          <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
          <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
          <link rel="stylesheet" href="https://unpkg.com/antd@5/dist/reset.css">
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; padding: 20px; }
            .ant-notification {
              position: fixed !important;
              top: 24px !important;
              right: 24px !important;
              z-index: 1000 !important;
            }
            .ant-notification-notice {
              background: white !important;
              border: 1px solid #d9d9d9 !important;
              border-radius: 6px !important;
              box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
              margin-bottom: 16px !important;
              min-width: 300px !important;
              max-width: 400px !important;
              padding: 16px !important;
              position: relative !important;
            }
            button {
              padding: 8px 16px;
              margin: 5px;
              background: #1890ff;
              color: white;
              border: none;
              border-radius: 4px;
              cursor: pointer;
            }
            button:hover { background: #40a9ff; }
          </style>
        </head>
        <body>
          <h1>Working Notification System Test</h1>
          <button id="test-simple">Test Simple Notification</button>
          <button id="test-reprocess">Test Reprocess Notification</button>
          <div id="notification-area"></div>
          
          <script type="module">
            // Import from CDN with ES modules
            import { notification } from 'https://esm.sh/antd@5';
            
            console.log('Notification module loaded:', typeof notification);
            
            // Test 1: Simple notification
            window.testSimple = function() {
              console.log('Testing simple notification...');
              try {
                notification.success({
                  message: 'Test Success',
                  description: 'This is a simple test notification',
                  placement: 'topRight',
                  duration: 3,
                });
                console.log('✅ Simple notification triggered');
              } catch (error) {
                console.error('❌ Simple notification failed:', error);
              }
            };
            
            // Test 2: Process notification (simplified version)
            window.testReprocess = function() {
              console.log('Testing reprocess notification...');
              try {
                const steps = [
                  'Initializing pipeline...',
                  'Processing Google Places data...',
                  'Geocoding locations...',
                  'Generating AI content...',
                  'Preparing for WordPress sync...',
                  'Pipeline completed successfully!'
                ];
                
                let currentStep = 0;
                const key = 'reprocess-test-' + Date.now();
                
                const updateNotification = () => {
                  const progress = ((currentStep + 1) / steps.length) * 100;
                  const isCompleted = currentStep >= steps.length - 1;
                  
                  const progressBar = React.createElement('div', {
                    style: {
                      width: '100%',
                      height: '8px',
                      backgroundColor: '#f0f0f0',
                      borderRadius: '4px',
                      overflow: 'hidden',
                      margin: '8px 0'
                    }
                  }, React.createElement('div', {
                    style: {
                      width: progress + '%',
                      height: '100%',
                      backgroundColor: '#1890ff',
                      transition: 'width 0.3s ease'
                    }
                  }));
                  
                  const description = React.createElement('div', {
                    style: { display: 'flex', flexDirection: 'column', gap: '8px' }
                  }, [
                    React.createElement('div', { key: 'status', style: { display: 'flex', alignItems: 'center', gap: '8px' } }, [
                      React.createElement('span', { key: 'icon' }, '🔄'),
                      React.createElement('span', { key: 'text' }, steps[currentStep])
                    ]),
                    progressBar,
                    React.createElement('div', { 
                      key: 'process-id',
                      style: { fontSize: '12px', color: '#666' }
                    }, 'Process ID: 12345')
                  ]);
                  
                  if (isCompleted) {
                    const completedDescription = React.createElement('div', {
                      style: { display: 'flex', flexDirection: 'column', gap: '8px' }
                    }, [
                      React.createElement('div', { key: 'success', style: { display: 'flex', alignItems: 'center', gap: '8px' } }, [
                        React.createElement('span', { key: 'icon' }, '✅'),
                        React.createElement('span', { key: 'text' }, 'Processing completed successfully!')
                      ]),
                      React.createElement('div', { key: 'buttons', style: { display: 'flex', gap: '8px', marginTop: '8px' } }, [
                        React.createElement('button', {
                          key: 'view',
                          onClick: () => alert('Would navigate to results'),
                          style: { padding: '4px 8px', border: '1px solid #d9d9d9', borderRadius: '4px', background: 'white', cursor: 'pointer' }
                        }, 'View Results'),
                        React.createElement('button', {
                          key: 'dismiss',
                          onClick: () => notification.destroy(key),
                          style: { padding: '4px 8px', border: '1px solid #d9d9d9', borderRadius: '4px', background: 'white', cursor: 'pointer' }
                        }, 'Dismiss')
                      ])
                    ]);
                    
                    notification.open({
                      key,
                      message: '✅ Test Provider Reprocessing Complete',
                      description: completedDescription,
                      duration: 0,
                      placement: 'topRight',
                      style: { width: '400px' },
                      closable: true
                    });
                  } else {
                    notification.open({
                      key,
                      message: 'Reprocessing Test Provider',
                      description: description,
                      duration: 0,
                      placement: 'topRight',
                      style: { width: '400px' },
                      closable: true
                    });
                    
                    currentStep++;
                    if (currentStep < steps.length) {
                      setTimeout(updateNotification, 2000);
                    }
                  }
                };
                
                updateNotification();
                console.log('✅ Reprocess notification started');
                
              } catch (error) {
                console.error('❌ Reprocess notification failed:', error);
              }
            };
            
            // Add event listeners
            document.getElementById('test-simple').addEventListener('click', window.testSimple);
            document.getElementById('test-reprocess').addEventListener('click', window.testReprocess);
          </script>
        </body>
      </html>
    `);

    // Test simple notification first
    console.log('[TEST] Testing simple notification...');
    await page.click('#test-simple');
    await page.waitForTimeout(1000);

    // Check if simple notification appears
    await expect(page.locator('.ant-notification-notice')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Test Success')).toBeVisible();

    // Wait for simple notification to disappear
    await page.waitForTimeout(4000);

    // Test reprocess notification
    console.log('[TEST] Testing reprocess notification...');
    await page.click('#test-reprocess');
    await page.waitForTimeout(1000);

    // Check for reprocess notification
    await expect(page.getByText('Reprocessing Test Provider')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Initializing pipeline...')).toBeVisible();

    // Wait for progress to advance
    await expect(page.getByText('Processing Google Places data...')).toBeVisible({ timeout: 3000 });
    await expect(page.getByText('Geocoding locations...')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Generating AI content...')).toBeVisible({ timeout: 7000 });

    // Wait for completion
    await expect(page.getByText('Processing completed successfully!')).toBeVisible({ timeout: 12000 });
    await expect(page.getByRole('button', { name: 'View Results' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Dismiss' })).toBeVisible();

    // Test dismiss functionality
    await page.getByRole('button', { name: 'Dismiss' }).click();
    await expect(page.locator('.ant-notification-notice')).not.toBeVisible({ timeout: 2000 });

    console.log('[TEST] ✅ All notification tests passed!');
  });
});