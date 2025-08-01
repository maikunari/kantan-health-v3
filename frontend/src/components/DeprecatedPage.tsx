import React from 'react';
import { Card, Button, Alert, Typography, Space } from 'antd';
import { InfoCircleOutlined, ArrowRightOutlined, BugOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph, Text } = Typography;

interface DeprecatedPageProps {
  title: string;
  description: string;
  replacementPath: string;
  replacementTitle: string;
}

const DeprecatedPage: React.FC<DeprecatedPageProps> = ({
  title,
  description,
  replacementPath,
  replacementTitle
}) => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          <InfoCircleOutlined style={{ fontSize: '64px', color: '#1890ff' }} />
          
          <Title level={2}>Page Deprecated</Title>
          
          <Alert
            message="Workflow Simplified"
            description="This page has been removed as part of streamlining the healthcare directory workflow."
            type="info"
            showIcon
          />
          
          <div>
            <Title level={4}>{title}</Title>
            <Paragraph type="secondary">
              {description}
            </Paragraph>
          </div>
          
          <div style={{ background: '#f6ffed', padding: '16px', borderRadius: '6px', border: '1px solid #b7eb8f' }}>
            <Title level={4} style={{ color: '#52c41a', marginBottom: '8px' }}>
              ✅ New Streamlined Workflow
            </Title>
            <Paragraph>
              <Text strong>1. Add Providers</Text> - Providers are automatically processed through the complete pipeline
              <br />
              <Text strong>2. Monitor Failures</Text> - Any issues are tracked and can be retried from the Pipeline Failures page
              <br />
              <Text strong>3. WordPress Sync</Text> - Ready providers are synced to WordPress
            </Paragraph>
          </div>
          
          <Space size="large">
            <Button 
              type="primary" 
              size="large"
              icon={<PlusOutlined />}
              onClick={() => navigate('/add-providers')}
            >
              Go to Add Providers
            </Button>
            
            <Button 
              size="large"
              icon={<BugOutlined />}
              onClick={() => navigate('/pipeline-failures')}
            >
              View Pipeline Failures
            </Button>
            
            <Button 
              size="large"
              icon={<ArrowRightOutlined />}
              onClick={() => navigate(replacementPath)}
            >
              {replacementTitle}
            </Button>
          </Space>
          
          <div style={{ marginTop: '32px', padding: '16px', background: '#fafafa', borderRadius: '6px' }}>
            <Text type="secondary">
              <strong>Why was this changed?</strong><br />
              We consolidated multiple content generation pages into a single, comprehensive pipeline that runs automatically when providers are added. This eliminates confusion and ensures all providers go through the complete process with proper error tracking and retry mechanisms.
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default DeprecatedPage;