'use client';

import React, { useState } from 'react';
import { message } from 'antd';
import Header from '@/components/nl2sql/Header';
import SchemaExplorer from '@/components/nl2sql/SchemaExplorer';
import QueryInput from '@/components/nl2sql/QueryInput';
import SQLPreview from '@/components/nl2sql/SQLPreview';
import ResultsTable from '@/components/nl2sql/ResultsTable';
import HybridLayout from '@/components/nl2sql/HybridLayout';

interface HistoryItem {
  id: string;
  question: string;
  sql: string;
  timestamp: Date;
}

export default function Home() {
  const [selectedDb, setSelectedDb] = useState('example.db');
  const [query, setQuery] = useState('');
  const [sql, setSql] = useState('');
  const [results, setResults] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const handleQuerySubmit = async (question: string) => {
    setQuery(question);
    setLoading(true);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const mockSql = `SELECT * FROM products WHERE category = 'Electronics' ORDER BY price DESC;`;
      const mockResults = [
        { id: 1, name: 'Laptop Pro', price: 1299.99, category: 'Electronics', stock: 50 },
        { id: 2, name: 'Wireless Mouse', price: 29.99, category: 'Electronics', stock: 200 },
        { id: 3, name: 'USB-C Hub', price: 49.99, category: 'Electronics', stock: 150 },
      ];
      
      setSql(mockSql);
      setResults(mockResults);
      
      const newHistory: HistoryItem = {
        id: Date.now().toString(),
        question,
        sql: mockSql,
        timestamp: new Date(),
      };
      setHistory(prev => [newHistory, ...prev]);
      
      message.success('Query executed successfully!');
    } catch (error) {
      message.error('Failed to execute query');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunQuery = async () => {
    if (!sql) return;
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const mockResults = [
        { id: 1, name: 'Laptop Pro', price: 1299.99, category: 'Electronics', stock: 50 },
        { id: 2, name: 'Wireless Mouse', price: 29.99, category: 'Electronics', stock: 200 },
      ];
      setResults(mockResults);
      message.success('Query executed!');
    } catch {
      message.error('Failed to run query');
    } finally {
      setLoading(false);
    }
  };

  const handleHistorySelect = (id: string) => {
    const item = history.find(h => h.id === id);
    if (item) {
      setQuery(item.question);
      setSql(item.sql);
    }
  };

  const leftPanel = <SchemaExplorer loading={false} />;
  
  const rightPanel = (
    <div className="h-full flex flex-col p-4 gap-4 overflow-auto">
      <QueryInput 
        onSubmit={handleQuerySubmit} 
        loading={loading}
        disabled={loading}
      />
      
      <SQLPreview 
        sql={sql}
        onRun={handleRunQuery}
        loading={loading}
      />
      
      <div className="flex-1">
        <ResultsTable 
          data={results}
          loading={loading}
        />
      </div>
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      <Header 
        databases={[selectedDb]}
        selectedDatabase={selectedDb}
        onDatabaseChange={setSelectedDb}
        history={history}
        onHistorySelect={handleHistorySelect}
      />
      
      <div className="flex-1 overflow-hidden">
        <HybridLayout 
          leftPanel={leftPanel}
          rightPanel={rightPanel}
          defaultLeftWidth={25}
          minLeftWidth={20}
          minRightWidth={40}
        />
      </div>
    </div>
  );
}
