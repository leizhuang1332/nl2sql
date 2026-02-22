'use client';

import React, { useState } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined, LoadingOutlined } from '@ant-design/icons';

const { TextArea } = Input;

interface QueryInputProps {
  onSubmit: (query: string) => void;
  loading?: boolean;
  disabled?: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({ 
  onSubmit, 
  loading = false,
  disabled = false 
}) => {
  const [value, setValue] = useState('');

  const handleSubmit = () => {
    if (value.trim() && !loading && !disabled) {
      onSubmit(value.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <TextArea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter your question in natural language... (⌘+Enter to submit)"
        autoSize={{ minRows: 3, maxRows: 6 }}
        disabled={disabled}
        className="font-mono text-sm"
      />
      <div className="flex justify-end">
        <Button 
          type="primary" 
          icon={loading ? <LoadingOutlined /> : <SendOutlined />}
          onClick={handleSubmit}
          loading={loading}
          disabled={disabled || !value.trim()}
          className="bg-green-500 hover:bg-green-600 border-green-500"
        >
          {loading ? 'Processing...' : 'Generate SQL'}
        </Button>
      </div>
    </div>
  );
};

export default QueryInput;
