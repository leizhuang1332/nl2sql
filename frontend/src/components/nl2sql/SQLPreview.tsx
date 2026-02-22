'use client';

import React from 'react';
import { Card, Button, message } from 'antd';
import { EditOutlined, PlayCircleOutlined, CopyOutlined } from '@ant-design/icons';

interface SQLPreviewProps {
  sql: string;
  onEdit?: () => void;
  onRun?: () => void;
  loading?: boolean;
}

export const SQLPreview: React.FC<SQLPreviewProps> = ({
  sql,
  onEdit,
  onRun,
  loading = false,
}) => {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      message.success('SQL copied to clipboard');
    } catch {
      message.error('Failed to copy');
    }
  };

  if (!sql) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <div className="text-slate-400 text-center py-8">
          Generated SQL will appear here
        </div>
      </Card>
    );
  }

  return (
    <Card 
      className="bg-slate-800 border-slate-700"
      title={
        <span className="text-slate-200 font-mono text-sm">Generated SQL</span>
      }
      extra={
        <div className="flex gap-2">
          <Button 
            size="small" 
            icon={<EditOutlined />}
            onClick={onEdit}
            disabled={!onEdit}
            className="text-slate-400 hover:text-slate-200"
          >
            Edit
          </Button>
          <Button 
            size="small" 
            icon={<PlayCircleOutlined />}
            onClick={onRun}
            disabled={!onRun || loading}
            className="text-green-400 hover:text-green-300"
          >
            Run
          </Button>
          <Button 
            size="small" 
            icon={<CopyOutlined />}
            onClick={handleCopy}
            className="text-slate-400 hover:text-slate-200"
          >
            Copy
          </Button>
        </div>
      }
    >
      <pre className="font-mono text-sm text-green-400 whitespace-pre-wrap break-words bg-slate-900 p-4 rounded-lg overflow-auto max-h-48">
        {sql}
      </pre>
    </Card>
  );
};

export default SQLPreview;
