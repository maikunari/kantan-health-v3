import React, { useEffect, useState } from 'react';
import { notification, Progress, Button, Space, Typography } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  EyeOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Text } = Typography;

interface ProcessNotificationProps {
  type: 'reprocess' | 'retry' | 'bulk_retry';
  providerName?: string;
  providerCount?: number;
  processId?: number;
  onClose?: () => void;
}

interface ProcessStatus {
  isRunning: boolean;
  progress: number;
  currentStep: string;
  completed: boolean;
  failed: boolean;
  error?: string;
}

const ProcessNotification: React.FC<ProcessNotificationProps> = ({
  type,
  providerName,
  providerCount = 1,
  processId,
  onClose
}) => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<ProcessStatus>({
    isRunning: true,
    progress: 0,
    currentStep: 'Initializing...',
    completed: false,
    failed: false
  });

  // Mock progress simulation (in real implementation, this would poll the backend)
  useEffect(() => {
    if (!status.isRunning) return;

    const steps = [
      'Initializing pipeline...',
      'Processing Google Places data...',
      'Geocoding locations...',
      'Generating AI content...',
      'Preparing for WordPress sync...',
      'Pipeline completed!'
    ];

    let stepIndex = 0;
    const interval = setInterval(() => {
      if (stepIndex < steps.length - 1) {
        setStatus(prev => ({
          ...prev,
          progress: ((stepIndex + 1) / steps.length) * 100,
          currentStep: steps[stepIndex + 1]
        }));
        stepIndex++;
      } else {
        setStatus(prev => ({
          ...prev,
          isRunning: false,
          completed: true,
          progress: 100,
          currentStep: 'Pipeline completed successfully!'
        }));
        clearInterval(interval);
      }
    }, 2000); // 2 seconds per step

    return () => clearInterval(interval);
  }, [status.isRunning]);


  const getDescription = () => {
    if (status.completed) {
      return (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Text type="success">
            <CheckCircleOutlined /> Processing completed successfully!
          </Text>
          <Space>
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => navigate('/pipeline-failures')}
            >
              View Results
            </Button>
            <Button 
              type="link" 
              icon={<CloseOutlined />} 
              size="small"
              onClick={onClose}
            >
              Dismiss
            </Button>
          </Space>
        </Space>
      );
    }

    if (status.failed) {
      return (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Text type="danger">
            <CloseCircleOutlined /> Processing failed
          </Text>
          {status.error && <Text type="secondary">{status.error}</Text>}
          <Space>
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => navigate('/pipeline-failures')}
            >
              View Failures
            </Button>
            <Button 
              type="link" 
              icon={<CloseOutlined />} 
              size="small"
              onClick={onClose}
            >
              Dismiss
            </Button>
          </Space>
        </Space>
      );
    }

    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <Space align="center">
          <LoadingOutlined />
          <Text>{status.currentStep}</Text>
        </Space>
        <Progress 
          percent={Math.round(status.progress)} 
          size="small" 
          status={status.isRunning ? 'active' : 'success'}
        />
        {processId && (
          <Text type="secondary" style={{ fontSize: '12px' }}>
            Process ID: {processId}
          </Text>
        )}
      </Space>
    );
  };

  return getDescription(); // Return the actual notification content
};

// Utility functions to show notifications
export const showReprocessNotification = (
  providerName: string, 
  processId?: number
) => {
  const key = `reprocess-${Date.now()}`;
  
  notification.open({
    key,
    message: `Reprocessing ${providerName}`,
    description: (
      <ProcessNotification
        type="reprocess"
        providerName={providerName}
        processId={processId}
        onClose={() => notification.destroy(key)}
      />
    ),
    duration: 0, // Keep open until manually closed
    placement: 'topRight',
    style: { width: '400px' },
    closable: true
  });
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
      <ProcessNotification
        type="retry"
        providerName={providerName}
        processId={processId}
        onClose={() => notification.destroy(key)}
      />
    ),
    duration: 0,
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
      <ProcessNotification
        type="bulk_retry"
        providerCount={providerCount}
        processId={processId}
        onClose={() => notification.destroy(key)}
      />
    ),
    duration: 0,
    placement: 'topRight',
    style: { width: '400px' },
    closable: true
  });
};

export default ProcessNotification;