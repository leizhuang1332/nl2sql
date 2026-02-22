'use client';

import React from 'react';
import { Select, Dropdown, Button, Badge } from 'antd';
import { DatabaseOutlined, HistoryOutlined, SettingOutlined } from '@ant-design/icons';

interface HeaderProps {
  databases?: string[];
  selectedDatabase?: string;
  onDatabaseChange?: (db: string) => void;
  history?: { id: string; question: string; timestamp: Date }[];
  onHistorySelect?: (id: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  databases = ['example.db'],
  selectedDatabase = 'example.db',
  onDatabaseChange,
  history = [],
  onHistorySelect,
}) => {
  const historyItems = history.map((item) => ({
    key: item.id,
    label: (
      <div className="max-w-xs truncate text-sm">
        {item.question}
      </div>
    ),
    onClick: () => onHistorySelect?.(item.id),
  }));

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <DatabaseOutlined className="text-green-400 text-lg" />
          <Select
            value={selectedDatabase}
            onChange={onDatabaseChange}
            options={databases.map((db) => ({ value: db, label: db }))}
            className="w-48"
            dropdownStyle={{ backgroundColor: '#1E293B' }}
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Dropdown 
          menu={{ items: historyItems }} 
          disabled={history.length === 0}
          placement="bottomRight"
        >
          <Button 
            icon={<HistoryOutlined />}
            className="text-slate-400 hover:text-slate-200"
          >
            History
            {history.length > 0 && (
              <Badge count={history.length} size="small" className="ml-2" />
            )}
          </Button>
        </Dropdown>
        <Button 
          icon={<SettingOutlined />}
          className="text-slate-400 hover:text-slate-200"
        />
      </div>
    </div>
  );
};

export default Header;
