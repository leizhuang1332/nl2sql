const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface QueryRequest {
  question: string;
  database?: string;
  include_sql?: boolean;
}

export interface QueryResponse {
  question: string;
  result: unknown;
  sql?: string;
  status: string;
  error?: string;
}

export interface StreamChunk {
  stage?: string;
  status?: string;
  sql?: string;
  result?: unknown;
  error?: string;
  explanation?: string;
  data?: Record<string, unknown>;  // For nested data from backend
}

export type StreamCallback = (chunk: StreamChunk) => void;

export interface TableListResponse {
  tables: string[];
}

export interface SchemaColumn {
  name: string;
  type: string;
}

export interface SchemaInfo {
  table_name: string;
  ddl: string;
  columns: SchemaColumn[];
}

export interface SchemaResponse {
  table: string;
  schema: SchemaInfo;
}

class NL2SQLAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async query(request: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getTables(): Promise<TableListResponse> {
    return this.request<TableListResponse>('/tables');
  }

  async getSchema(tableName: string): Promise<SchemaResponse> {
    return this.request<SchemaResponse>(`/schema/${tableName}`);
  }

  async health(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  async queryStream(
    request: QueryRequest,
    onChunk: StreamCallback,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ): Promise<void> {
    const url = `${this.baseUrl}/query/stream`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          // Process any remaining data in buffer
          if (buffer.trim()) {
            try {
              const chunk = JSON.parse(buffer.trim());
              onChunk(chunk);
            } catch {
              // Ignore parsing errors for incomplete chunks
            }
          }
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        // Split by SSE format: each line starts with "data: "
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('data: ')) {
            const data = trimmedLine.slice(6); // Remove "data: " prefix
            if (data.trim() === '[DONE]') {
              if (onComplete) onComplete();
              return;
            }
            try {
              const chunk = JSON.parse(data);
              onChunk(chunk);
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }

      if (onComplete) onComplete();
    } catch (error) {
      if (onError && error instanceof Error) {
        onError(error);
      } else if (onError) {
        onError(new Error('Unknown error occurred'));
      }
    }
  }
}

export const nl2sqlApi = new NL2SQLAPI();
export default NL2SQLAPI;
