# HAM 题库后端（FastAPI）

## 运行

```bash
cd server
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# 允许本地 Vite 访问（可选；多个用逗号分隔）
export CORS_ORIGINS="http://localhost:5173"

./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```

## 与前端联调（Vite）

前端默认请求 `http://localhost:8001`。你也可以在前端项目 `my-app` 里设置：

```bash
export VITE_HAM_API_BASE="http://127.0.0.1:8001"
```

然后启动前端：

```bash
npm --prefix ../my-app run dev
```

## API

- `GET /api/health`
- `GET /api/banks` 返回题库列表（含 pdfUrl、题目数量）
- `GET /api/banks/{bank_id}` 返回题库题目 JSON
- `GET /api/pdfs/{bank_id}` 返回对应 PDF（可 iframe 预览）

## 数据来源

后端只读取 `server/` 目录内的文件：

- `server/data/*.json`
- `server/pdfs/*.pdf`

如需重新生成 JSON：

```bash
./.venv/bin/python ../tools/build_question_bank.py --pdf "../A类题库.pdf" --out "./data/A类题库.json"
```

如果你已经在仓库根目录生成过 `data/*.json`，也可以直接复制进来：

```bash
cp -f ../data/*.json ./data/
cp -f ../*.pdf ./pdfs/
```
