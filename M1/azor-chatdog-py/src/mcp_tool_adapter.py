from typing import Dict, Any, List
import google.generativeai as genai
import google.ai.generativelanguage as glm # Import generativelanguage module


def _convert_type(json_type: str) -> str:
    """Maps JSON schema types to Gemini type strings."""
    type_mapping = {
        "string": "STRING",
        "number": "NUMBER",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "array": "ARRAY",
        "object": "OBJECT"
    }
    return type_mapping.get(json_type, "STRING")

def _convert_to_gemini_schema(json_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively converts a JSON schema dict to a Gemini schema dict."""
    schema_type_str = json_schema.get("type", "string")
    schema_type = _convert_type(schema_type_str)
    
    schema = {
        "type": schema_type
    }
    
    if "format" in json_schema:
        schema["format"] = json_schema["format"]
    if "description" in json_schema:
        schema["description"] = json_schema["description"]
    if "nullable" in json_schema:
        schema["nullable"] = json_schema["nullable"]
    if "enum" in json_schema:
        schema["enum"] = json_schema["enum"]
        
    if schema_type == "OBJECT":
        properties = json_schema.get("properties", {})
        converted_properties = {}
        for key, prop_schema in properties.items():
            converted_properties[key] = _convert_to_gemini_schema(prop_schema)
        
        schema["properties"] = converted_properties
        if "required" in json_schema:
            schema["required"] = json_schema["required"]

    elif schema_type == "ARRAY":
        items_schema = json_schema.get("items")
        if items_schema:
            schema["items"] = _convert_to_gemini_schema(items_schema)
            
    return schema

def mcp_to_gemini_tool(mcp_tool: Dict[str, Any]) -> genai.types.Tool: #type: ignore
    """Converts a single MCP tool definition to a Gemini-compatible Tool object."""
    
    # Input schema from MCP is usually an object schema for the arguments
    input_schema = mcp_tool.get("inputSchema", {})
    
    # Ensure the root of the arguments is treated as an OBJECT
    # (MCP tools usually define 'inputSchema' as the schema for the arguments object)
    if "type" not in input_schema:
        input_schema["type"] = "object"
        
    converted_schema = _convert_to_gemini_schema(input_schema)

    function_declaration = genai.types.FunctionDeclaration(
        name=mcp_tool["name"],
        description=mcp_tool.get("description", ""),
        parameters=converted_schema
    )
    return genai.types.Tool(function_declarations=[function_declaration])

def mcp_tools_to_gemini_tools(mcp_tools: List[Dict[str, Any]]) -> List[genai.types.Tool]: #type: ignore
    """
    Converts a list of MCP tool definitions to a list of Gemini-compatible Tool objects.
    """
    return [mcp_to_gemini_tool(tool) for tool in mcp_tools]
