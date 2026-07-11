# MCP Knowledge Bridge

> 轻量 **MCP 风格知识工具桥**：stdio JSON-RPC · 本地知识库检索 · 可被 Agent 当作外部工具挂载。  
> 借鉴 [Model Context Protocol](https://modelcontextprotocol.io/) 的工具发现/调用模型，**协议子集与知识工具自研实现**。

## 亮点

| 亮点 | 说明 |
|------|------|
| MCP stdio 子集 | 支持 `initialize` / `tools/list` / `tools/call` |
| 知识工具 | `kb_search`、`kb_get`、`echo_debug` |
| 零云依赖 | 本地 JSON 知识库即可演示 |
| Agent 友好 | 可与 `lite-react-agent` 组合：Agent 调 MCP 桥再查知识 |

## 快速开始

```bash
cd mcp-knowledge-bridge
pip install -r requirements.txt

# 交互式自测（非 stdio）
python -m examples.demo_local

# 作为 MCP stdio server（Cursor / 客户端可挂载）
python -m mcp_bridge.server
```

### Cursor MCP 配置示例

```json
{
  "mcpServers": {
    "knowledge-bridge": {
      "command": "python",
      "args": ["-m", "mcp_bridge.server"],
      "cwd": "C:/Users/你的用户名/Desktop/github-projects/mcp-knowledge-bridge"
    }
  }
}
```

## 与开源的区别

- **借鉴**：MCP 的 tool schema 与 stdio 传输  
- **自研**：精简 JSON-RPC 循环、内置知识库与检索工具（非官方 SDK 全家桶封装）

## License

MIT
