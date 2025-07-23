import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Form,
  Input,
  Typography,
  Space,
  Divider,
  Alert,
  message,
  Collapse,
  Badge,
  Spin,
  Tooltip,
} from 'antd';
import {
  SettingOutlined,
  TestOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
  SaveOutlined,
  ReloadOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { Password } = Input;

interface ConfigData {
  wordpress: {
    url: string;
    username: string;
    password_masked: string;
    password_set: boolean;
  };
  google_api: {
    places_api_key_masked: string;
    places_api_key_set: boolean;
  };
  claude_api: {
    api_key_masked: string;
    api_key_set: boolean;
  };
  admin: {
    password_set: boolean;
    secret_key_set: boolean;
  };
}

interface TestResult {
  success: boolean;
  message?: string;
  error?: string;
  user_info?: any;
  test_response?: string;
  usage?: any;
  quota_info?: any;
}

const Settings: React.FC = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});

  const [wordpressForm] = Form.useForm();
  const [googleForm] = Form.useForm();
  const [claudeForm] = Form.useForm();
  const [adminForm] = Form.useForm();

  useEffect(() => {
    fetchConfig();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchConfig, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await api.get(API_ENDPOINTS.SETTINGS_CONFIG);
      setConfig(response.data);
      
      // Update form values
      wordpressForm.setFieldsValue({
        url: response.data.wordpress.url,
        username: response.data.wordpress.username,
      });
    } catch (error: any) {
      console.error('Failed to fetch configuration:', error);
      message.error('Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const updateWordPressConfig = async (values: any) => {
    try {
      setSaving('wordpress');
      await api.put(API_ENDPOINTS.SETTINGS_UPDATE_WORDPRESS, values);
      message.success('WordPress configuration updated successfully');
      fetchConfig();
    } catch (error: any) {
      console.error('WordPress config update failed:', error);
      message.error(error.response?.data?.error || 'Failed to update WordPress configuration');
    } finally {
      setSaving(null);
    }
  };

  const updateGoogleConfig = async (values: any) => {
    try {
      setSaving('google');
      await api.put(API_ENDPOINTS.SETTINGS_UPDATE_GOOGLE, values);
      message.success('Google API configuration updated successfully');
      fetchConfig();
    } catch (error: any) {
      console.error('Google API config update failed:', error);
      message.error(error.response?.data?.error || 'Failed to update Google API configuration');
    } finally {
      setSaving(null);
    }
  };

  const updateClaudeConfig = async (values: any) => {
    try {
      setSaving('claude');
      await api.put(API_ENDPOINTS.SETTINGS_UPDATE_CLAUDE, values);
      message.success('Claude API configuration updated successfully');
      fetchConfig();
    } catch (error: any) {
      console.error('Claude API config update failed:', error);
      message.error(error.response?.data?.error || 'Failed to update Claude API configuration');
    } finally {
      setSaving(null);
    }
  };

  const updateAdminConfig = async (values: any) => {
    try {
      setSaving('admin');
      await api.put(API_ENDPOINTS.SETTINGS_UPDATE_ADMIN, values);
      message.success('Admin configuration updated successfully');
      fetchConfig();
    } catch (error: any) {
      console.error('Admin config update failed:', error);
      message.error(error.response?.data?.error || 'Failed to update admin configuration');
    } finally {
      setSaving(null);
    }
  };

  const testConnection = async (type: 'wordpress' | 'google' | 'claude') => {
    try {
      setTesting(type);
      let endpoint = '';
      
      switch (type) {
        case 'wordpress':
          endpoint = API_ENDPOINTS.SETTINGS_TEST_WORDPRESS;
          break;
        case 'google':
          endpoint = API_ENDPOINTS.SETTINGS_TEST_GOOGLE;
          break;
        case 'claude':
          endpoint = API_ENDPOINTS.SETTINGS_TEST_CLAUDE;
          break;
      }
      
      const response = await api.post(endpoint);
      setTestResults(prev => ({
        ...prev,
        [type]: response.data
      }));
      
      if (response.data.success) {
        message.success(`${type} connection test successful!`);
      } else {
        message.warning(`${type} connection test failed: ${response.data.error}`);
      }
    } catch (error: any) {
      console.error(`${type} test failed:`, error);
      const errorMsg = error.response?.data?.error || `Failed to test ${type} connection`;
      setTestResults(prev => ({
        ...prev,
        [type]: { success: false, error: errorMsg }
      }));
      message.error(errorMsg);
    } finally {
      setTesting(null);
    }
  };

  const downloadBackup = async () => {
    try {
      const response = await api.get(API_ENDPOINTS.SETTINGS_BACKUP);
      const backup = JSON.stringify(response.data, null, 2);
      const blob = new Blob([backup], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `healthcare-directory-config-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      message.success('Configuration backup downloaded');
    } catch (error: any) {
      console.error('Backup failed:', error);
      message.error('Failed to create backup');
    }
  };

  const togglePasswordVisibility = (field: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const getStatusBadge = (isConfigured: boolean, testResult?: TestResult) => {
    if (testResult) {
      return testResult.success ? (
        <Badge status="success" text="Connected" />
      ) : (
        <Badge status="error" text="Connection Failed" />
      );
    }
    
    return isConfigured ? (
      <Badge status="processing" text="Configured" />
    ) : (
      <Badge status="default" text="Not Configured" />
    );
  };

  if (loading || !config) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading settings...</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <SettingOutlined style={{ marginRight: 8 }} />
          System Configuration
        </Title>
        <Paragraph type="secondary">
          Manage API keys and service configurations for the healthcare directory system.
          All sensitive data is encrypted and stored securely.
        </Paragraph>
      </div>

      {/* Action Bar */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchConfig}
            loading={loading}
          >
            Refresh Config
          </Button>
          <Button 
            icon={<DownloadOutlined />} 
            onClick={downloadBackup}
          >
            Download Backup
          </Button>
        </Space>
      </Card>

      {/* Configuration Sections */}
      <Collapse defaultActiveKey={['wordpress']}>
        
        {/* WordPress Configuration */}
        <Panel 
          header={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>WordPress Integration</span>
              {getStatusBadge(config.wordpress.password_set, testResults.wordpress)}
            </div>
          } 
          key="wordpress"
        >
          <Form
            form={wordpressForm}
            layout="vertical"
            onFinish={updateWordPressConfig}
          >
            <Alert
              message="WordPress REST API Configuration"
              description="Configure connection to your WordPress site for automatic content publishing."
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item
                  label="WordPress Site URL"
                  name="url"
                  rules={[
                    { required: true, message: 'WordPress URL is required' },
                    { type: 'url', message: 'Please enter a valid URL' }
                  ]}
                >
                  <Input 
                    placeholder="https://your-wordpress-site.com"
                    prefix="🌐"
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="Username"
                  name="username"
                  rules={[{ required: true, message: 'Username is required' }]}
                >
                  <Input 
                    placeholder="WordPress username"
                    prefix="👤"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item
                  label={
                    <span>
                      Application Password
                      {config.wordpress.password_set && (
                        <Text type="secondary" style={{ marginLeft: 8 }}>
                          (Currently: {config.wordpress.password_masked})
                        </Text>
                      )}
                    </span>
                  }
                  name="password"
                  rules={!config.wordpress.password_set ? [
                    { required: true, message: 'Application password is required' }
                  ] : []}
                >
                  <Password 
                    placeholder={config.wordpress.password_set ? "Enter new password (optional)" : "WordPress application password"}
                    visibilityToggle={{
                      visible: showPasswords.wordpress,
                      onVisibleChange: () => togglePasswordVisibility('wordpress'),
                    }}
                  />
                </Form.Item>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Generate an application password in WordPress Admin → Users → Profile
                </Text>
              </Col>
            </Row>

            {testResults.wordpress && (
              <Alert
                message={testResults.wordpress.success ? "Connection Test Successful" : "Connection Test Failed"}
                description={
                  testResults.wordpress.success ? (
                    <div>
                      <Text strong>Connected as:</Text> {testResults.wordpress.user_info?.name}<br/>
                      <Text strong>Email:</Text> {testResults.wordpress.user_info?.email}<br/>
                      <Text strong>Roles:</Text> {testResults.wordpress.user_info?.roles?.join(', ')}
                    </div>
                  ) : (
                    testResults.wordpress.error
                  )
                }
                type={testResults.wordpress.success ? "success" : "error"}
                style={{ marginBottom: 16 }}
              />
            )}

            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                icon={<SaveOutlined />}
                loading={saving === 'wordpress'}
              >
                Save Configuration
              </Button>
              <Button 
                icon={<TestOutlined />}
                onClick={() => testConnection('wordpress')}
                loading={testing === 'wordpress'}
              >
                Test Connection
              </Button>
            </Space>
          </Form>
        </Panel>

        {/* Google API Configuration */}
        <Panel 
          header={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Google Places API</span>
              {getStatusBadge(config.google_api.places_api_key_set, testResults.google)}
            </div>
          } 
          key="google"
        >
          <Form
            form={googleForm}
            layout="vertical"
            onFinish={updateGoogleConfig}
          >
            <Alert
              message="Google Places API Configuration"
              description="API key for collecting healthcare provider data from Google Places. Requires Places API and Places Photos API enabled."
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Row gutter={16}>
              <Col xs={24} md={16}>
                <Form.Item
                  label={
                    <span>
                      Google Places API Key
                      {config.google_api.places_api_key_set && (
                        <Text type="secondary" style={{ marginLeft: 8 }}>
                          (Currently: {config.google_api.places_api_key_masked})
                        </Text>
                      )}
                    </span>
                  }
                  name="places_api_key"
                  rules={!config.google_api.places_api_key_set ? [
                    { required: true, message: 'Google Places API key is required' },
                    { pattern: /^AIza/, message: 'Invalid Google API key format' }
                  ] : [
                    { pattern: /^AIza/, message: 'Invalid Google API key format' }
                  ]}
                >
                  <Password 
                    placeholder={config.google_api.places_api_key_set ? "Enter new API key (optional)" : "AIzaSyDaxKYWh-94rc18EQPHHTfPymRjGQP4Jlc"}
                    visibilityToggle={{
                      visible: showPasswords.google,
                      onVisibleChange: () => togglePasswordVisibility('google'),
                    }}
                  />
                </Form.Item>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Get your API key from Google Cloud Console → APIs & Services → Credentials
                </Text>
              </Col>
            </Row>

            {testResults.google && (
              <Alert
                message={testResults.google.success ? "API Test Successful" : "API Test Failed"}
                description={
                  testResults.google.success ? (
                    <div>
                      <Text strong>Status:</Text> {testResults.google.quota_info?.status}<br/>
                      <Text strong>Test Results:</Text> Found {testResults.google.quota_info?.results_count} hospitals in Tokyo
                    </div>
                  ) : (
                    testResults.google.error
                  )
                }
                type={testResults.google.success ? "success" : "error"}
                style={{ marginBottom: 16 }}
              />
            )}

            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                icon={<SaveOutlined />}
                loading={saving === 'google'}
              >
                Save Configuration
              </Button>
              <Button 
                icon={<TestOutlined />}
                onClick={() => testConnection('google')}
                loading={testing === 'google'}
              >
                Test API
              </Button>
            </Space>
          </Form>
        </Panel>

        {/* Claude API Configuration */}
        <Panel 
          header={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Claude AI API</span>
              {getStatusBadge(config.claude_api.api_key_set, testResults.claude)}
            </div>
          } 
          key="claude"
        >
          <Form
            form={claudeForm}
            layout="vertical"
            onFinish={updateClaudeConfig}
          >
            <Alert
              message="Claude AI API Configuration"
              description="Anthropic API key for AI-powered content generation, including descriptions, SEO content, and review summaries."
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Row gutter={16}>
              <Col xs={24} md={16}>
                <Form.Item
                  label={
                    <span>
                      Claude API Key
                      {config.claude_api.api_key_set && (
                        <Text type="secondary" style={{ marginLeft: 8 }}>
                          (Currently: {config.claude_api.api_key_masked})
                        </Text>
                      )}
                    </span>
                  }
                  name="api_key"
                  rules={!config.claude_api.api_key_set ? [
                    { required: true, message: 'Claude API key is required' },
                    { pattern: /^sk-ant-/, message: 'Invalid Claude API key format' }
                  ] : [
                    { pattern: /^sk-ant-/, message: 'Invalid Claude API key format' }
                  ]}
                >
                  <Password 
                    placeholder={config.claude_api.api_key_set ? "Enter new API key (optional)" : "sk-ant-api03-..."}
                    visibilityToggle={{
                      visible: showPasswords.claude,
                      onVisibleChange: () => togglePasswordVisibility('claude'),
                    }}
                  />
                </Form.Item>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Get your API key from Anthropic Console → API Keys
                </Text>
              </Col>
            </Row>

            {testResults.claude && (
              <Alert
                message={testResults.claude.success ? "API Test Successful" : "API Test Failed"}
                description={
                  testResults.claude.success ? (
                    <div>
                      <Text strong>Model:</Text> {testResults.claude.model}<br/>
                      <Text strong>Test Response:</Text> {testResults.claude.test_response}<br/>
                      <Text strong>Usage:</Text> {testResults.claude.usage?.input_tokens} input, {testResults.claude.usage?.output_tokens} output tokens
                    </div>
                  ) : (
                    testResults.claude.error
                  )
                }
                type={testResults.claude.success ? "success" : "error"}
                style={{ marginBottom: 16 }}
              />
            )}

            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                icon={<SaveOutlined />}
                loading={saving === 'claude'}
              >
                Save Configuration
              </Button>
              <Button 
                icon={<TestOutlined />}
                onClick={() => testConnection('claude')}
                loading={testing === 'claude'}
              >
                Test API
              </Button>
            </Space>
          </Form>
        </Panel>

        {/* Admin Configuration */}
        <Panel 
          header={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Admin Settings</span>
              <Badge 
                status={config.admin.password_set && config.admin.secret_key_set ? "success" : "warning"} 
                text={config.admin.password_set && config.admin.secret_key_set ? "Configured" : "Incomplete"} 
              />
            </div>
          } 
          key="admin"
        >
          <Form
            form={adminForm}
            layout="vertical"
            onFinish={updateAdminConfig}
          >
            <Alert
              message="Admin Security Configuration"
              description="Update admin password and Flask secret key for enhanced security."
              type="warning"
              style={{ marginBottom: 16 }}
            />

            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item
                  label="Admin Password"
                  name="password"
                  rules={[
                    { min: 6, message: 'Password must be at least 6 characters' }
                  ]}
                >
                  <Password 
                    placeholder={config.admin.password_set ? "Enter new password (optional)" : "New admin password"}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  label="Flask Secret Key"
                  name="secret_key"
                  rules={[
                    { min: 16, message: 'Secret key must be at least 16 characters' }
                  ]}
                >
                  <Password 
                    placeholder={config.admin.secret_key_set ? "Enter new secret key (optional)" : "New Flask secret key"}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Button 
              type="primary" 
              htmlType="submit" 
              icon={<SaveOutlined />}
              loading={saving === 'admin'}
            >
              Update Admin Settings
            </Button>
          </Form>
        </Panel>

      </Collapse>
    </div>
  );
};

export default Settings;