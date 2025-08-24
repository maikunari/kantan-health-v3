import { notification } from 'antd';
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import React from 'react';

interface ProcessState {
  currentStep: number;
  steps: string[];
  completed: boolean;
  failed: boolean;
}

// Create a simple notification system that works with antd
export const showReprocessNotification = (
  providerName: string, 
  processId?: number
) => {
  console.log('🔔 showReprocessNotification called with:', { providerName, processId });
  
  const key = `reprocess-${Date.now()}`;
  console.log('🔔 Notification key:', key);
  
  const steps = [
    'Initializing pipeline...',
    'Processing Google Places data...',
    'Geocoding locations...',
    'Generating AI content...',
    'Preparing for WordPress sync...',
    'Pipeline completed successfully!'
  ];

  let currentStep = 0;

  const updateNotification = () => {
    try {
      console.log('🔔 updateNotification called, step:', currentStep, 'of', steps.length);
      const progress = ((currentStep + 1) / steps.length) * 100;
      const isCompleted = currentStep >= steps.length - 1;

      if (isCompleted) {
        console.log('🔔 Showing completion notification');
        // Show completion notification
        notification.open({
        key,
        message: `✅ ${providerName} Reprocessing Complete`,
        description: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <span>Processing completed successfully!</span>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <button
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  background: 'white',
                  cursor: 'pointer'
                }}
                onClick={() => {
                  window.location.href = '/pipeline-failures';
                }}
              >
                View Results
              </button>
              <button
                style={{
                  padding: '4px 8px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  background: 'white',
                  cursor: 'pointer'
                }}
                onClick={() => notification.destroy(key)}
              >
                Dismiss
              </button>
            </div>
          </div>
        ),
        duration: 0,
        placement: 'topRight',
        style: { width: '400px' },
        closable: true
      });
      } else {
        console.log('🔔 Showing progress notification for step:', steps[currentStep]);
        // Show progress notification
        notification.open({
        key,
        message: `Reprocessing ${providerName}`,
        description: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <LoadingOutlined style={{ color: '#1890ff' }} />
              <span>{steps[currentStep]}</span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: '#f0f0f0',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: '#1890ff',
                transition: 'width 0.3s ease'
              }} />
            </div>
            {processId && (
              <div style={{ fontSize: '12px', color: '#666' }}>
                Process ID: {processId}
              </div>
            )}
          </div>
        ),
        duration: 0,
        placement: 'topRight',
        style: { width: '400px' },
        closable: true
      });

        // Schedule next step
        currentStep++;
        if (currentStep < steps.length) {
          setTimeout(updateNotification, 2000);
        }
      }
    } catch (error) {
      console.error('🔔 Error in updateNotification:', error);
    }
  };

  try {
    console.log('🔔 Starting notification sequence');
    // Start the progress
    updateNotification();
  } catch (error) {
    console.error('🔔 Error starting notification:', error);
  }
};

export const showRetryNotification = (
  stepName: string,
  providerName: string,
  processId?: number
) => {
  const key = `retry-${Date.now()}`;
  
  notification.open({
    key,
    message: `Retrying ${stepName}`,
    description: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <LoadingOutlined style={{ color: '#1890ff' }} />
          <span>Retrying failed step for {providerName}</span>
        </div>
        {processId && (
          <div style={{ fontSize: '12px', color: '#666' }}>
            Process ID: {processId}
          </div>
        )}
      </div>
    ),
    duration: 5,
    placement: 'topRight',
    style: { width: '400px' },
    closable: true
  });
};

export const showBulkRetryNotification = (
  providerCount: number,
  processId?: number
) => {
  const key = `bulk-retry-${Date.now()}`;
  
  notification.open({
    key,
    message: `Bulk Retry Started`,
    description: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <LoadingOutlined style={{ color: '#1890ff' }} />
          <span>Processing {providerCount} providers</span>
        </div>
        {processId && (
          <div style={{ fontSize: '12px', color: '#666' }}>
            Process ID: {processId}
          </div>
        )}
      </div>
    ),
    duration: 0,
    placement: 'topRight',
    style: { width: '400px' },
    closable: true
  });
};