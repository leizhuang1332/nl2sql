'use client';

import React from 'react';
import { Table, Empty } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface ResultsTableProps {
  data: Record<string, unknown>[];
  loading?: boolean;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ data, loading = false }) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8">
        <Empty 
          description={<span className="text-slate-400">No results to display</span>}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    );
  }

  const columns: ColumnsType<Record<string, unknown>> = Object.keys(data[0] || {}).map((key) => ({
    title: (
      <span className="font-mono text-slate-300">{key}</span>
    ),
    dataIndex: key,
    key: key,
    render: (value: unknown) => (
      <span className="font-mono text-slate-200">
        {value === null ? <span className="text-slate-500">NULL</span> : String(value)}
      </span>
    ),
  }));

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
      <Table
        dataSource={data.map((row, index) => ({ ...row, key: index }))}
        columns={columns}
        loading={loading}
        pagination={{ 
          pageSize: 10, 
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} rows`,
        }}
        scroll={{ x: 'max-content' }}
        size="small"
        className="results-table"
      />
    </div>
  );
};

export default ResultsTable;
