'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Tree, Input, Typography, Spin, Empty } from 'antd';
import { 
  DatabaseOutlined, 
  TableOutlined, 
  ColumnWidthOutlined,
  SearchOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { nl2sqlApi } from '@/lib/api';

const { Text } = Typography;

interface TableData {
  name: string;
  columns: { name: string; type: string }[];
}

interface SchemaExplorerProps {
  loading?: boolean;
}

interface TreeNode {
  key: string;
  title: React.ReactNode;
  children?: TreeNode[];
  icon?: React.ReactNode;
}

export const SchemaExplorer: React.FC<SchemaExplorerProps> = ({ loading: externalLoading = false }) => {
  const [searchValue, setSearchValue] = useState('');
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [tables, setTables] = useState<TableData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSchema = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const tableList = await nl2sqlApi.getTables();
      const tableNames = tableList.tables;
      
      const tableDataPromises = tableNames.map(async (tableName) => {
        try {
          const schemaResponse = await nl2sqlApi.getSchema(tableName);
          return {
            name: tableName,
            columns: schemaResponse.schema.columns || []
          };
        } catch {
          return {
            name: tableName,
            columns: []
          };
        }
      });

      const tableData = await Promise.all(tableDataPromises);
      setTables(tableData);
      setExpandedKeys(tableNames);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load schema');
      console.error('Failed to load schema:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSchema();
  }, [loadSchema]);

  const buildTreeData = (): TreeNode[] => {
    const data: TreeNode[] = [];
    
    tables.forEach((table) => {
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

  const isLoadingFinal = externalLoading || isLoading;
  const totalColumns = tables.reduce((acc, t) => acc + t.columns.length, 0);

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <div className="p-3 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-3">
          <DatabaseOutlined className="text-lg text-green-400" />
          <Text strong className="text-slate-200">Schema Explorer</Text>
        </div>
        
        <Input
          prefix={<SearchOutlined className="text-slate-400" />}
          placeholder="Search tables or columns..."
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          className="bg-slate-800 border-slate-700 text-slate-200"
          allowClear
          disabled={isLoadingFinal}
        />
      </div>

      <div className="flex-1 overflow-auto p-2">
        {isLoadingFinal ? (
          <div className="flex items-center justify-center h-32">
            <Spin indicator={<LoadingOutlined spin className="text-green-400" />} />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <ExclamationCircleOutlined className="text-red-400 text-xl mb-2" />
            <Text type="secondary" className="text-xs text-red-400">{error}</Text>
          </div>
        ) : tables.length === 0 ? (
          <Empty description="No tables found" className="text-slate-400" />
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

      <div className="p-2 border-t border-slate-700 text-xs text-slate-400">
        {tables.length} tables • {totalColumns} columns
      </div>
    </div>
  );
};

export default SchemaExplorer;
