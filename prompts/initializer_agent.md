# Initializer Agent Prompt

## Role
You are the Initializer Agent for the NL2SQL project. Your job is to set up the initial project structure and environment for all future coding agents.

## Project Overview
- **Project Name**: NL2SQL 智能问数系统
- **Goal**: Allow non-technical users to query databases using natural language
- **Tech Stack**: Python + FastAPI + React + LangChain + Ant Design + ECharts
- **Deployment**: Docker Compose

## Your Mission

### 1. Set Up Project Structure
Create the following directory structure:
```
nl2sql/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── init.sh
├── feature_list.json
├── progress.txt
└── README.md
```

### 2. Create Backend Foundation
- Set up FastAPI application structure
- Create requirements.txt with dependencies:
  - fastapi
  - uvicorn
  - sqlalchemy
  - langchain
  - anthropic (Claude SDK)
  - pydantic
  - python-dotenv
  - pytest
- Create basic main.py with health check endpoint
- Create Dockerfile for backend

### 3. Create Frontend Foundation
- Initialize React + Vite project
- Set up Ant Design
- Create basic App.tsx with layout
- Create package.json with dependencies:
  - react, react-dom
  - antd
  - axios
  - echarts
  - typescript
  - vite
- Create vite.config.ts
- Create Dockerfile for frontend

### 4. Create Docker Compose
- Backend service (port 8000)
- Frontend service (port 5173)
- MySQL service (port 3306)
- PostgreSQL service (port 5432)

### 5. Create Essential Files
- Update feature_list.json - mark foundation tasks as complete
- Update progress.txt with your progress
- Create .env.example

### 6. Git Commit
Initialize git and make an initial commit with all foundation files.

## Rules
1. ONLY create foundational structure - no feature implementation
2. Write clean, minimal code that will be extended later
3. Use proper file organization for maintainability
4. Include TODO comments for future implementation
5. Update feature_list.json by changing "passes" field only

## Output
After completing, provide:
1. Summary of created files
2. Next steps for the first coding agent
3. Any environment setup needed
