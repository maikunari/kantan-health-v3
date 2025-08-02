import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Button, Space, Typography, Badge } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  SyncOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HeartOutlined,
  SettingOutlined,
  ApiOutlined,
  PlusOutlined,
  HistoryOutlined,
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

  const mainMenuItems = [
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
      key: '/sync',
      icon: <SyncOutlined />,
      label: 'WordPress Sync',
    },
  ];

  const utilityMenuItems = [
    {
      key: '/activity-log',
      icon: <HistoryOutlined />,
      label: 'Activity Log',
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
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ 
          padding: '16px', 
          textAlign: 'center',
          borderBottom: '1px solid #f0f0f0',
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
        
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={mainMenuItems}
            onClick={handleMenuClick}
            style={{ border: 'none', flex: 1 }}
          />
          
          <div style={{ 
            borderTop: '1px solid #f0f0f0', 
            marginTop: 'auto',
            paddingTop: '8px',
            paddingBottom: '8px'
          }}>
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              items={utilityMenuItems}
              onClick={handleMenuClick}
              style={{ border: 'none' }}
            />
          </div>
        </div>
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