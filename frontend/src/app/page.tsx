'use client';

import React, { useState } from 'react';
import { App } from 'antd';
import Header from '@/components/nl2sql/Header';
import SchemaExplorer from '@/components/nl2sql/SchemaExplorer';
import QueryInput from '@/components/nl2sql/QueryInput';
import SQLPreview from '@/components/nl2sql/SQLPreview';
import ResultsTable from '@/components/nl2sql/ResultsTable';
import HybridLayout from '@/components/nl2sql/HybridLayout';
import { nl2sqlApi } from '@/lib/api';

interface HistoryItem {
  id: string;
  question: string;
  sql: string;
  timestamp: Date;
}

export default function Home() {
  const { message } = App.useApp();
  const [selectedDb, setSelectedDb] = useState('example.db');
  const [, setQuery] = useState('');
  const [sql, setSql] = useState('');
  const [results, setResults] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const handleQuerySubmit = async (question: string) => {
    setQuery(question);
    setLoading(true);
    setSql('');
    setResults([]);
    
    try {
      const response = await nl2sqlApi.query({
        question,
        include_sql: true
      });

      if (response.status === 'success') {
        setSql(response.sql || '');
        
        if (response.result && Array.isArray(response.result)) {
          setResults(response.result as Record<string, unknown>[]);
        } else if (response.result) {
          setResults([response.result as Record<string, unknown>]);
        } else {
          setResults([]);
        }

        const newHistory: HistoryItem = {
          id: Date.now().toString(),
          question,
          sql: response.sql || '',
          timestamp: new Date(),
        };
        setHistory(prev => [newHistory, ...prev]);
        
        message.success('Query executed successfully!');
      } else {
        message.error(response.error || 'Query failed');
      }
    } catch (error) {
      message.error('Failed to execute query');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunQuery = async () => {
    if (!sql) return;
    message.info('Running custom SQL is not yet implemented');
  };

  const handleHistorySelect = (id: string) => {
    const item = history.find(h => h.id === id);
    if (item) {
      setQuery(item.question);
      setSql(item.sql);
    }
  };

  const leftPanel = <SchemaExplorer loading={loading} />;
  
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
