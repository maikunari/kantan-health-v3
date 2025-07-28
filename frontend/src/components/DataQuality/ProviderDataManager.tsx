import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Checkbox,
  Space,
  Typography,
  Divider,
  message,
  Badge,
  Tag,
} from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  RobotOutlined,
  EnvironmentOutlined,
  PhoneOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import { Provider } from '../../types';
import api from '../../utils/api';
import { API_ENDPOINTS } from '../../config/api';

const { Text, Title } = Typography;

interface ProviderDataManagerProps {
  provider: Provider;
  onUpdate?: () => void;
}

interface FieldGroup {
  key: string;
  title: string;
  icon: React.ReactNode;
  fields: FieldInfo[];
}

interface FieldInfo {
  key: string;
  label: string;
  value: any;
  canRegenerate: boolean;
  type: 'ai' | 'google' | 'location' | 'manual';
}

const ProviderDataManager: React.FC<ProviderDataManagerProps> = ({ provider, onUpdate }) => {
  const [selectedFields, setSelectedFields] = useState<string[]>([]);
  const [regenerating, setRegenerating] = useState(false);

  const fieldGroups: FieldGroup[] = [
    {
      key: 'location',
      title: 'Location Data',
      icon: <EnvironmentOutlined />,
      fields: [
        {
          key: 'location',
          label: 'Coordinates',
          value: provider.latitude && provider.longitude ? `${provider.latitude}, ${provider.longitude}` : null,
          canRegenerate: true,
          type: 'location'
        },
        {
          key: 'nearest_station',
          label: 'Nearest Station',
          value: provider.nearest_station,
          canRegenerate: false,
          type: 'google'
        }
      ]
    },
    {
      key: 'google_data',
      title: 'Google Places Data',
      icon: <GlobalOutlined />,
      fields: [
        {
          key: 'business_hours',
          label: 'Business Hours',
          value: provider.business_hours,
          canRegenerate: true,
          type: 'google'
        },
        {
          key: 'rating',
          label: 'Google Rating',
          value: provider.rating,
          canRegenerate: true,
          type: 'google'
        },
        {
          key: 'total_reviews',
          label: 'Review Count',
          value: provider.total_reviews,
          canRegenerate: true,
          type: 'google'
        },
        {
          key: 'wheelchair_accessible',
          label: 'Wheelchair Access',
          value: provider.wheelchair_accessible,
          canRegenerate: true,
          type: 'google'
        },
        {
          key: 'parking_available',
          label: 'Parking Available',
          value: provider.parking_available,
          canRegenerate: true,
          type: 'google'
        }
      ]
    },
    {
      key: 'ai_content',
      title: 'AI Generated Content',
      icon: <RobotOutlined />,
      fields: [
        {
          key: 'ai_description',
          label: 'Description',
          value: provider.ai_description,
          canRegenerate: true,
          type: 'ai'
        },
        {
          key: 'ai_excerpt',
          label: 'Excerpt',
          value: provider.ai_excerpt,
          canRegenerate: true,
          type: 'ai'
        },
        {
          key: 'seo_title',
          label: 'SEO Title',
          value: provider.seo_title,
          canRegenerate: true,
          type: 'ai'
        },
        {
          key: 'seo_meta_description',
          label: 'SEO Description',
          value: provider.seo_description,
          canRegenerate: true,
          type: 'ai'
        },
        {
          key: 'english_experience_summary',
          label: 'English Experience',
          value: provider.english_experience_summary,
          canRegenerate: true,
          type: 'ai'
        },
        {
          key: 'review_summary',
          label: 'Review Summary',
          value: provider.review_summary,
          canRegenerate: true,
          type: 'ai'
        }
      ]
    },
    {
      key: 'contact',
      title: 'Contact Information',
      icon: <PhoneOutlined />,
      fields: [
        {
          key: 'phone',
          label: 'Phone Number',
          value: provider.phone,
          canRegenerate: false,
          type: 'manual'
        },
        {
          key: 'website',
          label: 'Website',
          value: provider.website,
          canRegenerate: false,
          type: 'manual'
        }
      ]
    }
  ];

  const getFieldStatus = (field: FieldInfo) => {
    if (field.value === null || field.value === undefined || field.value === '') {
      return { status: 'error', text: 'Missing' };
    }
    
    if (field.type === 'location' && field.key === 'location') {
      // Special handling for coordinates
      return { status: 'success', text: 'Complete' };
    }
    
    if (typeof field.value === 'object') {
      return { status: 'success', text: 'Complete' };
    }
    
    if (typeof field.value === 'string' && field.value.length > 0) {
      return { status: 'success', text: 'Complete' };
    }
    
    if (typeof field.value === 'number' && field.value > 0) {
      return { status: 'success', text: 'Complete' };
    }
    
    return { status: 'warning', text: 'Partial' };
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'ai': return 'purple';
      case 'google': return 'blue';
      case 'location': return 'green';
      case 'manual': return 'orange';
      default: return 'default';
    }
  };

  const handleFieldSelection = (fieldKey: string, checked: boolean) => {
    if (checked) {
      setSelectedFields([...selectedFields, fieldKey]);
    } else {
      setSelectedFields(selectedFields.filter(key => key !== fieldKey));
    }
  };

  const handleSelectByType = (type: string) => {
    const fieldsOfType = fieldGroups
      .flatMap(group => group.fields)
      .filter(field => field.type === type && field.canRegenerate)
      .map(field => field.key);
    
    setSelectedFields(prev => {
      const newFields = new Set([...prev, ...fieldsOfType]);
      return Array.from(newFields);
    });
  };

  const handleRegenerateSelected = async () => {
    if (selectedFields.length === 0) {
      message.warning('Please select fields to regenerate');
      return;
    }

    try {
      setRegenerating(true);
      message.info(`Regenerating ${selectedFields.length} fields...`);

      const response = await api.post(`${API_ENDPOINTS.DATA_COMPLETION_PROVIDER_FIELDS}/${provider.id}/fields`, {
        fields: selectedFields
      });

      if (response.data.success) {
        message.success(response.data.message);
        setSelectedFields([]);
        if (onUpdate) {
          onUpdate();
        }
      } else {
        message.error(response.data.message || 'Failed to regenerate fields');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Unknown error occurred';
      message.error(`Failed to regenerate fields: ${errorMessage}`);
    } finally {
      setRegenerating(false);
    }
  };

  const calculateGroupCompleteness = (group: FieldGroup) => {
    const completedFields = group.fields.filter(field => {
      const status = getFieldStatus(field);
      return status.status === 'success';
    });
    return Math.round((completedFields.length / group.fields.length) * 100);
  };

  return (
    <Card title="Data Manager" extra={
      <Space>
        <Text type="secondary">{selectedFields.length} fields selected</Text>
        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={handleRegenerateSelected}
          loading={regenerating}
          disabled={selectedFields.length === 0}
        >
          Regenerate Selected
        </Button>
      </Space>
    }>
      {/* Quick Selection */}
      <div style={{ marginBottom: 16 }}>
        <Text strong>Quick Select: </Text>
        <Space size="small">
          <Button size="small" onClick={() => handleSelectByType('ai')}>
            All AI Fields
          </Button>
          <Button size="small" onClick={() => handleSelectByType('google')}>
            All Google Fields
          </Button>
          <Button size="small" onClick={() => handleSelectByType('location')}>
            Location Data
          </Button>
          <Button size="small" type="dashed" onClick={() => setSelectedFields([])}>
            Clear Selection
          </Button>
        </Space>
      </div>

      <Divider />

      {/* Field Groups */}
      <Row gutter={[16, 16]}>
        {fieldGroups.map(group => {
          const completeness = calculateGroupCompleteness(group);
          return (
            <Col span={12} key={group.key}>
              <Card
                size="small"
                title={
                  <Space>
                    {group.icon}
                    <span>{group.title}</span>
                    <Badge
                      count={`${completeness}%`}
                      style={{
                        backgroundColor: completeness >= 90 ? '#52c41a' : completeness >= 60 ? '#faad14' : '#f5222d'
                      }}
                    />
                  </Space>
                }
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  {group.fields.map(field => {
                    const status = getFieldStatus(field);
                    return (
                      <div key={field.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ flex: 1 }}>
                          <Space>
                            <Checkbox
                              checked={selectedFields.includes(field.key)}
                              onChange={(e) => handleFieldSelection(field.key, e.target.checked)}
                              disabled={!field.canRegenerate}
                            />
                            <Text style={{ fontSize: '12px' }}>{field.label}</Text>
                            <Tag size="small" color={getTypeColor(field.type)}>
                              {field.type.toUpperCase()}
                            </Tag>
                          </Space>
                        </div>
                        <Badge
                          status={status.status as any}
                          text={status.text}
                          style={{ fontSize: '11px' }}
                        />
                      </div>
                    );
                  })}
                </Space>
              </Card>
            </Col>
          );
        })}
      </Row>
    </Card>
  );
};

export default ProviderDataManager;