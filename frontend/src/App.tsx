import { useState } from 'react'
import { Layout, Input, Button, Card, Table, Tabs, message } from 'antd'
import { SendOutlined, DatabaseOutlined, HistoryOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Header, Content } = Layout
const { TextArea } = Input
const { TabPane } = Tabs

interface QueryResult {
  columns: string[]
  data: any[]
}

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [sql, setSql] = useState('')

  const handleQuery = async () => {
    if (!query.trim()) return
    
    setLoading(true)
    try {
      const response = await axios.post('/api/query', { query })
      setResult(response.data.result)
      setSql(response.data.sql)
    } catch (error: any) {
      message.error(error.message || 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  const columns = result?.columns.map(col => ({
    title: col,
    dataIndex: col,
    key: col,
  })) || []

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <DatabaseOutlined style={{ fontSize: 24, color: '#fff', marginRight: 12 }} />
        <span style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>NL2SQL 智能问数</span>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Tabs defaultActiveKey="1">
          <TabPane tab={<span><SendOutlined /> 智能查询</span>} key="1">
            <Card>
              <TextArea
                rows={4}
                placeholder="用自然语言描述你的查询，例如：查询2024年销售额最高的前10个产品"
                value={query}
                onChange={e => setQuery(e.target.value)}
                style={{ marginBottom: 16 }}
              />
              <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={handleQuery}>
                执行查询
              </Button>
              
              {sql && (
                <Card title="生成的SQL" size="small" style={{ marginTop: 16 }}>
                  <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>{sql}</pre>
                </Card>
              )}
              
              {result && (
                <Table
                  dataSource={result.data.map((row, i) => ({ ...row, key: i }))}
                  columns={columns}
                  pagination={{ pageSize: 10 }}
                  style={{ marginTop: 16 }}
                />
              )}
            </Card>
          </TabPane>
          <TabPane tab={<span><HistoryOutlined /> 查询历史</span>} key="2">
            <Card>查询历史功能开发中...</Card>
          </TabPane>
        </Tabs>
      </Content>
    </Layout>
  )
}

export default App
