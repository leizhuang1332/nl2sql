'use client';

import React, { useRef, useEffect } from 'react';
import { Card, Spin } from 'antd';
import { BulbOutlined, LoadingOutlined } from '@ant-design/icons';

interface ThinkingDisplayProps {
  thinking: string;
  loading?: boolean;
}

export const ThinkingDisplay: React.FC<ThinkingDisplayProps> = ({
  thinking,
  loading = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [thinking]);

  return (
    <Card
      className="bg-slate-800 border-slate-700"
      title={
        <div className="flex items-center gap-2 text-slate-200">
          {loading ? (
            <LoadingOutlined className="text-yellow-400" />
          ) : (
            <BulbOutlined className="text-yellow-400" />
          )}
          <span className="font-medium">AI 思考过程</span>
        </div>
      }
      bodyStyle={{ padding: 0 }}
    >
      <div
        ref={containerRef}
        className="h-40 overflow-auto p-4 bg-slate-900 rounded-b-lg"
      >
        {thinking ? (
          <pre className="text-sm text-yellow-200 whitespace-pre-wrap font-mono leading-relaxed">
            {thinking}
          </pre>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500">
            <Spin indicator={<LoadingOutlined spin />} tip="思考中..." />
          </div>
        )}
      </div>
    </Card>
  );
};

export default ThinkingDisplay;
