"""
Nexus AI Foundation - MCP Server
Model Context Protocol Implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import asyncio
import json


class MCPResourceType(Enum):
    """MCP资源类型"""
    STATIC = "static"
    DYNAMIC = "dynamic"


@dataclass
class MCPResource:
    """MCP资源"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    resource_type: MCPResourceType = MCPResourceType.STATIC


@dataclass
class MCPTool:
    """MCP工具"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


@dataclass
class MCPPrompt:
    """MCP提示模板"""
    name: str
    description: str
    template: str
    arguments: List[str] = field(default_factory=list)


class MCPServer:
    """MCP服务器 - AI通用USB-C接口
    
    支持:
    - Resources: 静态/动态资源
    - Tools: 可执行函数
    - Prompts: 提示模板
    """
    
    def __init__(self, name: str = "nexus-mcp"):
        self.name = name
        self.resources: Dict[str, MCPResource] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        
        self._register_builtin_resources()
        self._register_builtin_tools()
        self._register_builtin_prompts()
    
    def _register_builtin_resources(self):
        """注册内置资源"""
        self.register_resource(MCPResource(
            uri="nexus://config",
            name="system_config",
            description="系统配置信息",
            resource_type=MCPResourceType.DYNAMIC
        ))
        
        self.register_resource(MCPResource(
            uri="nexus://models",
            name="available_models",
            description="可用模型列表",
            resource_type=MCPResourceType.DYNAMIC
        ))
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        self.register_tool(MCPTool(
            name="get_time",
            description="获取当前时间",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._get_time
        ))
        
        self.register_tool(MCPTool(
            name="calculate",
            description="数学计算",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式"
                    }
                },
                "required": ["expression"]
            },
            handler=self._calculate
        ))
    
    def _register_builtin_prompts(self):
        """注册内置提示"""
        self.register_prompt(MCPPrompt(
            name="summarize",
            description="总结文本",
            template="请总结以下内容:\n\n{{content}}",
            arguments=["content"]
        ))
        
        self.register_prompt(MCPPrompt(
            name="analyze_code",
            description="分析代码",
            template="请分析以下代码:\n\n```\n{{code}}\n```\n\n请提供:\n1. 代码功能\n2. 潜在问题\n3. 改进建议",
            arguments=["code"]
        ))
    
    # ========== 注册方法 ==========
    
    def register_resource(self, resource: MCPResource):
        """注册资源"""
        self.resources[resource.uri] = resource
    
    def register_tool(self, tool: MCPTool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def register_prompt(self, prompt: MCPPrompt):
        """注册提示"""
        self.prompts[prompt.name] = prompt
    
    # ========== 处理请求 ==========
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        method = request.get("method")
        params = request.get("params", {})
        
        try:
            if method == "resources/list":
                return await self._list_resources()
            elif method == "resources/read":
                return await self._read_resource(params.get("uri"))
            elif method == "tools/list":
                return self._list_tools()
            elif method == "tools/call":
                return await self._call_tool(params.get("name"), params.get("arguments", {}))
            elif method == "prompts/list":
                return self._list_prompts()
            elif method == "prompts/get":
                return self._get_prompt(params.get("name"), params.get("arguments", {}))
            else:
                return {"error": f"Unknown method: {method}"}
        except Exception as e:
            return {"error": str(e)}
    
    # ========== 资源操作 ==========
    
    async def _list_resources(self) -> Dict:
        return {
            "resources": [
                {
                    "uri": r.uri,
                    "name": r.name,
                    "description": r.description,
                    "mimeType": r.mime_type
                }
                for r in self.resources.values()
            ]
        }
    
    async def _read_resource(self, uri: str) -> Dict:
        resource = self.resources.get(uri)
        if not resource:
            return {"error": f"Resource not found: {uri}"}
        
        # 根据URI返回数据
        if uri == "nexus://config":
            data = {"version": "1.0.0", "name": self.name}
        elif uri == "nexus://models":
            data = {"models": ["gpt-4o", "claude-3-5-sonnet", "gemini-2.0-flash"]}
        else:
            data = {"uri": uri}
        
        return {
            "contents": [{
                "uri": uri,
                "mimeType": resource.mime_type,
                "text": json.dumps(data, ensure_ascii=False)
            }]
        }
    
    # ========== 工具操作 ==========
    
    def _list_tools(self) -> Dict:
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.input_schema
                }
                for t in self.tools.values()
            ]
        }
    
    async def _call_tool(self, name: str, arguments: Dict) -> Dict:
        tool = self.tools.get(name)
        if not tool:
            return {"error": f"Tool not found: {name}"}
        
        # 执行工具
        result = tool.handler(**arguments)
        
        if asyncio.iscoroutine(result):
            result = await result
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False)
            }]
        }
    
    # ========== 提示操作 ==========
    
    def _list_prompts(self) -> Dict:
        return {
            "prompts": [
                {
                    "name": p.name,
                    "description": p.description,
                    "arguments": [{"name": a, "required": True} for a in p.arguments]
                }
                for p in self.prompts.values()
            ]
        }
    
    def _get_prompt(self, name: str, arguments: Dict) -> Dict:
        prompt = self.prompts.get(name)
        if not prompt:
            return {"error": f"Prompt not found: {name}"}
        
        # 渲染模板
        template = prompt.template
        for key, value in arguments.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return {
            "messages": [{
                "role": "user",
                "content": {"type": "text", "text": template}
            }]
        }
    
    # ========== 内置工具实现 ==========
    
    def _get_time(self) -> Dict:
        from datetime import datetime
        now = datetime.now()
        return {
            "datetime": now.isoformat(),
            "timestamp": now.timestamp(),
            "timezone": str(now.tzinfo)
        }
    
    def _calculate(self, expression: str) -> Dict:
        try:
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                raise ValueError("Invalid characters")
            result = eval(expression)
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"expression": expression, "error": str(e)}


class MCPClient:
    """MCP客户端"""
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url
        self.server = MCPServer()  # 本地模式
    
    async def list_resources(self) -> List[Dict]:
        result = await self.server.handle_request({"method": "resources/list"})
        return result.get("resources", [])
    
    async def read_resource(self, uri: str) -> Dict:
        return await self.server.handle_request({
            "method": "resources/read",
            "params": {"uri": uri}
        })
    
    async def list_tools(self) -> List[Dict]:
        result = await self.server.handle_request({"method": "tools/list"})
        return result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict = None) -> Any:
        result = await self.server.handle_request({
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}}
        })
        if "error" in result:
            raise ValueError(result["error"])
        return json.loads(result["content"][0]["text"])
    
    async def get_prompt(self, name: str, arguments: Dict = None) -> str:
        result = await self.server.handle_request({
            "method": "prompts/get",
            "params": {"name": name, "arguments": arguments or {}}
        })
        if "error" in result:
            raise ValueError(result["error"])
        return result["messages"][0]["content"]["text"]


# 测试
async def test_mcp():
    """测试MCP"""
    print("=== Test MCP Server ===\n")
    
    client = MCPClient()
    
    # 列出资源
    resources = await client.list_resources()
    print(f"Resources: {len(resources)}")
    for r in resources:
        print(f"  - {r['name']}: {r['description']}")
    
    # 列出工具
    tools = await client.list_tools()
    print(f"\nTools: {len(tools)}")
    for t in tools:
        print(f"  - {t['name']}: {t['description']}")
    
    # 调用工具
    time_result = await client.call_tool("get_time")
    print(f"\nTime: {time_result['datetime']}")
    
    calc_result = await client.call_tool("calculate", {"expression": "2+2*3"})
    print(f"Calc: {calc_result}")
    
    # 获取提示
    prompt = await client.get_prompt("summarize", {"content": "这是一段测试文本"})
    print(f"\nPrompt: {prompt[:50]}...")
    
    print("\n✓ MCP Test Passed!")


if __name__ == "__main__":
    asyncio.run(test_mcp())
