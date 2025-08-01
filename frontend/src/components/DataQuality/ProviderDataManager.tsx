import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Alert,
  Tag,
  Progress,
  message,
} from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  RobotOutlined,
  EnvironmentOutlined,
  GlobalOutlined,
  BugOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { Provider } from '../../types';
import { calculateGroupCompleteness, COMPLETENESS_FIELD_GROUPS, getCompletenessColor } from '../../utils/completeness';
import { API_BASE_URL, API_ENDPOINTS } from '../../config/api';
import { showReprocessNotification } from '../Notifications/SimpleProcessNotification';

const { Text, Title } = Typography;

interface ProviderDataManagerProps {
  provider: Provider;
  onUpdate?: () => void;
}

const ProviderDataManager: React.FC<ProviderDataManagerProps> = ({ provider, onUpdate }) => {
  const navigate = useNavigate();
  const [reprocessing, setReprocessing] = useState(false);

  const fieldGroups = [
    {
      key: 'location',
      title: 'Location Data',
      icon: <EnvironmentOutlined />,
      hasData: provider.latitude && provider.longitude,
    },
    {
      key: 'google_data',
      title: 'Google Places Data',
      icon: <GlobalOutlined />,
      hasData: provider.business_hours && provider.rating,
    },
    {
      key: 'content',
      title: 'AI Generated Content',
      icon: <RobotOutlined />,
      hasData: provider.ai_description && provider.seo_title && provider.featured_image_url,
    },
  ];

  const locationCompleteness = calculateGroupCompleteness(provider, 'location');
  const contactCompleteness = calculateGroupCompleteness(provider, 'contact');
  const contentCompleteness = calculateGroupCompleteness(provider, 'content');
  
  const overallCompleteness = Math.round(
    (locationCompleteness.percentage + contactCompleteness.percentage + contentCompleteness.percentage) / 3
  );

  const missingData = fieldGroups.filter(group => !group.hasData);
  
  console.log('📊 ProviderDataManager rendered for provider:', provider.provider_name);
  console.log('📊 Provider missing data:', missingData.map(g => g.title));

  const handleReprocessProvider = async () => {
    console.log('🔄 Reprocess Provider clicked for:', provider.provider_name);
    console.log('🔄 Provider ID:', provider.id);
    console.log('🔄 API URL:', `${API_BASE_URL}${API_ENDPOINTS.PIPELINE_PROVIDERS_REPROCESS}`);
    
    setReprocessing(true);
    try {
      // Trigger the enhanced pipeline for this specific provider
      const requestBody = {
        provider_ids: [provider.id]
      };
      console.log('🔄 Request body:', requestBody);
      
      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PIPELINE_PROVIDERS_REPROCESS}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      console.log('🔄 Response status:', response.status);
      const data = await response.json();
      console.log('🔄 Response data:', data);

      if (data.success) {
        console.log('🎯 About to show notification for:', provider.provider_name);
        console.log('🎯 Process ID:', data.process_id);
        
        // Show rich notification with progress tracking
        showReprocessNotification(provider.provider_name, data.process_id);
        
        console.log('🎯 Notification function called');
        
        // Call onUpdate after a brief delay to allow the pipeline to start
        if (onUpdate) {
          setTimeout(() => onUpdate(), 1000);
        }
      } else {
        console.log('❌ API call failed:', data.error);
        message.error(`Failed to start pipeline: ${data.error}`);
      }
    } catch (error) {
      console.error('❌ Error reprocessing provider:', error);
      message.error('Failed to start provider reprocessing');
    } finally {
      setReprocessing(false);
    }
  };

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={4}>Data Completeness</Title>
          <Progress
            percent={overallCompleteness}
            strokeColor={getCompletenessColor(overallCompleteness)}
            format={percent => `${percent}% Complete`}
          />
        </div>

        <Row gutter={16}>
          {fieldGroups.map(group => (
            <Col span={8} key={group.key}>
              <Card size="small">
                <Space direction="vertical" size="small" style={{ width: '100%', textAlign: 'center' }}>
                  {group.icon}
                  <Text strong>{group.title}</Text>
                  {group.hasData ? (
                    <Tag color="green" icon={<CheckCircleOutlined />}>Complete</Tag>
                  ) : (
                    <Tag color="orange" icon={<ExclamationCircleOutlined />}>Missing</Tag>
                  )}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>

        {missingData.length > 0 && (
          <Alert
            message="Data Generation Has Been Streamlined"
            description={
              <div>
                <p>Individual field regeneration has been replaced with a comprehensive pipeline system that handles all provider data processing automatically.</p>
                <p><strong>Missing data for this provider:</strong> {missingData.map(g => g.title.toLowerCase()).join(', ')}</p>
              </div>
            }
            type="info"
            showIcon
            action={
              <Space direction="vertical" size="small">
                <Button 
                  type="primary" 
                  icon={<BugOutlined />}
                  onClick={() => navigate('/pipeline-failures')}
                >
                  Check Pipeline Failures
                </Button>
                <Button 
                  type="default" 
                  icon={<ReloadOutlined />}
                  loading={reprocessing}
                  onClick={handleReprocessProvider}
                >
                  Re-process Provider
                </Button>
              </Space>
            }
          />
        )}

        {missingData.length === 0 && (
          <Alert
            message="Provider Data Complete"
            description="This provider has all required data fields. You can sync it to WordPress when ready."
            type="success"
            showIcon
          />
        )}

        <div style={{ background: '#f6ffed', padding: '16px', borderRadius: '6px', border: '1px solid #b7eb8f' }}>
          <Title level={5} style={{ color: '#52c41a', marginBottom: '8px' }}>
            ✅ New Streamlined Workflow
          </Title>
          <Text>
            <strong>1.</strong> Providers are automatically processed through the complete pipeline when added<br />
            <strong>2.</strong> Any failures are tracked and can be retried from the Pipeline Failures page<br />
            <strong>3.</strong> Complete providers are ready for WordPress sync
          </Text>
        </div>
      </Space>
    </Card>
  );
};

export default ProviderDataManager;