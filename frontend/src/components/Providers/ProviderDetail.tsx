import React, { useState } from 'react';
import {
  Form,
  Input,
  Select,
  Card,
  Row,
  Col,
  Tag,
  Typography,
  Divider,
  Space,
  Button,
  message,
  Collapse,
  Badge,
} from 'antd';
import {
  EditOutlined,
  SaveOutlined,
  SyncOutlined,
  FileTextOutlined,
  GlobalOutlined,
  PhoneOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons';
import { Provider } from '../../types';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;

interface ProviderDetailProps {
  provider: Provider;
  onUpdate: () => void;
}

const ProviderDetail: React.FC<ProviderDetailProps> = ({ provider, onUpdate }) => {
  const [form] = Form.useForm();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleEdit = () => {
    setEditing(true);
    form.setFieldsValue(provider);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      await api.put(`${API_ENDPOINTS.PROVIDERS}/${provider.id}`, values);
      
      message.success('Provider updated successfully');
      setEditing(false);
      onUpdate();
    } catch (error: any) {
      message.error(error.response?.data?.error || 'Failed to update provider');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    form.resetFields();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'green';
      case 'rejected': return 'red';
      case 'pending': return 'orange';
      default: return 'default';
    }
  };

  const getProficiencyBadge = (score: number) => {
    if (score >= 4) return <Badge status="success" text={`Score ${score} - Fluent`} />;
    if (score === 3) return <Badge status="warning" text={`Score ${score} - Basic`} />;
    return <Badge status="error" text={`Score ${score} - Unknown`} />;
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Space align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              {provider.provider_name}
            </Title>
            <Space>
              <Tag color={getStatusColor(provider.status)}>
                {provider.status.toUpperCase()}
              </Tag>
              {provider.wordpress_id && (
                <Tag color="blue">WordPress ID: {provider.wordpress_id}</Tag>
              )}
            </Space>
          </div>
          <Space>
            {!editing ? (
              <Button icon={<EditOutlined />} onClick={handleEdit}>
                Edit
              </Button>
            ) : (
              <>
                <Button onClick={handleCancel}>Cancel</Button>
                <Button 
                  type="primary" 
                  icon={<SaveOutlined />} 
                  onClick={handleSave}
                  loading={loading}
                >
                  Save
                </Button>
              </>
            )}
          </Space>
        </Space>
      </div>

      <Form form={form} layout="vertical" disabled={!editing}>
        {/* Basic Information */}
        <Card title="Basic Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item label="Provider Name" name="provider_name">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="City" name="city">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Ward" name="ward">
                <Input />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="Address" name="address">
                <TextArea rows={2} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Phone" name="phone">
                <Input prefix={<PhoneOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Website" name="website">
                <Input prefix={<GlobalOutlined />} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Medical Information */}
        <Card title="Medical Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item label="Specialties" name="specialties">
                <TextArea rows={2} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="English Proficiency" name="english_proficiency">
                <Select>
                  <Option value="Fluent">Fluent</Option>
                  <Option value="Conversational">Conversational</Option>
                  <Option value="Basic">Basic</Option>
                  <Option value="Unknown">Unknown</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Proficiency Score" name="english_proficiency_score">
                <Select>
                  <Option value={5}>5 - Fluent</Option>
                  <Option value={4}>4 - Conversational</Option>
                  <Option value={3}>3 - Basic</Option>
                  <Option value={0}>0 - Unknown</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Status" name="status">
                <Select>
                  <Option value="pending">Pending</Option>
                  <Option value="approved">Approved</Option>
                  <Option value="rejected">Rejected</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* AI Generated Content */}
        <Card title="AI Generated Content" style={{ marginBottom: 16 }}>
          <Collapse>
            <Panel header="Description" key="description">
              <Form.Item name="ai_description">
                <TextArea rows={6} placeholder="AI generated description..." />
              </Form.Item>
            </Panel>
            <Panel header="English Experience Summary" key="experience">
              <Form.Item name="ai_english_experience">
                <TextArea rows={4} placeholder="AI generated English experience summary..." />
              </Form.Item>
            </Panel>
            <Panel header="Review Summary" key="reviews">
              <Form.Item name="ai_review_summary">
                <TextArea rows={4} placeholder="AI generated review summary..." />
              </Form.Item>
            </Panel>
          </Collapse>
        </Card>

        {/* SEO Information */}
        <Card title="SEO Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item label="SEO Title" name="seo_title">
                <Input />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="SEO Description" name="seo_description">
                <TextArea rows={3} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Focus Keyword" name="seo_focus_keyword">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="SEO Keywords" name="seo_keywords">
                <Input placeholder="keyword1, keyword2, keyword3" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="Featured Image URL" name="featured_image_url">
                <Input />
              </Form.Item>
            </Col>
          </Row>
        </Card>
      </Form>

      {/* Read-only Information */}
      {!editing && (
        <Card title="System Information">
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>Provider ID:</Text>
              <div>{provider.id}</div>
            </Col>
            <Col span={12}>
              <Text strong>WordPress ID:</Text>
              <div>{provider.wordpress_id || 'Not synced'}</div>
            </Col>
            <Col span={12}>
              <Text strong>Created At:</Text>
              <div>
                {provider.created_at 
                  ? new Date(provider.created_at).toLocaleDateString()
                  : 'Unknown'
                }
              </div>
            </Col>
            <Col span={12}>
              <Text strong>Last Synced:</Text>
              <div>
                {provider.last_synced 
                  ? new Date(provider.last_synced).toLocaleDateString()
                  : 'Never'
                }
              </div>
            </Col>
            <Col span={24} style={{ marginTop: 16 }}>
              <Text strong>English Proficiency:</Text>
              <div style={{ marginTop: 8 }}>
                {getProficiencyBadge(provider.english_proficiency_score)}
              </div>
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default ProviderDetail;