import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Button, Space, Typography, Badge } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  FileTextOutlined,
  SyncOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HeartOutlined,
  SettingOutlined,
  ApiOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/providers',
      icon: <UserOutlined />,
      label: 'Providers',
    },
    {
      key: '/add-providers',
      icon: <PlusOutlined />,
      label: 'Add Providers',
    },
    {
      key: '/content',
      icon: <FileTextOutlined />,
      label: 'Content Generation',
    },
    {
      key: '/sync',
      icon: <SyncOutlined />,
      label: 'WordPress Sync',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: logout,
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          background: '#fff',
          boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ 
          padding: '16px', 
          textAlign: 'center',
          borderBottom: '1px solid #f0f0f0',
          marginBottom: '8px'
        }}>
          <HeartOutlined 
            style={{ 
              fontSize: collapsed ? 24 : 32, 
              color: '#1890ff',
              marginBottom: collapsed ? 0 : 8
            }} 
          />
          {!collapsed && (
            <div>
              <Text strong style={{ display: 'block', fontSize: '16px' }}>
                Healthcare
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Directory v2
              </Text>
            </div>
          )}
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ border: 'none' }}
        />
      </Sider>

      <Layout>
        <Header style={{ 
          padding: '0 16px', 
          background: '#fff', 
          boxShadow: '0 1px 4px rgba(0,21,41,.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '16px', width: 64, height: 64 }}
          />

          <Space>
            <Badge dot status="processing">
              <Button 
                type="text" 
                icon={<ApiOutlined />}
                title="API Status"
              />
            </Badge>
            
            <Dropdown 
              menu={{ items: userMenuItems }}
              placement="bottomRight"
            >
              <Space style={{ cursor: 'pointer', padding: '0 8px' }}>
                <Avatar icon={<UserOutlined />} />
                <Text>{user?.username}</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{ 
          margin: '16px',
          padding: '24px',
          background: '#fff',
          borderRadius: '6px',
          overflow: 'auto'
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;