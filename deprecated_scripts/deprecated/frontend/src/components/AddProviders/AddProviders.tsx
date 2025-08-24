import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Select,
  Typography,
  Space,
  Alert,
  Switch,
  InputNumber,
  Row,
  Col,
  Tag,
  message,
  Progress,
  Table,
  Timeline,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EnvironmentOutlined,
  MedicineBoxOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';
import { Provider } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

interface AddResult {
  success: boolean;
  message: string;
  provider_id?: number;
  details?: any;
  recent_providers?: Provider[];
  providers_added?: number;
  pipeline_results?: any;
  pipeline_summary?: any;
}

interface PipelineStatus {
  run_id: string;
  run_type: string;
  status: string;
  started_at: string;
  completed_at?: string;
  progress: {
    percentage: number;
    total_providers: number;
    completed_providers: number;
    failed_providers: number;
    steps_breakdown: Record<string, { success: number; failed: number; pending: number }>;
  };
  recent_activity: Array<{
    provider_name: string;
    step_name: string;
    status: string;
    error_message?: string;
    created_at: string;
  }>;
}

const AddProviders: React.FC = () => {
  const [specificForm] = Form.useForm();
  const [geographicForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AddResult[]>([]);
  const [progress, setProgress] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [pipelineRunId, setPipelineRunId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('geographic');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'green';
      case 'rejected': return 'red';
      case 'pending': return 'orange';
      case 'success': return 'green';
      case 'failed': return 'red';
      case 'running': return 'blue';
      default: return 'default';
    }
  };

  const getProficiencyColor = (score: number) => {
    if (score >= 4) return 'green';
    if (score === 3) return 'orange';
    return 'red';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid Date';
    }
  };

  // Poll pipeline status
  useEffect(() => {
    if (!pipelineRunId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/api/pipeline/status/${pipelineRunId}`);
        setPipelineStatus(response.data);
        
        // Stop polling if pipeline is completed or failed
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling pipeline status:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [pipelineRunId]);

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const providerColumns = [
    {
      title: 'Provider Name',
      dataIndex: 'provider_name',
      key: 'provider_name',
      width: 200,
      ellipsis: true,
      render: (text: string, record: Provider) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            ID: {record.id}
          </Text>
        </div>
      ),
    },
    {
      title: 'Location',
      key: 'location',
      width: 150,
      render: (_: any, record: Provider) => (
        <div>
          <div>{record.city}</div>
          {record.ward && <Text type="secondary">{record.ward}</Text>}
        </div>
      ),
    },
    {
      title: 'Specialties',
      dataIndex: 'specialties',
      key: 'specialties',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'English Proficiency',
      key: 'proficiency',
      width: 120,
      render: (_: any, record: Provider) => (
        <Tag color={getProficiencyColor(record.english_proficiency_score)}>
          Score {record.english_proficiency_score}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'AI Content',
      key: 'ai_content',
      width: 100,
      render: (_: any, record: Provider) => {
        const hasContent = !!(record.ai_description && record.seo_title);
        return (
          <Tag color={hasContent ? 'green' : 'orange'}>
            {hasContent ? 'Generated' : 'Pending'}
          </Tag>
        );
      },
    },
    {
      title: 'WordPress',
      key: 'wordpress',
      width: 100,
      render: (_: any, record: Provider) => {
        const isSynced = !!record.wordpress_id;
        return (
          <Tag color={isSynced ? 'green' : 'orange'}>
            {isSynced ? 'Synced' : 'Pending'}
          </Tag>
        );
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (dateString: string) => (
        <div style={{ fontSize: '12px' }}>{formatDate(dateString)}</div>
      ),
    },
  ];

  const handleAddSpecific = async (values: any) => {
    setLoading(true);
    setResults([]);
    
    try {
      const payload = {
        ...values,
        full_pipeline: !values.skip_content_generation && !values.skip_wordpress_sync,
        skip_content_generation: values.skip_content_generation || false,
        skip_wordpress_sync: values.skip_wordpress_sync || false,
        dry_run: values.dry_run || false,
      };

      const response = await api.post(API_ENDPOINTS.ADD_SPECIFIC_PROVIDER, payload);
      
      const result = {
        success: true,
        message: response.data.message,
        provider_id: response.data.provider_id,
        details: response.data.details,
        recent_providers: response.data.recent_providers || [],
        providers_added: response.data.providers_added || 0,
        pipeline_results: response.data.pipeline_results,
      };
      setResults([result]);
      
      // Start tracking pipeline if run_id is available
      if (response.data.pipeline_results?.run_id) {
        setPipelineRunId(response.data.pipeline_results.run_id);
      }
      
      message.success('Provider added successfully!');
      if (!values.dry_run) {
        specificForm.resetFields();
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to add provider';
      setResults([{
        success: false,
        message: errorMsg,
      }]);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleAddGeographic = async (values: any) => {
    setLoading(true);
    setResults([]);
    setProgress(0);
    
    try {
      const payload = {
        ...values,
        full_pipeline: !values.skip_content_generation && !values.skip_wordpress_sync,
        skip_content_generation: values.skip_content_generation || false,
        skip_wordpress_sync: values.skip_wordpress_sync || false,
        dry_run: values.dry_run || false,
      };

      // For geographic addition, we'll need to implement progress tracking
      const response = await api.post(API_ENDPOINTS.ADD_GEOGRAPHIC_PROVIDERS, payload);
      
      const result = {
        success: true,
        message: response.data.message,
        details: response.data.details,
        recent_providers: response.data.recent_providers || [],
        providers_added: response.data.providers_added || 0,
        pipeline_summary: response.data.pipeline_summary,
      };
      setResults([result]);
      
      // Start tracking pipeline if run_id is available
      if (response.data.pipeline_summary?.run_id) {
        setPipelineRunId(response.data.pipeline_summary.run_id);
      }
      
      message.success('Geographic provider search completed!');
      if (!values.dry_run) {
        geographicForm.resetFields();
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to add providers';
      setResults([{
        success: false,
        message: errorMsg,
      }]);
      message.error(errorMsg);
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Add Healthcare Providers</Title>
        <Paragraph>
          Add individual providers or bulk add by geographic area. The system automatically runs 
          the complete pipeline: <Tag>Google Places Discovery</Tag> → <Tag>AI Content Generation</Tag> → <Tag>WordPress Sync</Tag>
        </Paragraph>
      </div>

      <Tabs defaultActiveKey="geographic" size="large" onChange={setActiveTab}>
        {/* Add Geographic Providers Tab */}
        <TabPane 
          tab={
            <span>
              <EnvironmentOutlined />
              Add by Geographic Area
            </span>
          } 
          key="geographic"
        >
          <Card>
            <Form
              form={geographicForm}
              layout="vertical"
              onFinish={handleAddGeographic}
              initialValues={{
                limit: 10,
                skip_content_generation: false,
                skip_wordpress_sync: false,
                dry_run: false,
              }}
            >
              <Alert
                message="Bulk Add Providers by Geographic Area"
                description="Add multiple providers from specific cities, wards, or regions. Automatically finds healthcare providers in the specified areas."
                type="info"
                style={{ marginBottom: 24 }}
                showIcon
              />

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="City" name="city">
                    <Select 
                      placeholder="Select city"
                      mode="multiple"
                      allowClear
                    >
                      <Option value="Tokyo">Tokyo</Option>
                      <Option value="Osaka">Osaka</Option>
                      <Option value="Yokohama">Yokohama</Option>
                      <Option value="Kyoto">Kyoto</Option>
                      <Option value="Kobe">Kobe</Option>
                      <Option value="Nagoya">Nagoya</Option>
                      <Option value="Fukuoka">Fukuoka</Option>
                      <Option value="Sendai">Sendai</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Tokyo Wards (if Tokyo selected)" name="wards">
                    <Select 
                      placeholder="Select wards (optional)"
                      mode="multiple"
                      allowClear
                    >
                      <Option value="Shibuya">Shibuya</Option>
                      <Option value="Shinjuku">Shinjuku</Option>
                      <Option value="Minato">Minato</Option>
                      <Option value="Chiyoda">Chiyoda</Option>
                      <Option value="Ginza">Ginza</Option>
                      <Option value="Harajuku">Harajuku</Option>
                      <Option value="Roppongi">Roppongi</Option>
                      <Option value="Akihabara">Akihabara</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Provider Limit" name="limit">
                    <InputNumber 
                      min={1} 
                      max={50} 
                      placeholder="10"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Specialty Filter" name="specialty">
                    <Select placeholder="Filter by specialty (optional)">
                      <Option value="general">General Medicine</Option>
                      <Option value="cardiology">Cardiology</Option>
                      <Option value="dermatology">Dermatology</Option>
                      <Option value="gynecology">Gynecology</Option>
                      <Option value="pediatrics">Pediatrics</Option>
                      <Option value="psychiatry">Psychiatry</Option>
                      <Option value="dentistry">Dentistry</Option>
                      <Option value="ophthalmology">Ophthalmology</Option>
                      <Option value="orthopedics">Orthopedics</Option>
                      <Option value="ent">ENT</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Pipeline Options">
                    <Space direction="vertical">
                      <div>
                        <Form.Item name="skip_content_generation" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Skip AI Content Generation</Text>
                      </div>
                      
                      <div>
                        <Form.Item name="skip_wordpress_sync" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Skip WordPress Sync</Text>
                      </div>
                      
                      <div>
                        <Form.Item name="dry_run" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Dry Run (Preview Only)</Text>
                      </div>
                    </Space>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  icon={<PlayCircleOutlined />}
                  size="large"
                >
                  Start Geographic Search
                </Button>
              </Form.Item>
            </Form>

            {progress > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text>Progress:</Text>
                <Progress percent={progress} status="active" />
              </div>
            )}
          </Card>
        </TabPane>

        {/* Add Specific Provider Tab */}
        <TabPane 
          tab={
            <span>
              <MedicineBoxOutlined />
              Add Specific Provider
            </span>
          } 
          key="specific"
        >
          <Card>
            <Form
              form={specificForm}
              layout="vertical"
              onFinish={handleAddSpecific}
              initialValues={{
                skip_content_generation: false,
                skip_wordpress_sync: false,
                dry_run: false,
              }}
            >
              <Alert
                message="Add Individual Healthcare Provider"
                description="Add a specific provider by Google Place ID (most reliable) or by name and location search."
                type="info"
                style={{ marginBottom: 24 }}
                showIcon
              />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Google Place ID"
                    name="place_id"
                    help="Most reliable method. Format: ChIJN1t_tDeuEmsRUsoyG83frY4"
                  >
                    <Input 
                      placeholder="ChIJN1t_tDeuEmsRUsoyG83frY4" 
                      prefix={<SearchOutlined />}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="OR Provider Name" name="name">
                    <Input 
                      placeholder="Tokyo Medical Center" 
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Location (City)" name="location">
                    <Input 
                      placeholder="Tokyo" 
                      prefix={<EnvironmentOutlined />}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item label="Pipeline Options">
                    <Space direction="vertical">
                      <div>
                        <Form.Item name="skip_content_generation" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Skip AI Content Generation</Text>
                      </div>
                      
                      <div>
                        <Form.Item name="skip_wordpress_sync" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Skip WordPress Sync</Text>
                      </div>
                      
                      <div>
                        <Form.Item name="dry_run" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Dry Run (Preview Only)</Text>
                      </div>
                    </Space>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  icon={<PlusOutlined />}
                  size="large"
                >
                  Add Provider
                </Button>
              </Form.Item>
            </Form>

            {progress > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text>Progress:</Text>
                <Progress percent={progress} status="active" />
              </div>
            )}
          </Card>
        </TabPane>
      </Tabs>

      {/* Pipeline Progress Section */}
      {pipelineStatus && (
        <Card 
          title="Pipeline Progress" 
          style={{ marginTop: 24, marginBottom: 16 }}
          extra={
            <Tag color={getStatusColor(pipelineStatus.status)}>
              {pipelineStatus.status.toUpperCase()}
            </Tag>
          }
        >
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Progress 
                percent={pipelineStatus.progress.percentage} 
                status={pipelineStatus.status === 'failed' ? 'exception' : 'active'}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </Col>
            
            <Col xs={24} sm={8}>
              <Statistic
                title="Total Providers"
                value={pipelineStatus.progress.total_providers}
                prefix={<MedicineBoxOutlined />}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title="Completed"
                value={pipelineStatus.progress.completed_providers}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title="Failed"
                value={pipelineStatus.progress.failed_providers}
                valueStyle={{ color: '#cf1322' }}
                prefix={<CloseCircleOutlined />}
              />
            </Col>
          </Row>

          {/* Steps Breakdown */}
          {Object.keys(pipelineStatus.progress.steps_breakdown).length > 0 && (
            <div style={{ marginTop: 24 }}>
              <Title level={5}>Pipeline Steps Progress</Title>
              <Row gutter={[16, 16]}>
                {Object.entries(pipelineStatus.progress.steps_breakdown).map(([step, counts]) => (
                  <Col xs={24} sm={12} md={6} key={step}>
                    <Card size="small">
                      <Text strong>{step.replace('_', ' ').toUpperCase()}</Text>
                      <div style={{ marginTop: 8 }}>
                        <Space size="small">
                          <Tag color="green">{counts.success} ✓</Tag>
                          <Tag color="red">{counts.failed} ✗</Tag>
                          <Tag>{counts.pending} ⏳</Tag>
                        </Space>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          )}

          {/* Recent Activity Timeline */}
          {pipelineStatus.recent_activity.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <Title level={5}>Recent Activity</Title>
              <Timeline>
                {pipelineStatus.recent_activity.slice(0, 5).map((activity, index) => (
                  <Timeline.Item
                    key={index}
                    dot={getStepIcon(activity.status)}
                    color={getStatusColor(activity.status)}
                  >
                    <Space direction="vertical" size="small">
                      <Text strong>{activity.provider_name}</Text>
                      <Space>
                        <Tag>{activity.step_name.replace('_', ' ')}</Tag>
                        <Text type="secondary">{formatDate(activity.created_at)}</Text>
                      </Space>
                      {activity.error_message && (
                        <Text type="danger" style={{ fontSize: '12px' }}>
                          {activity.error_message}
                        </Text>
                      )}
                    </Space>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>
          )}
        </Card>
      )}

      {/* Results Section */}
      {results.length > 0 && (
        <div style={{ marginTop: 24 }}>
          {results.map((result, index) => (
            <div key={index}>
              {/* Success/Error Alert */}
              <Card title="Operation Results" style={{ marginBottom: 16 }}>
                <Alert
                  message={result.success ? 'Success' : 'Error'}
                  description={
                    <div>
                      <div>{result.message}</div>
                      {result.providers_added !== undefined && (
                        <div style={{ marginTop: 8 }}>
                          <Tag color="blue">Providers Added: {result.providers_added}</Tag>
                          {result.pipeline_results && (
                            <>
                              <Tag color={result.pipeline_results.ai_content_success ? 'green' : 'red'}>
                                AI Content: {result.pipeline_results.ai_content_success ? 'Success' : 'Failed'}
                              </Tag>
                              <Tag color={result.pipeline_results.wordpress_sync_success ? 'green' : 'red'}>
                                WordPress: {result.pipeline_results.wordpress_sync_success ? 'Success' : 'Failed'}
                              </Tag>
                            </>
                          )}
                          {result.pipeline_summary && (
                            <>
                              <Tag color="green">
                                AI Generated: {result.pipeline_summary.ai_success_count}/{result.pipeline_summary.total_processed}
                              </Tag>
                              <Tag color="green">
                                WordPress Synced: {result.pipeline_summary.wp_success_count}/{result.pipeline_summary.total_processed}
                              </Tag>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  }
                  type={result.success ? 'success' : 'error'}
                  showIcon
                />
              </Card>

              {/* Recently Added Providers Table */}
              {result.recent_providers && result.recent_providers.length > 0 && (
                <Card 
                  title={
                    <div>
                      <span>Recently Added Providers</span>
                      <Tag color="blue" style={{ marginLeft: 8 }}>
                        {result.recent_providers.length} provider{result.recent_providers.length !== 1 ? 's' : ''}
                      </Tag>
                    </div>
                  }
                >
                  <Table
                    columns={providerColumns}
                    dataSource={result.recent_providers}
                    rowKey="id"
                    pagination={false}
                    scroll={{ x: 1200 }}
                    size="small"
                  />
                </Card>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AddProviders;