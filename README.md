# GuideHub

Vite + React 前端，FastAPI 后端。教程数据在 `db/`。

## 目录

```text
frontend/   # 前端
backend/    # FastAPI 后端
db/         # 各分类 yaml 示例数据
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://127.0.0.1:5173/  
前端通过代理访问 `/api/*` → `http://127.0.0.1:8000`。

## API 概览

| 路径 | 说明 |
| --- | --- |
| `POST /api/calculator/action` | 计算器按键（后端 `Calculator` 类） |
| `POST /api/candy/solve` | 分发糖果（后端 `Solution.candy`） |
| `POST /api/concurrency/io` | IO 密集：serial / threads / processes |
| `POST /api/concurrency/cpu` | CPU 密集：serial / threads / processes |
| `GET /api/health` | 健康检查 |
