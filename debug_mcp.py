#!/usr/bin/env python3
"""
Debug MCP Tool Exposure Issue
Check if tools are being properly exposed to OpenAI
"""

import sys
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.mcp_tools import MCPToolServer
from core.mcp_bridge import MCPOpenAIBridge

def debug_mcp_tools():
    """Debug MCP tool exposure"""
    print("🔍 DEBUGGING MCP TOOL EXPOSURE")
    print("=" * 50)
    
    # Initialize MCP
    mcp = MCPToolServer()
    
    # Check what tools are registered
    print("=== MCP TOOLS REGISTERED ===")
    if hasattr(mcp, '_tools'):
        print(f"Tool count: {len(mcp._tools)}")
        print(f"Tool names: {list(mcp._tools.keys())}")
    else:
        print("ERROR: No _tools attribute found!")
    
    # Check OpenAI schema generation
    try:
        bridge = MCPOpenAIBridge(mcp, "test_key")
        
        print("\n=== OPENAI SCHEMAS ===")
        if hasattr(bridge, '_tool_schemas'):
            print(f"Schema count: {len(bridge._tool_schemas)}")
            for i, schema in enumerate(bridge._tool_schemas[:2]):  # Show first 2
                print(f"\nSchema {i+1}:")
                print(json.dumps(schema, indent=2))
        else:
            print("ERROR: No schemas generated!")
            
        # Check if schemas are in correct OpenAI format
        if bridge._tool_schemas:
            first = bridge._tool_schemas[0]
            print(f"\nSchema format check:")
            print(f"Has 'type': {first.get('type')}")
            print(f"Has 'function': {'function' in first}")
            print(f"Function name: {first.get('function', {}).get('name', 'NONE')}")
            
    except Exception as e:
        print(f"ERROR initializing bridge: {e}")
        import traceback
        traceback.print_exc()

def test_openai_api():
    """Test what OpenAI actually receives"""
    print("\n=== TESTING OPENAI API ===")
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: No OPENAI_API_KEY found!")
        return
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Manually create a simple tool schema
        test_tools = [{
            "type": "function",
            "function": {
                "name": "observe",
                "description": "Observe an entity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "resolution": {"type": "number"}
                    },
                    "required": ["entity_id"]
                }
            }
        }]
        
        print(f"Testing with {len(test_tools)} tools...")
        
        # Test if OpenAI can see and use tools
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a test agent. Use the available tools."},
                {"role": "user", "content": "Observe the environment."}
            ],
            tools=test_tools,
            tool_choice="auto"
        )
        
        print(f"OpenAI response type: {type(response.choices[0].message)}")
        print(f"Has tool_calls: {response.choices[0].message.tool_calls is not None}")
        if response.choices[0].message.tool_calls:
            print(f"Tool calls count: {len(response.choices[0].message.tool_calls)}")
            print(f"First tool call: {response.choices[0].message.tool_calls[0]}")
        else:
            print("No tool calls made!")
            print(f"Content: {response.choices[0].message.content}")
            
    except Exception as e:
        print(f"ERROR testing OpenAI API: {e}")
        import traceback
        traceback.print_exc()

def test_mcp_bridge_debug():
    """Test MCP bridge with debug logging"""
    print("\n=== TESTING MCP BRIDGE DEBUG ===")
    
    try:
        from core.game_state import GameState
        from core.memory import Memory
        
        # Setup
        game_state = GameState()
        memory = Memory()
        mcp = MCPToolServer()
        mcp.bind_context(game_state, memory, "TEST_AGENT")
        
        # Add test entity
        game_state.entities["environment"] = {"threat_level": 1}
        
        # Test bridge
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: No API key for bridge test")
            return
            
        bridge = MCPOpenAIBridge(mcp, api_key)
        
        print(f"Bridge tool schemas count: {len(bridge._tool_schemas)}")
        
        # Test actual call
        messages = [
            {"role": "system", "content": "You are a test agent. Use available tools."},
            {"role": "user", "content": "Observe the environment."}
        ]
        
        print("Making OpenAI call...")
        action, params, reasoning = bridge.chat_with_tools(messages)
        
        print(f"Result: action={action}, params={params}")
        print(f"Reasoning: {reasoning[:100]}...")
        
    except Exception as e:
        print(f"ERROR testing MCP bridge: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_mcp_tools()
    test_openai_api()
    test_mcp_bridge_debug()
