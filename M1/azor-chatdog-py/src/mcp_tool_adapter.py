from typing import Dict, Any, List
import google.generativeai as genai

def mcp_to_gemini_tool(mcp_tool: Dict[str, Any]) -> genai.types.Tool: #type: ignore
    """Converts a single MCP tool definition to a Gemini-compatible Tool object."""
    function_declaration = genai.types.FunctionDeclaration(
        name=mcp_tool["name"],
        description=mcp_tool.get("description", ""),
        parameters=mcp_tool.get("input_schema", {})
    )
    return genai.types.Tool(function_declarations=[function_declaration])

def mcp_tools_to_gemini_tools(mcp_tools: List[Dict[str, Any]]) -> List[genai.types.Tool]: #type: ignore
    """Converts a list of MCP tool definitions to a list of Gemini-compatible Tool objects."""
    return [mcp_to_gemini_tool(tool) for tool in mcp_tools]
