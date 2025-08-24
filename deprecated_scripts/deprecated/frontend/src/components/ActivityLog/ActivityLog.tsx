import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Typography,
  Select,
  Space,
  Button,
  DatePicker,
  Row,
  Col,
  Statistic,
  Timeline,
  Badge,
  Alert,
  Spin,
  message,
  Divider,
  Modal,
  Descriptions,
} from 'antd';
import {
  HistoryOutlined,
  ReloadOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  PlusCircleOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  SyncOutlined,
  DeleteOutlined,
  SettingOutlined,
  UserOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import api from '../../utils/api';

dayjs.extend(relativeTime);

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface ActivityRecord {
  id: number;
  timestamp: string;
  activity_type: string;
  activity_category: string;
  description: string;
  provider_id?: number;
  provider_name?: string;
  details?: any;
  status: string;
  duration_ms?: number;
  error_message?: string;
}

interface ActivitySummary {
  [category: string]: {
    total: number;
    success: number;
    error: number;
    success_rate: number;
  };
}

interface CategoryInfo {
  name: string;
  description: string;
  icon: string;
}

const ActivityLog: React.FC = () => {
  const [activities, setActivities] = useState<ActivityRecord[]>([]);
  const [summary, setSummary] = useState<ActivitySummary>({});
  const [categories, setCategories] = useState<{ [key: string]: CategoryInfo }>({});
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<ActivityRecord | null>(null);
  const [detailsModalVisible, setDetailsModalVisible] = useState(false);

  useEffect(() => {
    fetchCategories();
    fetchActivities();
    fetchSummary();
  }, [selectedCategory]);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/api/activity-log/activities/categories');
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const fetchActivities = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 200 };
      if (selectedCategory) {
        params.category = selectedCategory;
      }
      
      const response = await api.get('/api/activity-log/activities', { params });
      setActivities(response.data.activities);
    } catch (error) {
      console.error('Failed to fetch activities:', error);
      message.error('Failed to load activity log');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await api.get('/api/activity-log/activities/summary', {
        params: { days: 7 }
      });
      setSummary(response.data.summary);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchActivities(), fetchSummary()]);
    setRefreshing(false);
    message.success('Activity log refreshed');
  };

  const getCategoryIcon = (category: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      'provider_creation': <PlusCircleOutlined />,
      'content_generation': <FileTextOutlined />,
      'data_quality': <DatabaseOutlined />,
      'wordpress_sync': <SyncOutlined />,
      'duplicate_cleanup': <DeleteOutlined />,
      'settings_update': <SettingOutlined />,
      'authentication': <UserOutlined />,
    };
    return iconMap[category] || <HistoryOutlined />;
  };

  const getStatusTag = (status: string) => {
    const statusMap: { [key: string]: { color: string; icon: React.ReactNode } } = {
      'success': { color: 'success', icon: <CheckCircleOutlined /> },
      'error': { color: 'error', icon: <CloseCircleOutlined /> },
      'started': { color: 'processing', icon: <ClockCircleOutlined /> },
      'partial': { color: 'warning', icon: <ClockCircleOutlined /> },
    };
    
    const config = statusMap[status] || { color: 'default', icon: null };
    
    return (
      <Tag color={config.color} icon={config.icon}>
        {status.toUpperCase()}
      </Tag>
    );
  };

  const showActivityDetails = (record: ActivityRecord) => {
    setSelectedActivity(record);
    setDetailsModalVisible(true);
  };

  const columns: ColumnsType<ActivityRecord> = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => (
        <div>
          <div>{dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {dayjs(timestamp).fromNow()}
          </Text>
        </div>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'activity_category',
      key: 'activity_category',
      width: 150,
      render: (category: string) => (
        <Space>
          {getCategoryIcon(category)}
          <Text>{categories[category]?.name || category}</Text>
        </Space>
      ),
    },
    {
      title: 'Activity',
      dataIndex: 'activity_type',
      key: 'activity_type',
      width: 150,
      render: (type: string) => (
        <Tag>{type.replace(/_/g, ' ').toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      render: (text: string, record: ActivityRecord) => (
        <div>
          <div>{text}</div>
          {record.provider_name && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Provider: {record.provider_name}
            </Text>
          )}
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: 'Duration',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (duration: number) => 
        duration ? `${(duration / 1000).toFixed(1)}s` : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record: ActivityRecord) => (
        <Button 
          size="small" 
          onClick={() => showActivityDetails(record)}
          disabled={!record.details && !record.error_message}
        >
          Details
        </Button>
      ),
    },
  ];

  const exportToCSV = () => {
    const csvContent = [
      ['Timestamp', 'Category', 'Activity Type', 'Description', 'Status', 'Duration (ms)', 'Provider', 'Error'],
      ...activities.map(a => [
        a.timestamp,
        a.activity_category,
        a.activity_type,
        a.description,
        a.status,
        a.duration_ms || '',
        a.provider_name || '',
        a.error_message || ''
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity-log-${dayjs().format('YYYY-MM-DD')}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Activity Log</Title>
        <Text type="secondary">
          Track all system operations including provider creation, content generation, 
          data quality updates, and WordPress synchronization.
        </Text>
      </div>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {Object.entries(summary).map(([category, stats]) => (
          <Col xs={24} sm={12} md={8} lg={6} key={category}>
            <Card>
              <Statistic
                title={categories[category]?.name || category}
                value={stats.total}
                prefix={getCategoryIcon(category)}
                suffix={
                  <div style={{ fontSize: '14px', marginTop: 8 }}>
                    <div>
                      <CheckCircleOutlined style={{ color: '#52c41a' }} /> {stats.success}
                    </div>
                    {stats.error > 0 && (
                      <div>
                        <CloseCircleOutlined style={{ color: '#f5222d' }} /> {stats.error}
                      </div>
                    )}
                  </div>
                }
              />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">Success Rate</Text>
                <div>
                  <Badge
                    status={stats.success_rate >= 90 ? 'success' : stats.success_rate >= 70 ? 'warning' : 'error'}
                    text={`${stats.success_rate}%`}
                  />
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Activity Log Table */}
      <Card 
        title="Recent Activities"
        extra={
          <Space>
            <Select
              placeholder="Filter by category"
              style={{ width: 200 }}
              allowClear
              value={selectedCategory}
              onChange={setSelectedCategory}
            >
              {Object.entries(categories).map(([key, info]) => (
                <Option key={key} value={key}>
                  <Space>
                    {getCategoryIcon(key)}
                    {info.name}
                  </Space>
                </Option>
              ))}
            </Select>
            
            <Button
              icon={<ExportOutlined />}
              onClick={exportToCSV}
            >
              Export CSV
            </Button>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={refreshing}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={activities}
          rowKey="id"
          loading={loading}
          pagination={{
            defaultPageSize: 50,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} activities`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Details Modal */}
      <Modal
        title="Activity Details"
        open={detailsModalVisible}
        onCancel={() => setDetailsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailsModalVisible(false)}>
            Close
          </Button>
        ]}
        width={600}
      >
        {selectedActivity && (
          <div>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Activity ID">
                {selectedActivity.id}
              </Descriptions.Item>
              <Descriptions.Item label="Timestamp">
                {dayjs(selectedActivity.timestamp).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="Category">
                <Space>
                  {getCategoryIcon(selectedActivity.activity_category)}
                  {categories[selectedActivity.activity_category]?.name}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Type">
                {selectedActivity.activity_type}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                {getStatusTag(selectedActivity.status)}
              </Descriptions.Item>
              {selectedActivity.provider_name && (
                <Descriptions.Item label="Provider">
                  {selectedActivity.provider_name} (ID: {selectedActivity.provider_id})
                </Descriptions.Item>
              )}
              {selectedActivity.duration_ms && (
                <Descriptions.Item label="Duration">
                  {(selectedActivity.duration_ms / 1000).toFixed(1)} seconds
                </Descriptions.Item>
              )}
            </Descriptions>

            {selectedActivity.error_message && (
              <Alert
                message="Error Details"
                description={selectedActivity.error_message}
                type="error"
                style={{ marginTop: 16 }}
              />
            )}

            {selectedActivity.details && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>Additional Details</Title>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  overflow: 'auto',
                  maxHeight: 300
                }}>
                  {JSON.stringify(selectedActivity.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ActivityLog;