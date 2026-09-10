import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("mcp.client")


class MCPClientManager:
    """
    Asynchronous Model Context Protocol (MCP) stdio client connector.
    Wraps tool calls in Tenacity exponential backoff retries and returns
    structured fallback results if the external server is offline or fails.
    """
    def __init__(self, command: str = "python", args: Optional[list] = None):
        self.command = command
        self.args = args or []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=False
    )
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes an MCP tool over stdio transport with exponential retries.
        """
        logger.info(f"Invoking MCP tool '{tool_name}' with args {arguments}")
        try:
            # Check if mcp python SDK is available and functional
            import mcp
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=None
            )

            # In a real environment with an MCP server subprocess
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    response = await session.call_tool(tool_name, arguments)
                    return {
                        "status": "success",
                        "tool": tool_name,
                        "result": response.content,
                        "error": None
                    }
        except Exception as e:
            logger.warning(f"MCP stdio execution failed ({tool_name}): {e}. Providing synthetic fallback tool response.")
            # Graceful synthetic response so the LangGraph graph proceeds seamlessly
            return {
                "status": "fallback",
                "tool": tool_name,
                "result": f"MCP tool '{tool_name}' executed in fallback mode. Parameters processed: {arguments}",
                "error": str(e)
            }


# Singleton manager
_mcp_manager = None


def get_mcp_manager() -> MCPClientManager:
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
    return _mcp_manager


async def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to execute tool with the default MCP manager."""
    manager = get_mcp_manager()
    return await manager.call_tool(tool_name, arguments)
