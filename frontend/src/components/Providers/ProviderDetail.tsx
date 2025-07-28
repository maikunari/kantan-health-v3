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

  // Initialize form with provider data when component mounts or provider changes
  React.useEffect(() => {
    if (provider) {
      // Map provider data to form field names
      const formData = {
        ...provider,
        // Map frontend field names to API field names
        proficiency_score: provider.english_proficiency_score,
        english_experience_summary: provider.ai_english_experience,
        review_summary: provider.ai_review_summary,
        seo_meta_description: provider.seo_description,
      };
      form.setFieldsValue(formData);
    }
  }, [provider, form]);

  const handleEdit = () => {
    setEditing(true);
    // Use the same mapping as in useEffect
    const formData = {
      ...provider,
      proficiency_score: provider.english_proficiency_score,
      english_experience_summary: provider.ai_english_experience,
      review_summary: provider.ai_review_summary,
      seo_meta_description: provider.seo_description,
    };
    form.setFieldsValue(formData);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      console.log('Form values to be sent:', values);
      console.log('API URL:', `${API_ENDPOINTS.PROVIDERS}/${provider.id}`);
      
      await api.put(`${API_ENDPOINTS.PROVIDERS}/${provider.id}`, values);
      
      message.success('Provider updated successfully');
      setEditing(false);
      onUpdate();
    } catch (error: any) {
      console.error('Save error:', error);
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

  const getProficiencyColor = (score: number) => {
    if (score >= 4) return 'green';
    if (score === 3) return 'orange';
    return 'red';
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

      <Form form={form} layout="vertical" disabled={!editing} initialValues={provider}>
        {/* Basic Information */}
        <Card title="Basic Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item label="Provider Name" name="provider_name">
                {editing ? <Input /> : <Text>{provider?.provider_name}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="City" name="city">
                {editing ? <Input /> : <Text>{provider?.city}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Ward" name="ward">
                {editing ? <Input /> : <Text>{provider?.ward || 'Not specified'}</Text>}
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="Address" name="address">
                {editing ? <TextArea rows={2} /> : <Text>{provider?.address}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Phone" name="phone">
                {editing ? <Input prefix={<PhoneOutlined />} /> : <Text>{provider?.phone || 'Not provided'}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Website" name="website">
                {editing ? <Input prefix={<GlobalOutlined />} /> : <Text>{provider?.website || 'Not provided'}</Text>}
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Medical Information */}
        <Card title="Medical Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item label="Specialties" name="specialties">
                {editing ? <TextArea rows={2} /> : <Text>{Array.isArray(provider?.specialties) ? provider.specialties.join(', ') : provider?.specialties || 'Not specified'}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="English Proficiency" name="english_proficiency">
                {editing ? (
                  <Select>
                    <Option value="Fluent">Fluent</Option>
                    <Option value="Conversational">Conversational</Option>
                    <Option value="Basic">Basic</Option>
                    <Option value="Unknown">Unknown</Option>
                  </Select>
                ) : <Text>{provider?.english_proficiency || 'Unknown'}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Proficiency Score" name="proficiency_score">
                {editing ? (
                  <Select>
                    <Option value={5}>5 - Fluent</Option>
                    <Option value={4}>4 - Conversational</Option>
                    <Option value={3}>3 - Basic</Option>
                    <Option value={0}>0 - Unknown</Option>
                  </Select>
                ) : <Tag color={getProficiencyColor(provider?.english_proficiency_score || 0)}>Score {provider?.english_proficiency_score || 0}</Tag>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Status" name="status">
                {editing ? (
                  <Select>
                    <Option value="pending">Pending</Option>
                    <Option value="approved">Approved</Option>
                    <Option value="rejected">Rejected</Option>
                  </Select>
                ) : <Tag color={getStatusColor(provider?.status || 'pending')}>{provider?.status?.toUpperCase() || 'PENDING'}</Tag>}
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* AI Generated Content */}
        <Card title="AI Generated Content" style={{ marginBottom: 16 }}>
          <Collapse>
            <Panel header="Description" key="description">
              <Form.Item name="ai_description">
                {editing ? (
                  <TextArea rows={6} placeholder="AI generated description..." />
                ) : (
                  <Text>{provider?.ai_description || 'No description generated yet'}</Text>
                )}
              </Form.Item>
            </Panel>
            <Panel header="English Experience Summary" key="experience">
              <Form.Item name="english_experience_summary">
                {editing ? (
                  <TextArea rows={4} placeholder="AI generated English experience summary..." />
                ) : (
                  <Text>{provider?.ai_english_experience || 'No English experience summary generated yet'}</Text>
                )}
              </Form.Item>
            </Panel>
            <Panel header="Review Summary" key="reviews">
              <Form.Item name="review_summary">
                {editing ? (
                  <TextArea rows={4} placeholder="AI generated review summary..." />
                ) : (
                  <Text>{provider?.ai_review_summary || 'No review summary generated yet'}</Text>
                )}
              </Form.Item>
            </Panel>
          </Collapse>
        </Card>

        {/* Location & Navigation */}
        <Card title="Location & Navigation" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Latitude">
                <Text>{provider?.latitude ? provider.latitude.toFixed(6) : 'Not geocoded'}</Text>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Longitude">
                <Text>{provider?.longitude ? provider.longitude.toFixed(6) : 'Not geocoded'}</Text>
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="Google Place ID">
                <Text copyable={!!provider?.google_place_id}>{provider?.google_place_id || 'Not available'}</Text>
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="Nearest Station">
                <Text>{provider?.nearest_station || 'Not specified'}</Text>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Reviews & Ratings */}
        <Card title="Reviews & Ratings" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Google Rating">
                <Text>{provider?.rating ? `${provider.rating}/5.0` : 'No rating available'}</Text>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Total Reviews">
                <Text>{provider?.total_reviews || 0} reviews</Text>
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="Review Content">
                {provider?.review_content ? (
                  <div style={{ maxHeight: '4.5em', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    <Text>{provider.review_content}</Text>
                  </div>
                ) : (
                  <Text type="secondary">No review content available</Text>
                )}
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Accessibility Information */}
        <Card title="Accessibility Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Wheelchair Accessible">
                <Tag color={provider?.wheelchair_accessible === 'true' ? 'green' : provider?.wheelchair_accessible === 'false' ? 'red' : 'default'}>
                  {provider?.wheelchair_accessible === 'true' ? 'Yes' : provider?.wheelchair_accessible === 'false' ? 'No' : 'Unknown'}
                </Tag>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Parking Available">
                <Tag color={provider?.parking_available === 'true' ? 'green' : provider?.parking_available === 'false' ? 'red' : 'default'}>
                  {provider?.parking_available === 'true' ? 'Yes' : provider?.parking_available === 'false' ? 'No' : 'Unknown'}
                </Tag>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* SEO Information */}
        <Card title="SEO Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item label="SEO Title" name="seo_title">
                {editing ? <Input /> : <Text>{provider?.seo_title || 'No SEO title generated yet'}</Text>}
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="SEO Description" name="seo_meta_description">
                {editing ? <TextArea rows={3} /> : <Text>{provider?.seo_description || 'No SEO description generated yet'}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Focus Keyword" name="seo_focus_keyword">
                {editing ? <Input /> : <Text>{provider?.seo_focus_keyword || 'Not specified'}</Text>}
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="SEO Keywords" name="seo_keywords">
                {editing ? <Input placeholder="keyword1, keyword2, keyword3" /> : <Text>{provider?.seo_keywords || 'Not specified'}</Text>}
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item label="Featured Image URL" name="featured_image_url">
                {editing ? <Input /> : <Text>{provider?.featured_image_url || 'No featured image selected'}</Text>}
              </Form.Item>
            </Col>
          </Row>
        </Card>
      </Form>

      {/* Data Completeness Overview */}
      {!editing && (
        <Card title="Data Completeness">
          <Row gutter={16}>
            <Col span={24} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                <Text strong>Completeness Score: </Text>
                <div style={{ marginLeft: 8, flex: 1 }}>
                  {(() => {
                    const fields = [
                      provider.provider_name, provider.address, provider.city,
                      provider.phone, provider.website, provider.specialties,
                      provider.latitude, provider.longitude, provider.ai_description,
                      provider.seo_title, provider.seo_description
                    ];
                    const completed = fields.filter(f => f !== null && f !== undefined && f !== '').length;
                    const percentage = (completed / fields.length) * 100;
                    return (
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        <div style={{ width: 100, marginRight: 8 }}>
                          <div style={{
                            width: '100%',
                            height: 8,
                            backgroundColor: '#f5f5f5',
                            borderRadius: 4,
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              width: `${percentage}%`,
                              height: '100%',
                              backgroundColor: percentage >= 80 ? '#52c41a' : percentage >= 60 ? '#faad14' : '#f5222d',
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                        </div>
                        <Text strong style={{ color: percentage >= 80 ? '#52c41a' : percentage >= 60 ? '#faad14' : '#f5222d' }}>
                          {Math.round(percentage)}%
                        </Text>
                      </div>
                    );
                  })()
                }
                </div>
              </div>
              <Row gutter={[8, 8]}>
                <Col><Badge status={provider.provider_name ? 'success' : 'error'} text="Name" /></Col>
                <Col><Badge status={provider.address ? 'success' : 'error'} text="Address" /></Col>
                <Col><Badge status={provider.city ? 'success' : 'error'} text="City" /></Col>
                <Col><Badge status={provider.phone ? 'success' : 'error'} text="Phone" /></Col>
                <Col><Badge status={provider.website ? 'success' : 'error'} text="Website" /></Col>
                <Col><Badge status={provider.latitude && provider.longitude ? 'success' : 'error'} text="Location" /></Col>
                <Col><Badge status={provider.ai_description ? 'success' : 'error'} text="Description" /></Col>
                <Col><Badge status={provider.seo_title ? 'success' : 'error'} text="SEO Title" /></Col>
                <Col><Badge status={provider.wheelchair_accessible ? 'success' : 'warning'} text="Accessibility" /></Col>
              </Row>
            </Col>
          </Row>
        </Card>
      )}

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