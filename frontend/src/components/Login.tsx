import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Layout, Spin } from 'antd';
import { UserOutlined, LockOutlined, HeartOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;
const { Content } = Layout;

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    const success = await login(values.username, values.password);
    setLoading(false);
    
    if (success) {
      // Navigation will be handled by the router due to auth state change
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Card
          style={{
            width: 400,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            borderRadius: 8,
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <HeartOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
            <Title level={2} style={{ margin: 0 }}>
              Healthcare Directory
            </Title>
            <Text type="secondary">Admin Portal</Text>
          </div>

          <Form
            name="login"
            onFinish={onFinish}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: 'Please input your username!' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Username"
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Please input your password!' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Password"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{ width: '100%' }}
              >
                {loading ? <Spin size="small" /> : 'Log in'}
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Healthcare Provider Management System v2.0
            </Text>
          </div>
        </Card>
      </Content>
    </Layout>
  );
};

export default Login;