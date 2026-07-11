# MCP Knowledge Bridge

> 自研 **MCP 风格知识工具桥**（stdio JSON-RPC）：`tools/*` + `resources/*` · 内置 BM25 检索 · `kb_compare` · 进程内 Client 便于单测与 Agent 适配。  
> 可被 Cursor / 自研 Agent 挂载为外部知识源。

## 亮点

| 能力 | 说明 |
|------|------|
| MCP 子集 | `initialize` / `tools/list` / `tools/call` / `resources/list` / `resources/read` |
| BM25 KB | JSON 条目 + `knowledge_docs/*.md` 双数据源 |
| kb_compare | 结构化对比两个主题的术语重叠（独立小功能） |
| LocalMCPClient | 不启子进程也能测协议路径，方便 CI |

## 快速开始

```bash
cd mcp-knowledge-bridge
python -m examples.demo_local
python -m examples.demo_protocol
python -m mcp_bridge.server   # stdio MCP server
```

### Cursor 挂载示例

```json
{
  "mcpServers": {
    "knowledge-bridge": {
      "command": "python",
      "args": ["-m", "mcp_bridge.server"],
      "cwd": "C:/Users/你的用户/Desktop/github-projects/mcp-knowledge-bridge"
    }
  }
}
```

## 与 lite-react-agent / hybrid-rag-kit 的关系

- Agent 负责规划与工具循环  
- RAG Kit 负责检索算法与评测  
- 本仓库负责 **把知识能力标准化暴露**（协议层）

三者可组合成一条作品集叙事：**协议 → 检索 → Agent**。

## License

MIT
