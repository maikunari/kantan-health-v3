import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Table,
  Tag,
  Button,
  Select,
  Typography,
  Space,
  Statistic,
  Divider,
  Alert,
  Badge,
  message,
} from 'antd';
import {
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';
import { DataQualityOverview, DataQualityField } from '../../types';

const { Title, Text } = Typography;
const { Option } = Select;

interface MissingProvider {
  id: number;
  provider_name: string;
  city: string;
  status: string;
  missing_reason: string;
}

const DataQuality: React.FC = () => {
  const [overview, setOverview] = useState<DataQualityOverview | null>(null);
  const [missingProviders, setMissingProviders] = useState<MissingProvider[]>([]);
  const [selectedFieldType, setSelectedFieldType] = useState<string>('location');
  const [loading, setLoading] = useState(true);
  const [loadingMissing, setLoadingMissing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDataQualityOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(API_ENDPOINTS.DATA_QUALITY_OVERVIEW);
      setOverview(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load data quality overview');
    } finally {
      setLoading(false);
    }
  };

  const fetchMissingProviders = async (fieldType: string) => {
    try {
      setLoadingMissing(true);
      const response = await api.get(`${API_ENDPOINTS.DATA_QUALITY_MISSING_FIELDS}?field_type=${fieldType}&limit=100`);
      setMissingProviders(response.data.providers || []);
    } catch (err: any) {
      console.error('Failed to load missing providers:', err);
    } finally {
      setLoadingMissing(false);
    }
  };

  useEffect(() => {
    fetchDataQualityOverview();
    fetchMissingProviders(selectedFieldType);
  }, []);

  useEffect(() => {
    fetchMissingProviders(selectedFieldType);
  }, [selectedFieldType]);

  const handleRefresh = () => {
    fetchDataQualityOverview();
    fetchMissingProviders(selectedFieldType);
  };

  const handleDataCompletion = async (actionType: 'geocode' | 'google-places' | 'ai-content' | 'complete-all', options: { limit?: number; dry_run?: boolean } = {}) => {
    try {
      const { limit = 50, dry_run = false } = options;
      
      let endpoint;
      let actionName;
      
      switch (actionType) {
        case 'geocode':
          endpoint = API_ENDPOINTS.DATA_COMPLETION_GEOCODE;
          actionName = 'Geocoding';
          break;
        case 'google-places':
          endpoint = API_ENDPOINTS.DATA_COMPLETION_GOOGLE_PLACES;
          actionName = 'Google Places data fetch';
          break;
        case 'ai-content':
          endpoint = API_ENDPOINTS.DATA_COMPLETION_AI_CONTENT;
          actionName = 'AI content generation';
          break;
        case 'complete-all':
          endpoint = API_ENDPOINTS.DATA_COMPLETION_COMPLETE_ALL;
          actionName = 'Complete data completion';
          break;
        default:
          throw new Error('Invalid action type');
      }
      
      message.info(`${actionName} starting... This may take several minutes.`);
      
      const response = await api.post(endpoint, { limit, dry_run });
      
      if (response.data.success) {
        if (dry_run) {
          message.info(response.data.message);
        } else {
          message.success(response.data.message);
          
          // Poll for completion status if we have a process ID
          if (response.data.process_id) {
            pollCompletionStatus(response.data.process_id, actionName);
          }
        }
        
        // Refresh data after a short delay
        setTimeout(handleRefresh, 2000);
      } else {
        // Handle specific error cases
        if (response.data.troubleshooting) {
          message.error(
            <div>
              <div>{response.data.error}</div>
              <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                Alternative: <code>{response.data.troubleshooting.command_line_alternative}</code>
              </div>
            </div>,
            10 // Show for 10 seconds
          );
        } else {
          message.error(response.data.error || response.data.message || `Failed to start ${actionName}`);
        }
      }
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Unknown error occurred';
      message.error(`Failed to execute ${actionType}: ${errorMessage}`);
    }
  };

  const pollCompletionStatus = async (processId: number, actionName: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`${API_ENDPOINTS.DATA_COMPLETION_STATUS}/${processId}`);
        
        if (response.data.status === 'completed') {
          clearInterval(pollInterval);
          message.success(`${actionName} completed successfully!`);
          handleRefresh();
        } else if (response.data.status === 'failed') {
          clearInterval(pollInterval);
          message.error(`${actionName} failed. Check logs for details.`);
        }
      } catch (error) {
        // Process might have completed before we could check
        clearInterval(pollInterval);
      }
    }, 5000); // Check every 5 seconds
    
    // Stop polling after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 600000);
  };

  const getCompletenessColor = (percentage: number) => {
    if (percentage >= 90) return '#52c41a';
    if (percentage >= 70) return '#faad14';
    if (percentage >= 50) return '#fa8c16';
    return '#f5222d';
  };

  const getCompletenessStatus = (percentage: number) => {
    if (percentage >= 90) return 'success';
    if (percentage >= 70) return 'normal';
    return 'exception';
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'basic': return <InfoCircleOutlined />;
      case 'location': return <ExclamationCircleOutlined />;
      case 'content': return <CheckCircleOutlined />;
      case 'seo': return <InfoCircleOutlined />;
      case 'accessibility': return <WarningOutlined />;
      default: return <InfoCircleOutlined />;
    }
  };

  const fieldColumns: ColumnsType<DataQualityField> = [
    {
      title: 'Field',
      dataIndex: 'display_name',
      key: 'display_name',
      render: (text: string, record: DataQualityField) => (
        <Space>
          {getCategoryIcon(record.category)}
          <span>{text}</span>
          {record.required && <Badge status="error" text="Required" />}
        </Space>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={
          category === 'basic' ? 'blue' :
          category === 'location' ? 'red' :
          category === 'content' ? 'green' :
          category === 'seo' ? 'purple' :
          category === 'accessibility' ? 'orange' : 'default'
        }>
          {category.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Completion',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (percentage: number) => (
        <Progress
          percent={percentage}
          size="small"
          strokeColor={getCompletenessColor(percentage)}
          status={getCompletenessStatus(percentage)}
        />
      ),
      sorter: (a, b) => a.percentage - b.percentage,
    },
    {
      title: 'Completed',
      dataIndex: 'completed',
      key: 'completed',
      render: (completed: number, record: DataQualityField) => (
        <Text>{completed} / {completed + record.missing}</Text>
      ),
    },
    {
      title: 'Missing',
      dataIndex: 'missing',
      key: 'missing',
      render: (missing: number) => (
        <Text type={missing > 0 ? 'danger' : 'success'}>{missing}</Text>
      ),
    },
  ];

  const missingProviderColumns: ColumnsType<MissingProvider> = [
    {
      title: 'Provider',
      dataIndex: 'provider_name',
      key: 'provider_name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'City',
      dataIndex: 'city',
      key: 'city',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={
          status === 'approved' ? 'green' :
          status === 'pending' ? 'orange' :
          status === 'description_generated' ? 'blue' :
          'red'
        }>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Issue',
      dataIndex: 'missing_reason',
      key: 'missing_reason',
      render: (reason: string) => <Text type="secondary">{reason}</Text>,
    },
  ];

  if (loading) {
    return (
      <div style={{ padding: '24px' }}>
        <Card loading={true}>
          <div style={{ height: '400px' }} />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Error Loading Data Quality"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={handleRefresh}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  if (!overview) return null;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>Data Quality Dashboard</Title>
        <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
          Refresh
        </Button>
      </div>

      {/* Overview Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Providers"
              value={overview.total_providers}
              prefix={<InfoCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Average Completeness"
              value={overview.average_completeness}
              suffix="%"
              valueStyle={{ color: getCompletenessColor(overview.average_completeness) }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Complete Providers"
              value={overview.providers_by_completeness.complete}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Incomplete Providers"
              value={overview.providers_by_completeness.incomplete}
              valueStyle={{ color: '#f5222d' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Completeness Distribution */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={12}>
          <Card title="Provider Completeness Distribution">
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                  <Progress
                    type="circle"
                    percent={Math.round((overview.providers_by_completeness.complete / overview.total_providers) * 100)}
                    strokeColor="#52c41a"
                  />
                  <div style={{ marginTop: '8px' }}>
                    <Text strong>Complete (90%+)</Text>
                    <br />
                    <Text>{overview.providers_by_completeness.complete} providers</Text>
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Text>Almost Complete (70-89%): </Text>
                    <Tag color="orange">{overview.providers_by_completeness.almost_complete}</Tag>
                  </div>
                  <div>
                    <Text>Partial (40-69%): </Text>
                    <Tag color="red">{overview.providers_by_completeness.partial}</Tag>
                  </div>
                  <div>
                    <Text>Incomplete (&lt;40%): </Text>
                    <Tag color="red">{overview.providers_by_completeness.incomplete}</Tag>
                  </div>
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Data Completion Actions">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {/* Master Action */}
              <div style={{ padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Button 
                  type="primary"
                  size="large"
                  style={{ width: '100%', height: '48px' }}
                  onClick={() => handleDataCompletion('complete-all', { limit: 25 })}
                >
                  🚀 Complete All Missing Data (25 providers)
                </Button>
                <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: 4 }}>
                  Runs: Google Places → Geocoding → AI Content → WordPress Ready
                </Text>
              </div>

              {/* Individual Actions */}
              <Row gutter={[8, 8]}>
                <Col span={12}>
                  <div style={{ marginBottom: 8 }}>
                    <Badge count={overview.critical_missing.missing_location} style={{ backgroundColor: '#f5222d' }} />
                    <Text style={{ marginLeft: 8 }}>Missing Locations</Text>
                  </div>
                  <Button 
                    size="small" 
                    block
                    disabled={overview.critical_missing.missing_location === 0}
                    onClick={() => handleDataCompletion('geocode')}
                  >
                    📍 Geocode Locations
                  </Button>
                </Col>
                
                <Col span={12}>
                  <div style={{ marginBottom: 8 }}>
                    <Badge count={overview.critical_missing.missing_ai_content} style={{ backgroundColor: '#fa8c16' }} />
                    <Text style={{ marginLeft: 8 }}>Missing AI Content</Text>
                  </div>
                  <Button 
                    size="small" 
                    block
                    disabled={overview.critical_missing.missing_ai_content === 0}
                    onClick={() => handleDataCompletion('ai-content')}
                  >
                    🤖 Generate AI Content
                  </Button>
                </Col>
                
                <Col span={12}>
                  <div style={{ marginBottom: 8 }}>
                    <Text>Google Places Data</Text>
                  </div>
                  <Button 
                    size="small" 
                    block
                    onClick={() => handleDataCompletion('google-places')}
                  >
                    🏪 Fetch Google Data
                  </Button>
                </Col>
                
                <Col span={12}>
                  <div style={{ marginBottom: 8 }}>
                    <Badge count={overview.critical_missing.missing_contact} style={{ backgroundColor: '#faad14' }} />
                    <Text style={{ marginLeft: 8 }}>Missing Contact</Text>
                  </div>
                  <Button 
                    size="small" 
                    block
                    disabled
                    title="Requires manual data entry"
                  >
                    📞 Manual Entry
                  </Button>
                </Col>
              </Row>

              {/* Quick Test Actions */}
              <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 8 }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>Quick Test (Dry Run):</Text>
                <Space size="small" wrap style={{ marginTop: 4 }}>
                  <Button 
                    size="small" 
                    type="dashed"
                    onClick={() => handleDataCompletion('geocode', { limit: 5, dry_run: true })}
                  >
                    Test Geocoding
                  </Button>
                  <Button 
                    size="small" 
                    type="dashed"
                    onClick={() => handleDataCompletion('ai-content', { limit: 5, dry_run: true })}
                  >
                    Test AI Content
                  </Button>
                  <Button 
                    size="small" 
                    type="dashed"
                    onClick={() => handleDataCompletion('complete-all', { limit: 3, dry_run: true })}
                  >
                    Test Complete Flow
                  </Button>
                </Space>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Field Completeness Table */}
      <Card title="Field Completeness Details" style={{ marginBottom: '24px' }}>
        <Table
          columns={fieldColumns}
          dataSource={overview.field_completeness}
          rowKey="field_name"
          pagination={false}
          size="small"
        />
      </Card>

      {/* Missing Data by Category */}
      <Card
        title="Providers with Missing Data"
        extra={
          <Select
            value={selectedFieldType}
            onChange={setSelectedFieldType}
            style={{ width: 200 }}
          >
            <Option value="location">Missing Location</Option>
            <Option value="content">Missing Content</Option>
            <Option value="contact">Missing Contact</Option>
            <Option value="accessibility">Missing Accessibility</Option>
          </Select>
        }
      >
        <Table
          columns={missingProviderColumns}
          dataSource={missingProviders}
          rowKey="id"
          loading={loadingMissing}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>
    </div>
  );
};

export default DataQuality;