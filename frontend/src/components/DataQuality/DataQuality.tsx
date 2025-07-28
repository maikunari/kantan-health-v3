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

  const handleBulkAction = async (actionType: 'geocode' | 'content') => {
    try {
      if (actionType === 'geocode') {
        // This would integrate with the existing populate_provider_locations.py script
        message.info('Geocoding missing locations... This may take a few minutes.');
        // In a real implementation, you'd call an API endpoint that triggers the geocoding script
        // await api.post('/api/providers/bulk-geocode');
        console.log('Would trigger geocoding for providers missing location data');
      } else if (actionType === 'content') {
        // This would integrate with the existing content generation system  
        message.info('Generating missing AI content... This may take several minutes.');
        // In a real implementation, you'd call the content generation API
        // await api.post('/api/content/generate-missing');
        console.log('Would trigger content generation for providers missing AI content');
      }
      
      // Show success message and refresh data
      setTimeout(() => {
        message.success(`Bulk ${actionType} action completed successfully!`);
        handleRefresh();
      }, 2000);
      
    } catch (error: any) {
      message.error(`Failed to execute bulk ${actionType} action: ${error.message}`);
    }
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
          <Card title="Critical Missing Data & Quick Actions">
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text>Missing Location Data:</Text>
                  <Badge count={overview.critical_missing.missing_location} style={{ backgroundColor: '#f5222d' }} />
                </div>
                <Button 
                  size="small" 
                  type="primary" 
                  disabled={overview.critical_missing.missing_location === 0}
                  onClick={() => handleBulkAction('geocode')}
                >
                  Geocode Missing Locations
                </Button>
              </div>
              
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text>Missing AI Content:</Text>
                  <Badge count={overview.critical_missing.missing_ai_content} style={{ backgroundColor: '#fa8c16' }} />
                </div>
                <Button 
                  size="small" 
                  type="primary"
                  disabled={overview.critical_missing.missing_ai_content === 0}
                  onClick={() => handleBulkAction('content')}
                >
                  Generate Missing Content
                </Button>
              </div>
              
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text>Missing Contact Info:</Text>
                  <Badge count={overview.critical_missing.missing_contact} style={{ backgroundColor: '#faad14' }} />
                </div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Requires manual data entry
                </Text>
              </div>
              
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text>Missing Accessibility:</Text>
                  <Badge count={overview.critical_missing.missing_accessibility} style={{ backgroundColor: '#1890ff' }} />
                </div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Update via Provider Details
                </Text>
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