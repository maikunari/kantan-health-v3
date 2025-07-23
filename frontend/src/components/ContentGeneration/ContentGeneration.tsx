import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Select,
  Typography,
  Progress,
  Alert,
  Space,
  Statistic,
  Tag,
  Form,
  InputNumber,
  Switch,
  message,
  Badge,
  Divider,
  Spin,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  FileTextOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { ContentGenerationStatus } from '../../types';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';

const { Title, Text } = Typography;
const { Option } = Select;

const ContentGeneration: React.FC = () => {
  const [form] = Form.useForm();
  const [status, setStatus] = useState<ContentGenerationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      setRefreshing(true);
      const response = await api.get(API_ENDPOINTS.CONTENT_BATCH_STATUS);
      setStatus(response.data);
      // Update generating state based on batch_running status
      if (response.data.batch_running) {
        setGenerating(true);
      } else {
        setGenerating(false);
      }
    } catch (error: any) {
      console.error('Failed to fetch content generation status:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleStartGeneration = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      console.log('Starting content generation with values:', values);
      
      const response = await api.post(API_ENDPOINTS.CONTENT_GENERATE, {
        limit: values.limit || 10,
        status: values.status || '',
        content_types: values.content_types || ['all'],
        dry_run: values.dry_run || false,
      });
      
      console.log('Content generation response:', response.data);
      
      // Check if it's a status filter mismatch
      if (response.data.status_filter_mismatch) {
        message.warning(response.data.message);
      } else if (response.data.full_output) {
        // Test mode - show detailed output
        message.info('Test mode complete - check console for details');
        console.log('Full output:', response.data.full_output);
      } else {
        message.success(response.data.message || 'Content generation started successfully');
        setGenerating(true);
        // Immediately fetch status to update UI
        setTimeout(fetchStatus, 1000);
      }
    } catch (error: any) {
      console.error('Content generation error:', error);
      const errorData = error.response?.data;
      
      if (errorData?.stdout || errorData?.stderr) {
        // Show detailed error information
        message.error('Content generation failed - check console for details');
        console.error('Command:', errorData.command);
        console.error('Working dir:', errorData.working_dir);
        console.error('Stdout:', errorData.stdout);
        console.error('Stderr:', errorData.stderr);
      } else {
        message.error(errorData?.error || 'Failed to start content generation');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!status) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading content generation status...</div>
      </div>
    );
  }

  const completionRate = status.content_stats.total_approved > 0 
    ? (status.content_stats.fully_complete / status.content_stats.total_approved) * 100 
    : 0;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>AI Content Generation</Title>
        <Text type="secondary">Manage AI-powered content generation for healthcare providers</Text>
      </div>

      {/* Status Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Approved"
              value={status.content_stats.total_approved}
              prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Fully Complete"
              value={status.content_stats.fully_complete}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Pending Content"
              value={status.content_stats.pending_content}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <RobotOutlined style={{ color: '#722ed1', marginRight: 8 }} />
              <Text strong>Batch Status</Text>
              {refreshing && <Spin size="small" style={{ marginLeft: 8 }} />}
            </div>
            <Badge
              status={status.batch_running ? 'processing' : 'default'}
              text={status.batch_running ? 'Running' : 'Idle'}
            />
          </Card>
        </Col>
      </Row>

      {/* Progress Overview */}
      <Card title="Content Generation Progress" style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text strong>Overall Completion</Text>
            <Text>{Math.round(completionRate)}%</Text>
          </div>
          <Progress 
            percent={completionRate}
            status={completionRate === 100 ? 'success' : 'active'}
            strokeColor="#52c41a"
          />
        </div>

        <Row gutter={16}>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">Descriptions</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1890ff' }}>
                {status.content_stats.with_description}
              </div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">Experience</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#52c41a' }}>
                {status.content_stats.with_experience}
              </div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">Reviews</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#faad14' }}>
                {status.content_stats.with_reviews}
              </div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">SEO Content</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#722ed1' }}>
                {status.content_stats.with_seo}
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Control Panel */}
      <Card title="Generation Control Panel">
        {(status.batch_running || generating) && (
          <Alert
            message="Content Generation in Progress"
            description={
              <div>
                <div>The AI batch processor is currently generating content. New requests will be queued.</div>
                <div style={{ marginTop: 8 }}>
                  <Spin size="small" style={{ marginRight: 8 }} />
                  <Text type="secondary">Processing providers...</Text>
                </div>
              </div>
            }
            type="info"
            showIcon
            icon={<ThunderboltOutlined spin />}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item 
                label="Provider Status (Info Only)" 
                name="status"
                initialValue=""
                help="Note: Content is generated for ANY provider missing content, regardless of status"
              >
                <Select>
                  <Option value="">All Statuses</Option>
                  <Option value="approved">Show Approved Count</Option>
                  <Option value="pending">Show Pending Count</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item 
                label="Batch Limit" 
                name="limit"
                initialValue={20}
              >
                <InputNumber 
                  min={1} 
                  max={100} 
                  style={{ width: '100%' }}
                  placeholder="Number of providers to process"
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item 
                label="Content Types" 
                name="content_types"
                initialValue={['all']}
              >
                <Select mode="multiple">
                  <Option value="all">All Content Types</Option>
                  <Option value="description">Descriptions</Option>
                  <Option value="experience">English Experience</Option>
                  <Option value="reviews">Review Summaries</Option>
                  <Option value="seo">SEO Content</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="dry_run" valuePropName="checked">
                <Switch /> 
                <Text style={{ marginLeft: 8 }}>Dry Run (Preview Only)</Text>
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleStartGeneration}
              loading={loading}
              disabled={status.batch_running || generating}
              size="large"
            >
              {loading ? 'Starting...' : 'Start Generation'}
            </Button>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchStatus}
              loading={refreshing}
            >
              Refresh Status
            </Button>

            <Button
              icon={<PauseCircleOutlined />}
              disabled={!status.batch_running && !generating}
              danger
            >
              Stop Generation
            </Button>
          </Space>
        </Form>

        <Divider />

        {/* Quick Actions */}
        <div>
          <Text strong style={{ marginBottom: 16, display: 'block' }}>Quick Actions</Text>
          <Space wrap>
            <Button 
              size="small"
              onClick={() => {
                message.info('Note: The content generator always creates ALL missing content types together for efficiency.');
                handleStartGeneration();
              }}
              disabled={status.batch_running || generating || loading}
            >
              Generate All Missing Content
            </Button>
            <Button 
              size="small"
              onClick={() => {
                form.setFieldsValue({ limit: 50 });
                handleStartGeneration();
              }}
              disabled={status.batch_running || generating || loading}
            >
              Process 50 Providers
            </Button>
            <Button 
              size="small"
              onClick={() => {
                form.setFieldsValue({ limit: 100 });
                handleStartGeneration();
              }}
              disabled={status.batch_running || generating || loading}
            >
              Process 100 Providers
            </Button>
            <Button 
              size="small"
              onClick={() => {
                form.setFieldsValue({ dry_run: true });
                handleStartGeneration();
              }}
              disabled={status.batch_running || generating || loading}
            >
              Preview (Dry Run)
            </Button>
            <Button 
              size="small"
              type="dashed"
              onClick={async () => {
                try {
                  const response = await api.get(API_ENDPOINTS.CONTENT_CHECK_PROVIDERS);
                  message.info(`Found ${response.data.providers_needing_content} providers needing content out of ${response.data.total_providers} total`);
                  console.log('Providers needing content:', response.data);
                  
                  // Show sample providers in console
                  if (response.data.sample_providers?.length > 0) {
                    console.log('Sample providers missing content:');
                    response.data.sample_providers.forEach((p: any) => {
                      console.log(`- ${p.name} (ID: ${p.id}, Status: ${p.status})`);
                      console.log(`  Has description: ${p.has_description}, Has SEO: ${p.has_seo_title}, Has image: ${p.has_featured_image}`);
                    });
                  }
                } catch (error: any) {
                  console.error('Check providers error:', error);
                  message.error('Failed to check providers');
                }
              }}
              disabled={loading}
            >
              Check Providers
            </Button>
            <Button 
              size="small"
              type="primary"
              onClick={async () => {
                try {
                  // Run a test with just 1 provider
                  const response = await api.post(API_ENDPOINTS.CONTENT_GENERATE, {
                    limit: 1,
                    test_mode: true
                  });
                  console.log('Test generation response:', response.data);
                  if (response.data.full_output) {
                    console.log('Full output:', response.data.full_output);
                  }
                  message.info('Test complete - check console for output');
                } catch (error: any) {
                  console.error('Test generation error:', error);
                  message.error('Test failed - check console');
                }
              }}
              disabled={loading}
            >
              Test 1 Provider
            </Button>
          </Space>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card 
        title="Recent Activity" 
        style={{ marginTop: 16 }}
        extra={
          <Space>
            {(status.batch_running || generating) && (
              <Badge status="processing" text="Generating" />
            )}
            <Tag color="processing">
              Last updated: {new Date().toLocaleTimeString()}
            </Tag>
          </Space>
        }
      >
        <div style={{ minHeight: 100 }}>
          {generating || status.batch_running ? (
            <div>
              <Alert
                message="Generation Started"
                description={`Processing up to ${form.getFieldValue('limit') || 20} providers that need content...`}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Text type="secondary">
                Check the console or run `ps aux | grep run_mega_batch` to monitor progress.
              </Text>
            </div>
          ) : (
            <Text type="secondary">
              Content generation activity will appear here when processing starts...
            </Text>
          )}
        </div>
      </Card>
    </div>
  );
};

export default ContentGeneration;