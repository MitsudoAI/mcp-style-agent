"""
MCP Server implementation for Deep Thinking Engine

This module implements the standard MCP (Model Context Protocol) server
that exposes the deep thinking tools to MCP-compatible hosts like Cursor.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp import McpError, Tool
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .config.config_manager import ConfigManager
from .config.exceptions import DeepThinkingError
from .flows.flow_manager import FlowManager
from .models.mcp_models import (
    AnalyzeStepInput,
    CompleteThinkingInput,
    NextStepInput,
    StartThinkingInput,
)
from .sessions.session_manager import SessionManager
from .templates.template_manager import TemplateManager
from .tools.mcp_tools import MCPTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepThinkingMCPServer:
    """
    MCP Server for Deep Thinking Engine
    
    Provides zero-cost local MCP tools that return prompt templates
    for LLM execution, following the intelligent division of labor principle.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP server with configuration"""
        self.server = Server("deep-thinking-engine")
        
        # Initialize core components
        try:
            self.config_manager = ConfigManager(config_path)
            self.session_manager = SessionManager()
            self.template_manager = TemplateManager()
            self.flow_manager = FlowManager()
            self.mcp_tools = MCPTools(
                self.session_manager,
                self.template_manager,
                self.flow_manager
            )
        except Exception as e:
            logger.error(f"Failed to initialize MCP server components: {e}")
            raise

        # Register MCP tools
        self._register_tools()
        
        logger.info("Deep Thinking MCP Server initialized successfully")

    def _register_tools(self):
        """Register all MCP tools with the server"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available MCP tools"""
            return [
                Tool(
                    name="start_thinking",
                    description="开始深度思考流程，返回问题分解的Prompt模板",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "要深度思考的主题或问题"
                            },
                            "complexity": {
                                "type": "string",
                                "enum": ["simple", "moderate", "complex"],
                                "default": "moderate",
                                "description": "问题复杂度级别"
                            },
                            "focus": {
                                "type": "string",
                                "description": "分析重点或特定关注领域（可选）"
                            },
                            "flow_type": {
                                "type": "string",
                                "enum": ["comprehensive_analysis", "quick_analysis"],
                                "default": "comprehensive_analysis",
                                "description": "思维流程类型"
                            }
                        },
                        "required": ["topic"]
                    }
                ),
                Tool(
                    name="next_step",
                    description="获取思考流程的下一步Prompt模板",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "思考会话ID"
                            },
                            "step_result": {
                                "type": "string",
                                "description": "上一步的执行结果"
                            },
                            "quality_feedback": {
                                "type": "object",
                                "description": "质量反馈信息（可选）",
                                "properties": {
                                    "quality_score": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                        "description": "质量评分 (0-1)"
                                    },
                                    "feedback": {
                                        "type": "string",
                                        "description": "具体反馈内容"
                                    }
                                }
                            }
                        },
                        "required": ["session_id", "step_result"]
                    }
                ),
                Tool(
                    name="analyze_step",
                    description="分析步骤执行质量，返回评估Prompt模板",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "思考会话ID"
                            },
                            "step_name": {
                                "type": "string",
                                "description": "要分析的步骤名称"
                            },
                            "step_result": {
                                "type": "string",
                                "description": "步骤执行结果"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["quality", "format", "completeness"],
                                "default": "quality",
                                "description": "分析类型"
                            }
                        },
                        "required": ["session_id", "step_name", "step_result"]
                    }
                ),
                Tool(
                    name="complete_thinking",
                    description="完成思考流程，生成最终综合报告的Prompt模板",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "思考会话ID"
                            },
                            "final_insights": {
                                "type": "string",
                                "description": "最终洞察和总结（可选）"
                            }
                        },
                        "required": ["session_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle MCP tool calls"""
            try:
                logger.info(f"Calling tool: {name} with arguments: {arguments}")
                
                if name == "start_thinking":
                    input_data = StartThinkingInput(**arguments)
                    result = self.mcp_tools.start_thinking(input_data)
                    
                elif name == "next_step":
                    input_data = NextStepInput(**arguments)
                    result = self.mcp_tools.next_step(input_data)
                    
                elif name == "analyze_step":
                    input_data = AnalyzeStepInput(**arguments)
                    result = self.mcp_tools.analyze_step(input_data)
                    
                elif name == "complete_thinking":
                    input_data = CompleteThinkingInput(**arguments)
                    result = self.mcp_tools.complete_thinking(input_data)
                    
                else:
                    raise McpError(f"Unknown tool: {name}")

                # Convert result to MCP response format
                response_content = self._format_mcp_response(result)
                
                logger.info(f"Tool {name} executed successfully")
                return [TextContent(type="text", text=response_content)]
                
            except DeepThinkingError as e:
                logger.error(f"Deep thinking error in tool {name}: {e}")
                error_response = self._format_error_response(name, str(e))
                return [TextContent(type="text", text=error_response)]
                
            except Exception as e:
                logger.error(f"Unexpected error in tool {name}: {e}")
                error_response = self._format_error_response(name, f"Internal error: {str(e)}")
                return [TextContent(type="text", text=error_response)]

    def _format_mcp_response(self, result) -> str:
        """Format MCP tool result for client consumption"""
        response = {
            "tool_name": result.tool_name,
            "session_id": result.session_id,
            "step": result.step,
            "prompt_template": result.prompt_template,
            "instructions": result.instructions,
            "context": result.context,
            "next_action": result.next_action,
            "metadata": result.metadata
        }
        
        return json.dumps(response, ensure_ascii=False, indent=2)

    def _format_error_response(self, tool_name: str, error_message: str) -> str:
        """Format error response for MCP client"""
        error_response = {
            "error": True,
            "tool_name": tool_name,
            "error_message": error_message,
            "recovery_suggestions": [
                "检查输入参数是否正确",
                "确认会话ID是否有效",
                "重新开始思考流程"
            ]
        }
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Deep Thinking MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for the MCP server"""
    try:
        server = DeepThinkingMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())