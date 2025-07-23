import React, { useState } from 'react';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Select,
  Typography,
  Space,
  Alert,
  Switch,
  InputNumber,
  Row,
  Col,
  Tag,
  Divider,
  message,
  Progress,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EnvironmentOutlined,
  MedicineBoxOutlined,
  PlayCircleOutlined,
  StopOutlined,
} from '@ant-design/icons';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

interface AddResult {
  success: boolean;
  message: string;
  provider_id?: number;
  details?: any;
}

const AddProviders: React.FC = () => {
  const [specificForm] = Form.useForm();
  const [geographicForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AddResult[]>([]);
  const [progress, setProgress] = useState(0);

  const handleAddSpecific = async (values: any) => {
    setLoading(true);
    setResults([]);
    
    try {
      const payload = {
        ...values,
        full_pipeline: !values.skip_content_generation && !values.skip_wordpress_sync,
        skip_content_generation: values.skip_content_generation || false,
        skip_wordpress_sync: values.skip_wordpress_sync || false,
        dry_run: values.dry_run || false,
      };

      const response = await api.post(API_ENDPOINTS.ADD_SPECIFIC_PROVIDER, payload);
      
      setResults([{
        success: true,
        message: response.data.message,
        provider_id: response.data.provider_id,
        details: response.data.details,
      }]);
      
      message.success('Provider added successfully!');
      if (!values.dry_run) {
        specificForm.resetFields();
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to add provider';
      setResults([{
        success: false,
        message: errorMsg,
      }]);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleAddGeographic = async (values: any) => {
    setLoading(true);
    setResults([]);
    setProgress(0);
    
    try {
      const payload = {
        ...values,
        full_pipeline: !values.skip_content_generation && !values.skip_wordpress_sync,
        skip_content_generation: values.skip_content_generation || false,
        skip_wordpress_sync: values.skip_wordpress_sync || false,
        dry_run: values.dry_run || false,
      };

      // For geographic addition, we'll need to implement progress tracking
      const response = await api.post(API_ENDPOINTS.ADD_GEOGRAPHIC_PROVIDERS, payload);
      
      setResults([{
        success: true,
        message: response.data.message,
        details: response.data.details,
      }]);
      
      message.success('Geographic provider search completed!');
      if (!values.dry_run) {
        geographicForm.resetFields();
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to add providers';
      setResults([{
        success: false,
        message: errorMsg,
      }]);
      message.error(errorMsg);
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Add Healthcare Providers</Title>
        <Paragraph>
          Add individual providers or bulk add by geographic area. The system automatically runs 
          the complete pipeline: <Tag>Google Places Discovery</Tag> → <Tag>AI Content Generation</Tag> → <Tag>WordPress Sync</Tag>
        </Paragraph>
      </div>

      <Tabs defaultActiveKey="specific" size="large">
        {/* Add Specific Provider Tab */}
        <TabPane 
          tab={
            <span>
              <MedicineBoxOutlined />
              Add Specific Provider
            </span>
          } 
          key="specific"
        >
          <Card>
            <Form
              form={specificForm}
              layout="vertical"
              onFinish={handleAddSpecific}
              initialValues={{
                skip_content_generation: false,
                skip_wordpress_sync: false,
                dry_run: false,
              }}
            >
              <Alert
                message="Add Individual Healthcare Provider"
                description="Add a specific provider by Google Place ID (most reliable) or by name and location search."
                type="info"
                style={{ marginBottom: 24 }}
                showIcon
              />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Google Place ID"
                    name="place_id"
                    help="Most reliable method. Format: ChIJN1t_tDeuEmsRUsoyG83frY4"
                  >
                    <Input 
                      placeholder="ChIJN1t_tDeuEmsRUsoyG83frY4" 
                      prefix={<SearchOutlined />}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="OR Provider Name" name="name">
                    <Input 
                      placeholder="Tokyo Medical University Hospital" 
                      prefix={<MedicineBoxOutlined />}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="Location" name="location">
                    <Input 
                      placeholder="Tokyo, Shibuya, etc." 
                      prefix={<EnvironmentOutlined />}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Specialty" name="specialty">
                    <Select placeholder="Select specialty (optional)">
                      <Option value="general">General Medicine</Option>
                      <Option value="cardiology">Cardiology</Option>
                      <Option value="dermatology">Dermatology</Option>
                      <Option value="gynecology">Gynecology</Option>
                      <Option value="pediatrics">Pediatrics</Option>
                      <Option value="psychiatry">Psychiatry</Option>
                      <Option value="dentistry">Dentistry</Option>
                      <Option value="ophthalmology">Ophthalmology</Option>
                      <Option value="orthopedics">Orthopedics</Option>
                      <Option value="ent">ENT</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Pipeline Options">
                    <Space direction="vertical">
                      <Form.Item name="skip_content_generation" valuePropName="checked" noStyle>
                        <Switch size="small" />
                      </Form.Item>
                      <Text style={{ fontSize: '12px' }}>Skip AI Content Generation</Text>
                      
                      <Form.Item name="skip_wordpress_sync" valuePropName="checked" noStyle>
                        <Switch size="small" />
                      </Form.Item>
                      <Text style={{ fontSize: '12px' }}>Skip WordPress Sync</Text>
                      
                      <Form.Item name="dry_run" valuePropName="checked" noStyle>
                        <Switch size="small" />
                      </Form.Item>
                      <Text style={{ fontSize: '12px' }}>Dry Run (Preview Only)</Text>
                    </Space>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  icon={<PlusOutlined />}
                  size="large"
                >
                  Add Provider
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Add Geographic Providers Tab */}
        <TabPane 
          tab={
            <span>
              <EnvironmentOutlined />
              Add by Geographic Area
            </span>
          } 
          key="geographic"
        >
          <Card>
            <Form
              form={geographicForm}
              layout="vertical"
              onFinish={handleAddGeographic}
              initialValues={{
                limit: 10,
                skip_content_generation: false,
                skip_wordpress_sync: false,
                dry_run: false,
              }}
            >
              <Alert
                message="Bulk Add Providers by Geographic Area"
                description="Add multiple providers from specific cities, wards, or regions. Automatically finds healthcare providers in the specified areas."
                type="info"
                style={{ marginBottom: 24 }}
                showIcon
              />

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="City" name="city">
                    <Select 
                      placeholder="Select city"
                      mode="multiple"
                      allowClear
                    >
                      <Option value="Tokyo">Tokyo</Option>
                      <Option value="Osaka">Osaka</Option>
                      <Option value="Yokohama">Yokohama</Option>
                      <Option value="Kyoto">Kyoto</Option>
                      <Option value="Kobe">Kobe</Option>
                      <Option value="Nagoya">Nagoya</Option>
                      <Option value="Fukuoka">Fukuoka</Option>
                      <Option value="Sendai">Sendai</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Tokyo Wards (if Tokyo selected)" name="wards">
                    <Select 
                      placeholder="Select wards (optional)"
                      mode="multiple"
                      allowClear
                    >
                      <Option value="Shibuya">Shibuya</Option>
                      <Option value="Shinjuku">Shinjuku</Option>
                      <Option value="Minato">Minato</Option>
                      <Option value="Chiyoda">Chiyoda</Option>
                      <Option value="Ginza">Ginza</Option>
                      <Option value="Harajuku">Harajuku</Option>
                      <Option value="Roppongi">Roppongi</Option>
                      <Option value="Akihabara">Akihabara</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="Provider Limit" name="limit">
                    <InputNumber 
                      min={1} 
                      max={50} 
                      placeholder="10"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Specialty Filter" name="specialty">
                    <Select placeholder="Filter by specialty (optional)">
                      <Option value="general">General Medicine</Option>
                      <Option value="cardiology">Cardiology</Option>
                      <Option value="dermatology">Dermatology</Option>
                      <Option value="gynecology">Gynecology</Option>
                      <Option value="pediatrics">Pediatrics</Option>
                      <Option value="psychiatry">Psychiatry</Option>
                      <Option value="dentistry">Dentistry</Option>
                      <Option value="ophthalmology">Ophthalmology</Option>
                      <Option value="orthopedics">Orthopedics</Option>
                      <Option value="ent">ENT</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Pipeline Options">
                    <Space direction="vertical">
                      <div>
                        <Form.Item name="skip_content_generation" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Skip AI Content Generation</Text>
                      </div>
                      
                      <div>
                        <Form.Item name="skip_wordpress_sync" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Skip WordPress Sync</Text>
                      </div>
                      
                      <div>
                        <Form.Item name="dry_run" valuePropName="checked" noStyle>
                          <Switch size="small" />
                        </Form.Item>
                        <Text style={{ fontSize: '12px', marginLeft: 8 }}>Dry Run (Preview Only)</Text>
                      </div>
                    </Space>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  icon={<PlayCircleOutlined />}
                  size="large"
                >
                  Start Geographic Search
                </Button>
              </Form.Item>
            </Form>

            {progress > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text>Progress:</Text>
                <Progress percent={progress} status="active" />
              </div>
            )}
          </Card>
        </TabPane>
      </Tabs>

      {/* Results Section */}
      {results.length > 0 && (
        <Card title="Results" style={{ marginTop: 24 }}>
          {results.map((result, index) => (
            <Alert
              key={index}
              message={result.success ? 'Success' : 'Error'}
              description={
                <div>
                  <div>{result.message}</div>
                  {result.provider_id && (
                    <div style={{ marginTop: 8 }}>
                      <Tag>Provider ID: {result.provider_id}</Tag>
                    </div>
                  )}
                  {result.details && (
                    <pre style={{ marginTop: 8, fontSize: '12px', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                      {JSON.stringify(result.details, null, 2)}
                    </pre>
                  )}
                </div>
              }
              type={result.success ? 'success' : 'error'}
              style={{ marginBottom: 8 }}
              showIcon
            />
          ))}
        </Card>
      )}
    </div>
  );
};

export default AddProviders;