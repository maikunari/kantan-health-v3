import React, { useEffect, useState } from 'react';
import {
  Table,
  Card,
  Input,
  Select,
  Button,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Drawer,
  message,
  Popconfirm,
  Badge,
  Tooltip,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  EditOutlined,
  CheckOutlined,
  CloseOutlined,
  SyncOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType, TableProps } from 'antd/es/table';
import { Provider, ProvidersResponse } from '../../types';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';
import ProviderDetail from './ProviderDetail';

const { Title, Text } = Typography;
const { Option } = Select;

interface Filters {
  search: string;
  status: string;
  city: string;
  proficiency: string;
  specialty: string;
}

const ProviderList: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [filters, setFilters] = useState<Filters>({
    search: '',
    status: '',
    city: '',
    proficiency: '',
    specialty: '',
  });
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);

  useEffect(() => {
    fetchProviders();
  }, [pagination.current, pagination.pageSize, filters]);

  const fetchProviders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.current.toString(),
        per_page: pagination.pageSize.toString(),
      });

      // Add filters
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });

      const response = await api.get<ProvidersResponse>(`${API_ENDPOINTS.PROVIDERS}?${params}`);
      setProviders(response.data.providers);
      setPagination(prev => ({
        ...prev,
        total: response.data.pagination.total,
      }));
    } catch (error: any) {
      message.error(error.response?.data?.error || 'Failed to fetch providers');
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange: TableProps<Provider>['onChange'] = (paginationInfo) => {
    setPagination(prev => ({
      ...prev,
      current: paginationInfo.current || 1,
      pageSize: paginationInfo.pageSize || 20,
    }));
  };

  const handleFilterChange = (key: keyof Filters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, current: 1 })); // Reset to first page
  };

  const handleBulkStatusChange = async (status: 'approved' | 'rejected' | 'pending') => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select providers first');
      return;
    }

    try {
      await api.post(API_ENDPOINTS.PROVIDER_BULK_UPDATE, {
        provider_ids: selectedRowKeys,
        action: status === 'approved' ? 'approve' : status === 'rejected' ? 'reject' : 'pending',
      });
      
      message.success(`Successfully updated ${selectedRowKeys.length} providers`);
      setSelectedRowKeys([]);
      fetchProviders();
    } catch (error: any) {
      message.error(error.response?.data?.error || 'Failed to update providers');
    }
  };

  const handleViewProvider = (provider: Provider) => {
    setSelectedProvider(provider);
    setDrawerVisible(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'green';
      case 'rejected': return 'red';
      case 'pending': return 'orange';
      default: return 'default';
    }
  };

  const getProficiencyColor = (score: number) => {
    if (score >= 4) return 'green';
    if (score === 3) return 'orange';
    return 'red';
  };

  const columns: ColumnsType<Provider> = [
    {
      title: 'Provider Name',
      dataIndex: 'provider_name',
      key: 'provider_name',
      width: 250,
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
      width: 200,
      render: (_, record: Provider) => (
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
      width: 200,
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'English Proficiency',
      key: 'proficiency',
      width: 150,
      render: (_, record: Provider) => (
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
      title: 'Content',
      key: 'content',
      width: 120,
      render: (_, record: Provider) => {
        const hasContent = !!(record.ai_description && record.seo_title);
        return (
          <Badge
            status={hasContent ? 'success' : 'default'}
            text={hasContent ? 'Complete' : 'Missing'}
          />
        );
      },
    },
    {
      title: 'WordPress',
      key: 'wordpress',
      width: 120,
      render: (_, record: Provider) => {
        const isSynced = !!record.wordpress_id;
        return (
          <Badge
            status={isSynced ? 'success' : 'default'}
            text={isSynced ? 'Synced' : 'Not Synced'}
          />
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, record: Provider) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              onClick={() => handleViewProvider(record)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button icon={<EditOutlined />} size="small" />
          </Tooltip>
          {record.status === 'pending' && (
            <>
              <Tooltip title="Approve">
                <Popconfirm
                  title="Approve this provider?"
                  onConfirm={() => handleBulkStatusChange('approved')}
                  okText="Yes"
                  cancelText="No"
                >
                  <Button icon={<CheckOutlined />} size="small" type="primary" />
                </Popconfirm>
              </Tooltip>
              <Tooltip title="Reject">
                <Popconfirm
                  title="Reject this provider?"
                  onConfirm={() => handleBulkStatusChange('rejected')}
                  okText="Yes"
                  cancelText="No"
                >
                  <Button icon={<CloseOutlined />} size="small" danger />
                </Popconfirm>
              </Tooltip>
            </>
          )}
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Provider Management</Title>
        <Text type="secondary">Manage healthcare providers and their information</Text>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="Search providers..."
              prefix={<SearchOutlined />}
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Status"
              value={filters.status || undefined}
              onChange={(value) => handleFilterChange('status', value || '')}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="pending">Pending</Option>
              <Option value="approved">Approved</Option>
              <Option value="rejected">Rejected</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="City"
              value={filters.city || undefined}
              onChange={(value) => handleFilterChange('city', value || '')}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="Tokyo">Tokyo</Option>
              <Option value="Osaka">Osaka</Option>
              <Option value="Kyoto">Kyoto</Option>
              <Option value="Yokohama">Yokohama</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Proficiency"
              value={filters.proficiency || undefined}
              onChange={(value) => handleFilterChange('proficiency', value || '')}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="5">Score 5 (Fluent)</Option>
              <Option value="4">Score 4 (Conversational)</Option>
              <Option value="3">Score 3 (Basic)</Option>
              <Option value="0">Score 0 (Unknown)</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={fetchProviders}
                loading={loading}
              >
                Refresh
              </Button>
              <Button icon={<FilterOutlined />}>
                Advanced Filters
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Bulk Actions */}
      {selectedRowKeys.length > 0 && (
        <Card style={{ marginBottom: 16, backgroundColor: '#f6ffed' }}>
          <Space>
            <Text strong>{selectedRowKeys.length} providers selected</Text>
            <Button 
              type="primary" 
              icon={<CheckOutlined />}
              onClick={() => handleBulkStatusChange('approved')}
            >
              Approve Selected
            </Button>
            <Button 
              danger 
              icon={<CloseOutlined />}
              onClick={() => handleBulkStatusChange('rejected')}
            >
              Reject Selected
            </Button>
            <Button 
              icon={<SyncOutlined />}
            >
              Sync to WordPress
            </Button>
            <Button onClick={() => setSelectedRowKeys([])}>
              Clear Selection
            </Button>
          </Space>
        </Card>
      )}

      {/* Main Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={providers}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} providers`,
          }}
          rowSelection={rowSelection}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Provider Detail Drawer */}
      <Drawer
        title="Provider Details"
        width={720}
        open={drawerVisible}
        onClose={() => {
          setDrawerVisible(false);
          setSelectedProvider(null);
        }}
        extra={
          <Space>
            <Button onClick={() => setDrawerVisible(false)}>Cancel</Button>
            <Button type="primary">Save Changes</Button>
          </Space>
        }
      >
        {selectedProvider && (
          <ProviderDetail 
            provider={selectedProvider} 
            onUpdate={fetchProviders}
          />
        )}
      </Drawer>
    </div>
  );
};

export default ProviderList;