import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Select,
  Input,
  Tooltip,
  Modal,
  message,
  Statistic,
  Row,
  Col,
  Badge,
  Typography,
  Alert,
  Collapse
} from 'antd';
import {
  ReloadOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  BugOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Option } = Select;
const { Search } = Input;
const { Title, Text } = Typography;
const { Panel } = Collapse;

interface PipelineFailure {
  id: number;
  provider_id: number;
  provider_name: string;
  current_provider_name: string;
  current_status: string;
  step: string;
  failure_reason: string;
  error_details: string;
  retry_count: number;
  created_at: string;
  has_ai_description: boolean;
  has_seo_title: boolean;
  has_location: boolean;
}

interface FailureSummary {
  total_failures_7d: number;
  total_resolved_7d: number;
  total_unresolved_7d: number;
  resolution_rate: number;
}

interface FailureBreakdown {
  step: string;
  failure_reason: string;
  count: number;
  resolved_count: number;
  unresolved_count: number;
  latest_failure: string;
}

interface RunStatistic {
  run_type: string;
  total_runs: number;
  completed_runs: number;
  success_rate: number;
  avg_successful: number;
  avg_failed: number;
}

interface MissingFieldProvider {
  id: number;
  provider_name: string;
  status: string;
  missing_fields: string[];
  missing_count: number;
  created_at: string;
}

const PipelineFailures: React.FC = () => {
  const [failures, setFailures] = useState<PipelineFailure[]>([]);
  const [missingFieldProviders, setMissingFieldProviders] = useState<MissingFieldProvider[]>([]);
  const [summary, setSummary] = useState<FailureSummary | null>(null);
  const [failureBreakdown, setFailureBreakdown] = useState<FailureBreakdown[]>([]);
  const [runStatistics, setRunStatistics] = useState<RunStatistic[]>([]);
  const [loading, setLoading] = useState(false);
  const [retryingIds, setRetryingIds] = useState<Set<number>>(new Set());
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  
  // Filters
  const [stepFilter, setStepFilter] = useState<string>('');
  const [reasonFilter, setReasonFilter] = useState<string>('');
  const [searchText, setSearchText] = useState<string>('');

  useEffect(() => {
    loadFailures();
    loadSummary();
    loadMissingFieldProviders();
  }, [stepFilter, reasonFilter]);

  const loadFailures = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (stepFilter) params.append('step', stepFilter);
      if (reasonFilter) params.append('failure_reason', reasonFilter);
      params.append('limit', '100');

      const response = await fetch(`/api/pipeline/failures?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setFailures(data.failures);
      } else {
        message.error('Failed to load pipeline failures');
      }
    } catch (error) {
      message.error('Error loading pipeline failures');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const response = await fetch('/api/pipeline/failures/summary');
      const data = await response.json();
      
      if (data.success) {
        setSummary(data.summary);
        setFailureBreakdown(data.failure_breakdown);
        setRunStatistics(data.run_statistics);
      }
    } catch (error) {
      console.error('Error loading summary:', error);
    }
  };

  const loadMissingFieldProviders = async () => {
    try {
      const response = await fetch('/api/pipeline/providers/missing-fields?limit=50');
      const data = await response.json();
      
      if (data.success) {
        setMissingFieldProviders(data.providers);
      }
    } catch (error) {
      console.error('Error loading missing field providers:', error);
    }
  };

  const handleRetryFailure = async (failureId: number) => {
    setRetryingIds(prev => new Set(prev).add(failureId));
    
    try {
      const response = await fetch(`/api/pipeline/failures/${failureId}/retry`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.success) {
        message.success(`Retry initiated for failure ID ${failureId}`);
        loadFailures();
      } else {
        message.error(`Failed to retry: ${data.error}`);
      }
    } catch (error) {
      message.error('Error retrying failure');
      console.error('Error:', error);
    } finally {
      setRetryingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(failureId);
        return newSet;
      });
    }
  };

  const handleBulkRetry = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select failures to retry');
      return;
    }

    Modal.confirm({
      title: 'Bulk Retry Confirmation',
      content: `Are you sure you want to retry ${selectedRowKeys.length} selected failures?`,
      icon: <ExclamationCircleOutlined />,
      onOk: async () => {
        try {
          const response = await fetch('/api/pipeline/failures/bulk-retry', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              failure_ids: selectedRowKeys
            })
          });
          
          const data = await response.json();
          
          if (data.success) {
            message.success(`Bulk retry initiated for ${data.provider_count} providers`);
            setSelectedRowKeys([]);
            loadFailures();
          } else {
            message.error(`Failed to bulk retry: ${data.error}`);
          }
        } catch (error) {
          message.error('Error in bulk retry');
          console.error('Error:', error);
        }
      }
    });
  };

  const getStepIcon = (step: string) => {
    switch (step) {
      case 'google_data': return '🌐';
      case 'geocoding': return '📍';
      case 'ai_content': return '🤖';
      case 'wp_preparation': return '📝';
      default: return '❓';
    }
  };

  const getStepColor = (step: string) => {
    switch (step) {
      case 'google_data': return 'blue';
      case 'geocoding': return 'green';
      case 'ai_content': return 'purple';
      case 'wp_preparation': return 'orange';
      default: return 'default';
    }
  };

  const getReasonColor = (reason: string) => {
    switch (reason) {
      case 'api_limit': return 'red';
      case 'timeout': return 'orange';
      case 'network_error': return 'volcano';
      case 'processing_error': return 'magenta';
      case 'max_retries_exceeded': return 'red';
      default: return 'default';
    }
  };

  const filteredFailures = failures.filter(failure => 
    !searchText || 
    failure.provider_name.toLowerCase().includes(searchText.toLowerCase()) ||
    failure.current_provider_name?.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns: ColumnsType<PipelineFailure> = [
    {
      title: 'Provider',
      dataIndex: 'provider_name',
      key: 'provider_name',
      render: (text: string, record: PipelineFailure) => (
        <div>
          <div><strong>{record.current_provider_name || text}</strong></div>
          <div><Text type="secondary">ID: {record.provider_id}</Text></div>
          <div><Text type="secondary">Status: {record.current_status}</Text></div>
        </div>
      ),
      width: 250,
    },
    {
      title: 'Step',
      dataIndex: 'step',
      key: 'step',
      render: (step: string) => (
        <Tag color={getStepColor(step)}>
          {getStepIcon(step)} {step.replace('_', ' ').toUpperCase()}
        </Tag>
      ),
      width: 140,
    },
    {
      title: 'Failure Reason',
      dataIndex: 'failure_reason',
      key: 'failure_reason',
      render: (reason: string) => (
        <Tag color={getReasonColor(reason)}>
          {reason.replace('_', ' ').toUpperCase()}
        </Tag>
      ),
      width: 150,
    },
    {
      title: 'Current Status',
      key: 'current_status',
      render: (_, record: PipelineFailure) => (
        <Space direction="vertical" size="small">
          <div>
            {record.has_ai_description ? 
              <Tag color="green" icon={<CheckCircleOutlined />}>AI Content</Tag> : 
              <Tag color="red">No AI Content</Tag>
            }
          </div>
          <div>
            {record.has_location ? 
              <Tag color="green" icon={<CheckCircleOutlined />}>Location</Tag> : 
              <Tag color="red">No Location</Tag>
            }
          </div>
        </Space>
      ),
      width: 150,
    },
    {
      title: 'Retry Count',
      dataIndex: 'retry_count',
      key: 'retry_count',
      render: (count: number) => (
        <Badge count={count} style={{ backgroundColor: count > 2 ? '#f5222d' : '#1890ff' }} />
      ),
      width: 100,
    },
    {
      title: 'Error Details',
      dataIndex: 'error_details',
      key: 'error_details',
      render: (details: string) => (
        details ? (
          <Tooltip title={details} placement="topLeft">
            <Button icon={<InfoCircleOutlined />} size="small" type="link">
              View Details
            </Button>
          </Tooltip>
        ) : null
      ),
      width: 120,
    },
    {
      title: 'Failed At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <div>
          <div>{new Date(date).toLocaleDateString()}</div>
          <div><Text type="secondary">{new Date(date).toLocaleTimeString()}</Text></div>
        </div>
      ),
      width: 120,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: PipelineFailure) => (
        <Button
          type="primary"
          size="small"
          icon={<ReloadOutlined />}
          loading={retryingIds.has(record.id)}
          onClick={() => handleRetryFailure(record.id)}
        >
          Retry
        </Button>
      ),
      width: 100,
    },
  ];

  const missingFieldColumns: ColumnsType<MissingFieldProvider> = [
    {
      title: 'Provider',
      dataIndex: 'provider_name',
      key: 'provider_name',
      render: (text: string, record: MissingFieldProvider) => (
        <div>
          <div><strong>{text}</strong></div>
          <div><Text type="secondary">ID: {record.id}</Text></div>
          <div><Text type="secondary">Status: {record.status}</Text></div>
        </div>
      ),
    },
    {
      title: 'Missing Fields',
      dataIndex: 'missing_fields',
      key: 'missing_fields',
      render: (fields: string[]) => (
        <Space wrap>
          {fields.map(field => (
            <Tag key={field} color="orange">
              {field.replace('_', ' ').toUpperCase()}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: 'Missing Count',
      dataIndex: 'missing_count',
      key: 'missing_count',
      render: (count: number) => (
        <Badge count={count} style={{ backgroundColor: '#fa8c16' }} />
      ),
    },
    {
      title: 'Added At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <BugOutlined /> Pipeline Failures Management
        </Title>
        <Text type="secondary">
          Monitor and retry failed pipeline steps with detailed failure tracking
        </Text>
      </div>

      {/* Summary Statistics */}
      {summary && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Failures (7d)"
                value={summary.total_failures_7d}
                valueStyle={{ color: '#cf1322' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Unresolved"
                value={summary.total_unresolved_7d}
                valueStyle={{ color: '#fa8c16' }}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Resolved"
                value={summary.total_resolved_7d}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Resolution Rate"
                value={summary.resolution_rate}
                precision={1}
                suffix="%"
                valueStyle={{ color: summary.resolution_rate > 70 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Collapse style={{ marginBottom: '24px' }}>
        <Panel header="Failure Breakdown & Pipeline Statistics" key="stats">
          <Row gutter={16}>
            <Col span={12}>
              <Title level={4}>Failure Breakdown</Title>
              {failureBreakdown.map((breakdown, index) => (
                <div key={index} style={{ marginBottom: '8px' }}>
                  <Tag color={getStepColor(breakdown.step)}>
                    {breakdown.step.toUpperCase()}
                  </Tag>
                  <Tag color={getReasonColor(breakdown.failure_reason)}>
                    {breakdown.failure_reason.replace('_', ' ').toUpperCase()}
                  </Tag>
                  <Text>
                    {breakdown.unresolved_count} unresolved / {breakdown.count} total
                  </Text>
                </div>
              ))}
            </Col>
            <Col span={12}>
              <Title level={4}>Pipeline Run Statistics</Title>
              {runStatistics.map((stat, index) => (
                <div key={index} style={{ marginBottom: '8px' }}>
                  <Tag>{stat.run_type.toUpperCase()}</Tag>
                  <Text>
                    {stat.success_rate}% success rate ({stat.completed_runs}/{stat.total_runs} runs)
                  </Text>
                </div>
              ))}
            </Col>
          </Row>
        </Panel>
      </Collapse>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16} align="middle">
          <Col span={6}>
            <Select
              placeholder="Filter by step"
              style={{ width: '100%' }}
              value={stepFilter}
              onChange={setStepFilter}
              allowClear
            >
              <Option value="google_data">🌐 Google Data</Option>
              <Option value="geocoding">📍 Geocoding</Option>
              <Option value="ai_content">🤖 AI Content</Option>
              <Option value="wp_preparation">📝 WP Preparation</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Select
              placeholder="Filter by reason"
              style={{ width: '100%' }}
              value={reasonFilter}
              onChange={setReasonFilter}
              allowClear
            >
              <Option value="api_limit">API Limit</Option>
              <Option value="timeout">Timeout</Option>
              <Option value="network_error">Network Error</Option>
              <Option value="processing_error">Processing Error</Option>
              <Option value="max_retries_exceeded">Max Retries Exceeded</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Search
              placeholder="Search providers"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={6}>
            <Space>
              <Button 
                type="primary" 
                icon={<ReloadOutlined />} 
                onClick={loadFailures}
                loading={loading}
              >
                Refresh
              </Button>
              <Button
                type="default"
                disabled={selectedRowKeys.length === 0}
                onClick={handleBulkRetry}
              >
                Bulk Retry ({selectedRowKeys.length})
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Pipeline Failures Table */}
      <Card title="Pipeline Failures" style={{ marginBottom: '24px' }}>
        {filteredFailures.length === 0 && !loading ? (
          <Alert
            message="No Pipeline Failures Found"
            description="Great news! There are currently no unresolved pipeline failures."
            type="success"
            showIcon
          />
        ) : (
          <Table
            columns={columns}
            dataSource={filteredFailures}
            rowKey="id"
            loading={loading}
            rowSelection={rowSelection}
            pagination={{
              total: filteredFailures.length,
              showSizeChanger: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} of ${total} failures`,
            }}
            scroll={{ x: 1400 }}
          />
        )}
      </Card>

      {/* Missing Fields Providers */}
      <Card title="Providers with Missing Fields">
        {missingFieldProviders.length === 0 ? (
          <Alert
            message="No Missing Field Issues"
            description="All providers have complete field data."
            type="success"
            showIcon
          />
        ) : (
          <Table
            columns={missingFieldColumns}
            dataSource={missingFieldProviders}
            rowKey="id"
            pagination={{
              total: missingFieldProviders.length,
              showSizeChanger: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} of ${total} providers`,
            }}
          />
        )}
      </Card>
    </div>
  );
};

export default PipelineFailures;