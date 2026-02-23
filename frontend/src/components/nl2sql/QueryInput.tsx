'use client';

import React, { useState } from 'react';
import { Input, Button, Progress, Tag } from 'antd';
import { SendOutlined, LoadingOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';

const { TextArea } = Input;

interface QueryInputProps {
  onSubmit: (query: string) => void;
  loading?: boolean;
  disabled?: boolean;
  streaming?: boolean;
  streamStage?: string;
  streamProgress?: number;
}

const STAGE_LABELS: Record<string, string> = {
  semantic_mapping: '语义映射',
  schema_prep: 'Schema 准备',
  sql_generation: 'SQL 生成',
  security: '安全验证',
  execution: '执行查询',
  explaining: '结果解释',
  done: '完成',
};

const STAGE_COLORS: Record<string, string> = {
  semantic_mapping: 'blue',
  schema_prep: 'cyan',
  sql_generation: 'green',
  security: 'orange',
  execution: 'purple',
  explaining: 'magenta',
  done: 'green',
};

export const QueryInput: React.FC<QueryInputProps> = ({ 
  onSubmit, 
  loading = false,
  disabled = false,
  streaming = false,
  streamStage,
  streamProgress,
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

  const currentStageLabel = streamStage ? STAGE_LABELS[streamStage] || streamStage : '';
  const currentStageColor = streamStage ? STAGE_COLORS[streamStage] || 'default' : 'default';

  return (
    <div className="flex flex-col gap-3">
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {loading ? (
              <SyncOutlined spin className="text-green-400" />
            ) : (
              <CheckCircleOutlined className="text-green-400" />
            )}
            <span className="text-sm text-slate-300">处理阶段:</span>
            {currentStageLabel ? (
              <Tag color={currentStageColor}>{currentStageLabel}</Tag>
            ) : (
              <Tag color="default">等待输入</Tag>
            )}
          </div>
          <span className="text-sm text-slate-400">
            {streamProgress !== undefined ? `${streamProgress}%` : '0%'}
          </span>
        </div>
        <Progress 
          percent={streamProgress || 0} 
          size="small" 
          status={loading ? 'active' : 'normal'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
        />
      </div>

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
          {loading ? (streaming ? '处理中...' : '生成中...') : 'Generate SQL'}
        </Button>
      </div>
    </div>
  );
};

export default QueryInput;
