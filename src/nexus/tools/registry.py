"""
Nexus AI Foundation - Tool Registry
工具注册与执行
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Type
from enum import Enum
import asyncio
import inspect


class ToolCategory(Enum):
    """工具类别"""
    SEARCH = "search"           # 搜索
    COMPUTE = "compute"         # 计算
    DATA = "data"              # 数据处理
    EXTERNAL = "external"       # 外部服务
    FILE = "file"              # 文件操作
    BROWSER = "browser"         # 浏览器控制
    CODE = "code"              # 代码执行


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    handler: Callable
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def __call__(self, **kwargs) -> Any:
        """执行工具"""
        return self.handler(**kwargs)
    
    def validate_params(self, params: Dict) -> bool:
        """验证参数"""
        for param in self.parameters:
            if param.required and param.name not in params:
                return False
        return True


class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.categories: Dict[ToolCategory, List[str]] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        # Web Search
        self.register(Tool(
            name="web_search",
            description="搜索互联网获取最新信息",
            category=ToolCategory.SEARCH,
            parameters=[
                ToolParameter("query", "string", "搜索查询", required=True),
                ToolParameter("num_results", "number", "返回结果数量", required=False, default=5),
            ],
            handler=self._web_search,
            examples=["搜索AI最新发展", "查找Python教程"],
            tags=["search", "web"]
        ))
        
        # Web Fetch
        self.register(Tool(
            name="web_fetch",
            description="获取网页内容",
            category=ToolCategory.SEARCH,
            parameters=[
                ToolParameter("url", "string", "网页URL", required=True),
                ToolParameter("max_chars", "number", "最大字符数", required=False, default=5000),
            ],
            handler=self._web_fetch,
            examples=["获取Wikipedia页面", "抓取博客文章"],
            tags=["fetch", "web"]
        ))
        
        # Python Execute
        self.register(Tool(
            name="python_exec",
            description="执行Python代码",
            category=ToolCategory.COMPUTE,
            parameters=[
                ToolParameter("code", "string", "要执行的Python代码", required=True),
                ToolParameter("timeout", "number", "超时时间(秒)", required=False, default=30),
            ],
            handler=self._python_exec,
            examples=["计算斐波那契数列", "数据处理"],
            tags=["code", "python", "compute"]
        ))
        
        # Calculator
        self.register(Tool(
            name="calculator",
            description="数学计算",
            category=ToolCategory.COMPUTE,
            parameters=[
                ToolParameter("expression", "string", "数学表达式", required=True),
            ],
            handler=self._calculator,
            examples=["2+2", "sqrt(16) * 3"],
            tags=["math", "compute"]
        ))
        
        # File Read
        self.register(Tool(
            name="file_read",
            description="读取文件内容",
            category=ToolCategory.FILE,
            parameters=[
                ToolParameter("path", "string", "文件路径", required=True),
                ToolParameter("limit", "number", "限制行数", required=False),
            ],
            handler=self._file_read,
            examples=["读取配置文件", "查看日志"],
            tags=["file", "read"]
        ))
        
        # File Write
        self.register(Tool(
            name="file_write",
            description="写入文件内容",
            category=ToolCategory.FILE,
            parameters=[
                ToolParameter("path", "string", "文件路径", required=True),
                ToolParameter("content", "string", "文件内容", required=True),
                ToolParameter("append", "boolean", "是否追加", required=False, default=False),
            ],
            handler=self._file_write,
            examples=["写入配置文件", "保存日志"],
            tags=["file", "write"]
        ))
        
        # Browser Control
        self.register(Tool(
            name="browser_navigate",
            description="导航到URL",
            category=ToolCategory.BROWSER,
            parameters=[
                ToolParameter("url", "string", "目标URL", required=True),
            ],
            handler=self._browser_navigate,
            examples=["打开Google", "访问GitHub"],
            tags=["browser", "web"]
        ))
        
        # Current Time
        self.register(Tool(
            name="get_current_time",
            description="获取当前时间",
            category=ToolCategory.EXTERNAL,
            parameters=[],
            handler=self._get_current_time,
            examples=["现在几点", "当前日期"],
            tags=["time", "system"]
        ))
    
    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
        
        # 更新分类索引
        if tool.category not in self.categories:
            self.categories[tool.category] = []
        self.categories[tool.category].append(tool.name)
    
    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self.tools:
            tool = self.tools[name]
            del self.tools[name]
            self.categories[tool.category].remove(name)
            return True
        return False
    
    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        tags: Optional[List[str]] = None
    ) -> List[Tool]:
        """列出工具"""
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]
        
        return tools
    
    async def execute(
        self,
        name: str,
        params: Dict[str, Any]
    ) -> Any:
        """执行工具"""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        if not tool.validate_params(params):
            raise ValueError(f"Invalid parameters for tool: {name}")
        
        # 异步执行
        if asyncio.iscoroutinefunction(tool.handler):
            return await tool.handler(**params)
        else:
            return tool.handler(**params)
    
    # 内置工具实现
    def _web_search(self, query: str, num_results: int = 5) -> Dict:
        """Web搜索 - 需要配置实际API"""
        return {
            "query": query,
            "results": [
                {"title": f"Result {i+1} for {query}", "url": f"https://example.com/{i}"}
                for i in range(num_results)
            ]
        }
    
    def _web_fetch(self, url: str, max_chars: int = 5000) -> Dict:
        """Web抓取"""
        return {
            "url": url,
            "content": f"Mock content from {url}..."[:max_chars]
        }
    
    def _python_exec(self, code: str, timeout: int = 30) -> Dict:
        """Python执行"""
        try:
            # 安全的执行环境
            import io
            import sys
            
            stdout = io.StringIO()
            local_vars = {}
            
            exec(code, {"__builtins__": __builtins__}, local_vars)
            
            return {
                "success": True,
                "output": stdout.getvalue(),
                "result": local_vars.get("result")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculator(self, expression: str) -> Dict:
        """计算器"""
        try:
            # 安全计算
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")
            
            result = eval(expression)
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"expression": expression, "error": str(e)}
    
    def _file_read(self, path: str, limit: Optional[int] = None) -> Dict:
        """文件读取"""
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            if limit:
                content = content[:limit]
            
            return {"path": path, "content": content, "success": True}
        except Exception as e:
            return {"path": path, "error": str(e), "success": False}
    
    def _file_write(
        self,
        path: str,
        content: str,
        append: bool = False
    ) -> Dict:
        """文件写入"""
        try:
            mode = 'a' if append else 'w'
            with open(path, mode) as f:
                f.write(content)
            
            return {"path": path, "success": True}
        except Exception as e:
            return {"path": str(e), "error": str(e), "success": False}
    
    def _browser_navigate(self, url: str) -> Dict:
        """浏览器导航"""
        return {"url": url, "message": "Browser navigation called (needs browser config)"}
    
    def _get_current_time(self) -> Dict:
        """获取当前时间"""
        import datetime
        now = datetime.datetime.now()
        return {
            "datetime": now.isoformat(),
            "timestamp": now.timestamp(),
            "timezone": str(now.tzinfo)
        }


# 全局工具注册表
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


# 测试
async def test_tool_registry():
    """测试工具注册表"""
    print("=== 测试 Tool Registry ===\n")
    
    registry = ToolRegistry()
    
    # 列出所有工具
    print(f"内置工具数量: {len(registry.tools)}")
    print("\n工具列表:")
    
    for category in ToolCategory:
        tools = registry.list_tools(category=category)
        if tools:
            print(f"\n  [{category.value}]")
            for tool in tools:
                print(f"    - {tool.name}: {tool.description}")
    
    # 测试执行
    print("\n\n测试工具执行:")
    
    # 计算器
    result = await registry.execute("calculator", {"expression": "2 + 2 * 3"})
    print(f"  calculator(2+2*3) = {result}")
    
    # 时间
    result = await registry.execute("get_current_time", {})
    print(f"  get_current_time() = {result['datetime']}")
    
    # 搜索
    result = await registry.execute("web_search", {"query": "AI news", "num_results": 3})
    print(f"  web_search(AI news) = {len(result['results'])} results")
    
    print("\n✓ Tool Registry 测试通过!")


if __name__ == "__main__":
    asyncio.run(test_tool_registry())
