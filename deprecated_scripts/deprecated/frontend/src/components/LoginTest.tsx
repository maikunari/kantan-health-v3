import React, { useState } from 'react';
import { Form, Input, Button, Card, Alert } from 'antd';
import axios from 'axios';

const LoginTest: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>('');

  const onFinish = async (values: any) => {
    console.log('Login button clicked!', values);
    setMessage('Login button clicked! Check console.');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:5001/api/auth/login', {
        username: values.username,
        password: values.password
      });
      console.log('Login response:', response.data);
      setMessage(`Success: ${JSON.stringify(response.data)}`);
    } catch (error: any) {
      console.error('Login error:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const testAPI = async () => {
    console.log('Testing API connection...');
    setMessage('Testing API...');
    try {
      const response = await axios.get('http://localhost:5001/api');
      console.log('API test response:', response.data);
      setMessage(`API Test Success: ${JSON.stringify(response.data)}`);
    } catch (error: any) {
      console.error('API test error:', error);
      setMessage(`API Test Error: ${error.message}`);
    }
  };

  return (
    <div style={{ padding: '50px', maxWidth: '400px', margin: '0 auto' }}>
      <Card title="Login Test Component">
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item
            label="Username"
            name="username"
            rules={[{ required: true, message: 'Please input your username!' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Password"
            name="password"
            rules={[{ required: true, message: 'Please input your password!' }]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} style={{ marginRight: '10px' }}>
              Test Login
            </Button>
            <Button onClick={testAPI}>
              Test API
            </Button>
          </Form.Item>
        </Form>

        {message && (
          <Alert
            message="Test Result"
            description={message}
            type={message.includes('Error') ? 'error' : 'success'}
            showIcon
            style={{ marginTop: '20px' }}
          />
        )}
      </Card>
    </div>
  );
};

export default LoginTest;