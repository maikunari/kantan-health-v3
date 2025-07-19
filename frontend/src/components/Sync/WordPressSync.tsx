import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Typography,
  Progress,
  Alert,
  Space,
  Statistic,
  Tag,
  Table,
  Form,
  InputNumber,
  Switch,
  message,
  Badge,
  Divider,
  Spin,
  List,
  Timeline,
} from 'antd';
import {
  SyncOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  LinkOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { SyncStatus } from '../../types';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';

const { Title, Text } = Typography;

interface SyncOperation {
  operation: string;
  status: string;
  count: number;
  last_operation: string;
}

interface SyncError {
  provider_id: number;
  error: string;
  timestamp: string;
}

const WordPressSync: React.FC = () => {
  const [form] = Form.useForm();
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'success' | 'error'>('unknown');

  useEffect(() => {
    fetchStatus();
    testConnection();
    const interval = setInterval(fetchStatus, 15000); // Update every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      setRefreshing(true);
      const [statusRes, batchRes] = await Promise.all([
        api.get(API_ENDPOINTS.SYNC_STATUS),
        api.get(API_ENDPOINTS.SYNC_BATCH_STATUS),
      ]);
      
      setStatus({
        ...statusRes.data,
        batch_running: batchRes.data.sync_running,
      });
    } catch (error: any) {
      console.error('Failed to fetch sync status:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const testConnection = async () => {
    try {
      const response = await api.get(API_ENDPOINTS.SYNC_TEST_CONNECTION);
      setConnectionStatus(response.data.status === 'connected' ? 'success' : 'error');
    } catch (error) {
      setConnectionStatus('error');
    }
  };

  const handleStartSync = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      await api.post(API_ENDPOINTS.SYNC, {
        sync_all: values.sync_all || false,
        limit: values.limit || 25,
        force: values.force || false,
        dry_run: values.dry_run || false,
      });
      
      message.success('WordPress sync started successfully');
      setSyncing(true);
      fetchStatus();
    } catch (error: any) {
      message.error(error.response?.data?.error || 'Failed to start sync');
    } finally {
      setLoading(false);
    }
  };

  if (!status) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading WordPress sync status...</div>
      </div>
    );
  }

  const syncPercentage = status.sync_overview.total_providers > 0 
    ? status.sync_overview.sync_percentage 
    : 0;

  const operationColumns: ColumnsType<SyncOperation> = [
    {
      title: 'Operation',
      dataIndex: 'operation',
      key: 'operation',
      render: (text: string) => text.charAt(0).toUpperCase() + text.slice(1),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : status === 'error' ? 'red' : 'orange'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
    },
    {
      title: 'Last Operation',
      dataIndex: 'last_operation',
      key: 'last_operation',
      render: (text: string) => text ? new Date(text).toLocaleString() : 'Never',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>WordPress Sync Management</Title>
        <Text type="secondary">Manage synchronization between the database and WordPress</Text>
      </div>

      {/* Connection Status */}
      <Alert
        message={
          <Space>
            <GlobalOutlined />
            WordPress Connection Status
          </Space>
        }
        description={
          connectionStatus === 'success' 
            ? 'Successfully connected to WordPress API'
            : connectionStatus === 'error'
            ? 'Unable to connect to WordPress API. Check your credentials and URL.'
            : 'Testing connection...'
        }
        type={connectionStatus === 'success' ? 'success' : connectionStatus === 'error' ? 'error' : 'info'}
        showIcon
        style={{ marginBottom: 24 }}
        action={
          <Button size="small" onClick={testConnection}>
            Test Connection
          </Button>
        }
      />

      {/* Status Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Providers"
              value={status.sync_overview.total_providers}
              prefix={<GlobalOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Synced"
              value={status.sync_overview.synced_providers}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Pending Sync"
              value={status.sync_overview.pending_sync}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <SyncOutlined style={{ color: '#722ed1', marginRight: 8 }} />
              <Text strong>Sync Status</Text>
              {refreshing && <Spin size="small" style={{ marginLeft: 8 }} />}
            </div>
            <Badge
              status={status.batch_running ? 'processing' : 'default'}
              text={status.batch_running ? 'Running' : 'Idle'}
            />
          </Card>
        </Col>
      </Row>

      {/* Sync Progress */}
      <Card title="Synchronization Progress" style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text strong>Overall Sync Completion</Text>
            <Text>{Math.round(syncPercentage)}%</Text>
          </div>
          <Progress 
            percent={syncPercentage}
            status={syncPercentage === 100 ? 'success' : 'active'}
            strokeColor="#52c41a"
          />
        </div>

        <Row gutter={16}>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">Synced Last 24h</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#52c41a' }}>
                {status.sync_overview.synced_last_24h}
              </div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">Success Rate</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1890ff' }}>
                {status.recent_operations.length > 0 
                  ? Math.round((status.recent_operations.filter(op => op.status === 'success').length / status.recent_operations.length) * 100)
                  : 0}%
              </div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">Recent Errors</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f5222d' }}>
                {status.recent_errors.length}
              </div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">Operations</Text>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#722ed1' }}>
                {status.recent_operations.length}
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Control Panel */}
      <Card title="Sync Control Panel">
        {status.batch_running && (
          <Alert
            message="Sync Operation in Progress"
            description="WordPress sync is currently running. New requests will be queued."
            type="info"
            showIcon
            icon={<ThunderboltOutlined />}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item 
                label="Sync Limit" 
                name="limit"
                initialValue={25}
              >
                <InputNumber 
                  min={1} 
                  max={100} 
                  style={{ width: '100%' }}
                  placeholder="Number of providers to sync"
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item name="sync_all" valuePropName="checked">
                <Switch /> 
                <Text style={{ marginLeft: 8 }}>Sync All Eligible Providers</Text>
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item name="force" valuePropName="checked">
                <Switch /> 
                <Text style={{ marginLeft: 8 }}>Force Update Existing</Text>
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
              icon={<SyncOutlined />}
              onClick={handleStartSync}
              loading={loading}
              disabled={status.batch_running || connectionStatus === 'error'}
              size="large"
            >
              Start Sync
            </Button>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchStatus}
              loading={refreshing}
            >
              Refresh Status
            </Button>

            <Button
              icon={<LinkOutlined />}
              onClick={testConnection}
            >
              Test Connection
            </Button>
          </Space>
        </Form>
      </Card>

      {/* Recent Operations and Errors */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Recent Operations" size="small">
            <Table
              columns={operationColumns}
              dataSource={status.recent_operations}
              pagination={false}
              size="small"
              scroll={{ y: 300 }}
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card 
            title="Recent Errors" 
            size="small"
            extra={
              status.recent_errors.length > 0 && (
                <Tag color="red">{status.recent_errors.length} errors</Tag>
              )
            }
          >
            {status.recent_errors.length > 0 ? (
              <List
                size="small"
                dataSource={status.recent_errors}
                renderItem={(error: SyncError) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<WarningOutlined style={{ color: '#f5222d' }} />}
                      title={`Provider ID: ${error.provider_id}`}
                      description={
                        <div>
                          <div>{error.error}</div>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {new Date(error.timestamp).toLocaleString()}
                          </Text>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
                <CheckCircleOutlined style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} />
                <div>No recent errors</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default WordPressSync;