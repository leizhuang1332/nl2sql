'use client';

import React, { useState, useMemo } from 'react';
import { App, Switch } from 'antd';
import Header from '@/components/nl2sql/Header';
import SchemaExplorer from '@/components/nl2sql/SchemaExplorer';
import QueryInput from '@/components/nl2sql/QueryInput';
import SQLPreview from '@/components/nl2sql/SQLPreview';
import ResultsTable from '@/components/nl2sql/ResultsTable';
import HybridLayout from '@/components/nl2sql/HybridLayout';
import ThinkingDisplay from '@/components/nl2sql/ThinkingDisplay';
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
  const [thinking, setThinking] = useState('');
  const [showThinking, setShowThinking] = useState(false);

  const handleQuerySubmit = async (question: string) => {
    setQuery(question);
    setLoading(true);
    setSql('');
    setResults([]);
    setStreaming(true);
    setStreamStage('semantic_mapping');
    setStreamProgress(0);
    setThinking('');
    
    try {
      await nl2sqlApi.queryStream(
        {
          question,
          include_sql: true
        },
        (chunk: StreamChunk) => {
          // Handle nested data structure from backend
          const data = chunk.data as Record<string, unknown> | undefined;
          
          if (chunk.stage) {
            setStreamStage(chunk.stage);
            setStreamProgress(STAGE_PROGRESS[chunk.stage] || 0);
          }
          
          // Handle thinking streaming
          if (chunk.stage === 'thinking' && chunk.status === 'streaming' && chunk.chunk) {
            // Clean thinking tags from content
            const cleanedChunk = chunk.chunk
              .replace(/<thinking>/g, '')
              .replace(/<\/thinking>/g, '');
            setThinking(prev => prev + cleanedChunk);
          }
          // Handle thinking done
          if (chunk.stage === 'thinking_done' && data?.thinking) {
            // Clean thinking tags from content
            const cleanedThinking = (data.thinking as string)
              .replace(/<thinking>/g, '')
              .replace(/<\/thinking>/g, '');
            setThinking(cleanedThinking);
          }
          

          if (data?.sql) {
            setSql(data.sql as string);
          }
          
          // Handle execution_result from both execution and done stages
          // execution_result is returned as a string in the format "[(...), (...)]"
          // We need to parse it to display in the table
          if (data?.execution_result && chunk.stage !== 'explained') {
            const execResult = data.execution_result as string;
            
            // Get column names from data if available
            const columns = data.columns as string[] | undefined;
            
            if (execResult && execResult.trim()) {
              try {
                // Parse the string representation of tuples
                // First, convert single quotes to double quotes (but preserve escaped quotes)
                const parsed = execResult
                  .replace(/\(/g, '[')
                  .replace(/\)/g, ']')
                  .replace(/'/g, '"');
                const rows = JSON.parse(parsed) as unknown[][];
                if (Array.isArray(rows) && rows.length > 0) {
                  // Use provided column names or generate generic ones
                  const columnNames = columns && columns.length > 0 
                    ? columns 
                    : Array.from({ length: Math.max(...rows.map(r => Array.isArray(r) ? r.length : 0)) }, (_, i) => `column_${i}`);
                  
                  const formattedResults = rows.map(row => {
                    const obj: Record<string, unknown> = {};
                    if (Array.isArray(row)) {
                      row.forEach((val, idx) => {
                        obj[columnNames[idx]] = val;
                      });
                    }
                    return obj;
                  });
                  setResults(formattedResults);
                }
              } catch (e) {
                console.error('Failed to parse execution_result:', e);
              }
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

  const leftPanel = useMemo(() => <SchemaExplorer />, []);
  
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
      
      {/* 思考过程切换按钮 - 默认隐藏 */}
      <div className="flex items-center gap-2 mb-2">
        <Switch
          checked={showThinking}
          onChange={(checked) => setShowThinking(checked)}
          size="small"
        />
        <span className="text-sm text-slate-400">显示 AI 思考过程</span>
      </div>
      
      {showThinking && (
        <ThinkingDisplay 
          thinking={thinking} 
          loading={loading && !thinking} 
        />
      )}
      
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
