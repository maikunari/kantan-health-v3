import React, { useEffect, useState } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Typography, 
  Alert, 
  Spin,
  Tag,
  Progress,
  Divider,
  Space
} from 'antd';
import {
  UserOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  ApiOutlined,
  DollarOutlined,
  FileTextOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line, ResponsiveContainer } from 'recharts';
import { DashboardOverview, ProviderStats } from '../../types';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';

const { Title, Text } = Typography;

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#eb2f96'];

const Dashboard: React.FC = () => {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [stats, setStats] = useState<ProviderStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
    // Set up polling for real-time updates
    const interval = setInterval(fetchDashboardData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setError(null);
      const [overviewRes, statsRes] = await Promise.all([
        api.get(API_ENDPOINTS.DASHBOARD_OVERVIEW),
        api.get(API_ENDPOINTS.PROVIDER_STATS),
      ]);
      
      setOverview(overviewRes.data);
      setStats(statsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error Loading Dashboard"
        description={error}
        type="error"
        showIcon
        action={
          <button onClick={fetchDashboardData}>Retry</button>
        }
      />
    );
  }

  if (!overview || !stats) return null;

  // Prepare chart data
  const statusData = Object.entries(stats.status_breakdown).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value,
    color: key === 'approved' ? '#52c41a' : key === 'pending' ? '#faad14' : '#f5222d'
  }));

  const proficiencyData = Object.entries(stats.proficiency_breakdown).map(([score, count]) => ({
    score: `Score ${score}`,
    count,
  }));

  const cityData = stats.top_cities.slice(0, 8);

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Healthcare Directory Dashboard</Title>
        <Text type="secondary">System overview and key performance metrics</Text>
      </div>

      {/* Key Metrics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Providers"
              value={overview.providers.total}
              prefix={<UserOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Approved"
              value={overview.providers.approved}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Pending Review"
              value={overview.providers.pending}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Synced to WordPress"
              value={overview.providers.synced_to_wordpress}
              prefix={<GlobalOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Content Generation Progress */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="AI Content Generation Progress" extra={<FileTextOutlined />}>
            <div style={{ marginBottom: 16 }}>
              <Text strong>Completion Rate</Text>
              <Progress 
                percent={overview.content_generation.completion_rate}
                status={overview.content_generation.completion_rate === 100 ? 'success' : 'active'}
                strokeColor="#52c41a"
              />
            </div>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Fully Processed"
                  value={overview.content_generation.fully_processed}
                  suffix={`/ ${overview.content_generation.total_approved}`}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="With AI Content"
                  value={overview.providers.with_ai_content}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Recent Activity (24h)" extra={<SyncOutlined />}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>New Providers</Text>
                <Tag color="blue">{overview.recent_activity.new_providers_24h}</Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>WordPress Syncs</Text>
                <Tag color="green">{overview.recent_activity.recent_syncs_24h}</Tag>
              </div>
              <Divider style={{ margin: '12px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text strong>API Calls Today</Text>
                <Text strong>
                  {Object.values(overview.api_usage).reduce((sum, api) => sum + api.count, 0)}
                </Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card title="Provider Status Distribution">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="English Proficiency Scores">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={proficiencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="score" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Top Cities">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={cityData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="city" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="count" fill="#52c41a" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Content Statistics */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="Content Generation Details">
            <Row gutter={16}>
              <Col xs={24} sm={6}>
                <Statistic
                  title="With Descriptions"
                  value={stats.content_completion.with_description}
                  suffix={`/ ${stats.content_completion.total}`}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="With Experience"
                  value={stats.content_completion.with_experience}
                  suffix={`/ ${stats.content_completion.total}`}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="With Reviews"
                  value={stats.content_completion.with_reviews}
                  suffix={`/ ${stats.content_completion.total}`}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              <Col xs={24} sm={6}>
                <Statistic
                  title="With SEO"
                  value={stats.content_completion.with_seo}
                  suffix={`/ ${stats.content_completion.total}`}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;