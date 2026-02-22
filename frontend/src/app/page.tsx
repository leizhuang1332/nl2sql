'use client';

import React, { useState } from 'react';
import { App } from 'antd';
import Header from '@/components/nl2sql/Header';
import SchemaExplorer from '@/components/nl2sql/SchemaExplorer';
import QueryInput from '@/components/nl2sql/QueryInput';
import SQLPreview from '@/components/nl2sql/SQLPreview';
import ResultsTable from '@/components/nl2sql/ResultsTable';
import HybridLayout from '@/components/nl2sql/HybridLayout';
import { nl2sqlApi, StreamChunk } from '@/lib/api';

interface HistoryItem {
  id: string;
  question: string;
  sql: string;
  timestamp: Date;
}

const STAGE_PROGRESS: Record<string, number> = {
  semantic_mapping: 16,
  schema_prep: 33,
  sql_generation: 50,
  security: 66,
  execution: 83,
  explaining: 95,
  done: 100,
};

export default function Home() {
  const { message } = App.useApp();
  const [selectedDb, setSelectedDb] = useState('example.db');
  const [, setQuery] = useState('');
  const [sql, setSql] = useState('');
  const [results, setResults] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  
  const [streaming, setStreaming] = useState(false);
  const [streamStage, setStreamStage] = useState<string>('');
  const [streamProgress, setStreamProgress] = useState<number>(0);

  const handleQuerySubmit = async (question: string) => {
    setQuery(question);
    setLoading(true);
    setSql('');
    setResults([]);
    setStreaming(true);
    setStreamStage('semantic_mapping');
    setStreamProgress(0);
    
    try {
      await nl2sqlApi.queryStream(
        {
          question,
          include_sql: true
        },
        (chunk: StreamChunk) => {
          if (chunk.stage) {
            setStreamStage(chunk.stage);
            setStreamProgress(STAGE_PROGRESS[chunk.stage] || 0);
          }
          if (chunk.sql) {
            setSql(chunk.sql);
          }
          if (chunk.result) {
            if (Array.isArray(chunk.result)) {
              setResults(chunk.result as Record<string, unknown>[]);
            } else {
              setResults([chunk.result as Record<string, unknown>]);
            }
          }
        },
        () => {
          setLoading(false);
          setStreaming(false);
          setStreamStage('done');
          setStreamProgress(100);
          
          const newHistory: HistoryItem = {
            id: Date.now().toString(),
            question,
            sql: sql,
            timestamp: new Date(),
          };
          setHistory(prev => [newHistory, ...prev]);
          message.success('Query executed successfully!');
        },
        (error: Error) => {
          setLoading(false);
          setStreaming(false);
          message.error(error.message || 'Failed to execute query');
        }
      );
    } catch (error) {
      setLoading(false);
      setStreaming(false);
      message.error('Failed to execute query');
      console.error(error);
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
        streaming={streaming}
        streamStage={streamStage}
        streamProgress={streamProgress}
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
