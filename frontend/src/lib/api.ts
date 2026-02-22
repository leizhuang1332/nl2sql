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
}

export const nl2sqlApi = new NL2SQLAPI();
export default NL2SQLAPI;
