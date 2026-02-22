'use client';

import React, { useState } from 'react';
import { Tree, Input, Typography, Spin } from 'antd';
import { 
  DatabaseOutlined, 
  TableOutlined, 
  ColumnWidthOutlined,
  SearchOutlined,
  LoadingOutlined
} from '@ant-design/icons';

const { Text } = Typography;

// Types
interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  key: boolean;
  default: string | null;
  extra: string;
}

interface TableInfo {
  name: string;
  columns: ColumnInfo[];
}

interface SchemaData {
  tables: TableInfo[];
  tableNames: string[];
}

// Mock data - should be fetched from API
const mockSchemaData: SchemaData = {
  tables: [
    {
      name: 'products',
      columns: [
        { name: 'id', type: 'INTEGER', nullable: false, key: true, default: null, extra: 'AUTOINCREMENT' },
        { name: 'name', type: 'VARCHAR(255)', nullable: false, key: false, default: null, extra: '' },
        { name: 'price', type: 'DECIMAL(10,2)', nullable: false, key: false, default: null, extra: '' },
        { name: 'category', type: 'VARCHAR(100)', nullable: true, key: false, default: null, extra: '' },
        { name: 'stock', type: 'INTEGER', nullable: false, key: false, default: '0', extra: '' },
        { name: 'created_at', type: 'DATETIME', nullable: false, key: false, default: 'CURRENT_TIMESTAMP', extra: '' },
      ],
    },
    {
      name: 'orders',
      columns: [
        { name: 'id', type: 'INTEGER', nullable: false, key: true, default: null, extra: 'AUTOINCREMENT' },
        { name: 'user_id', type: 'INTEGER', nullable: false, key: false, default: null, extra: '' },
        { name: 'total_amount', type: 'DECIMAL(10,2)', nullable: false, key: false, default: null, extra: '' },
        { name: 'status', type: 'VARCHAR(50)', nullable: false, key: false, default: "'pending'", extra: '' },
        { name: 'created_at', type: 'DATETIME', nullable: false, key: false, default: 'CURRENT_TIMESTAMP', extra: '' },
      ],
    },
    {
      name: 'users',
      columns: [
        { name: 'id', type: 'INTEGER', nullable: false, key: true, default: null, extra: 'AUTOINCREMENT' },
        { name: 'username', type: 'VARCHAR(100)', nullable: false, key: false, default: null, extra: '' },
        { name: 'email', type: 'VARCHAR(255)', nullable: false, key: false, default: null, extra: '' },
        { name: 'created_at', type: 'DATETIME', nullable: false, key: false, default: 'CURRENT_TIMESTAMP', extra: '' },
      ],
    },
  ],
  tableNames: ['products', 'orders', 'users'],
};

interface SchemaExplorerProps {
  loading?: boolean;
}

interface TreeNode {
  key: string;
  title: React.ReactNode;
  children?: TreeNode[];
  icon?: React.ReactNode;
}

export const SchemaExplorer: React.FC<SchemaExplorerProps> = ({ loading = false }) => {
  const [searchValue, setSearchValue] = useState('');
  const [expandedKeys, setExpandedKeys] = useState<string[]>(['products', 'orders', 'users']);

  const buildTreeData = (): TreeNode[] => {
    const data: TreeNode[] = [];
    
    mockSchemaData.tables.forEach((table) => {
      if (searchValue && !table.name.toLowerCase().includes(searchValue.toLowerCase())) {
        return;
      }

      const tableChildren = table.columns
        .filter(col => 
          !searchValue || 
          col.name.toLowerCase().includes(searchValue.toLowerCase())
        )
        .map(col => ({
          key: `${table.name}.${col.name}`,
          title: (
            <div className="flex items-center gap-2 py-0.5">
              <ColumnWidthOutlined className="text-xs text-blue-400" />
              <Text code className="text-xs text-slate-400">{col.type}</Text>
              <Text className="text-sm text-slate-200">{col.name}</Text>
              {col.key && <span className="text-xs text-yellow-400 font-medium">PK</span>}
            </div>
          ),
        }));

      data.push({
        key: table.name,
        title: (
          <div className="flex items-center gap-2 py-1">
            <TableOutlined className="text-purple-400" />
            <Text strong className="text-sm text-slate-200">{table.name}</Text>
            <Text type="secondary" className="text-xs">({table.columns.length})</Text>
          </div>
        ),
        children: tableChildren,
      });
    });

    return data;
  };

  const onExpand = (keys: React.Key[]) => {
    setExpandedKeys(keys as string[]);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* Header */}
      <div className="p-3 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-3">
          <DatabaseOutlined className="text-lg text-green-400" />
          <Text strong className="text-slate-200">Schema Explorer</Text>
        </div>
        
        {/* Search */}
        <Input
          prefix={<SearchOutlined className="text-slate-400" />}
          placeholder="Search tables or columns..."
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          className="bg-slate-800 border-slate-700 text-slate-200"
          allowClear
        />
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-auto p-2">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Spin indicator={<LoadingOutlined spin className="text-green-400" />} />
          </div>
        ) : (
          <Tree
            showIcon
            expandedKeys={expandedKeys}
            onExpand={onExpand}
            treeData={buildTreeData()}
            className="bg-transparent text-slate-200"
          />
        )}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-slate-700 text-xs text-slate-400">
        {mockSchemaData.tableNames.length} tables • {mockSchemaData.tables.reduce((acc, t) => acc + t.columns.length, 0)} columns
      </div>
    </div>
  );
};

export default SchemaExplorer;
