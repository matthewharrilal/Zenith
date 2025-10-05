"""
MCP Tool Server - Wrapper around PrimitiveTools for OpenAI function calling
Provides the 10 core primitive tools as OpenAI function schemas
"""

from typing import Dict, Any, List, Tuple
from .primitives import PrimitiveTools
from .game_state import GameState
from .memory import Memory

class MCPToolServer:
    def __init__(self):
        self.game_state = None
        self.memory = None
        self.agent_name = None
        self.primitives = None
        
    def bind_context(self, game_state: GameState, memory: Memory, agent_name: str):
        """Bind the current game context to this server"""
        self.game_state = game_state
        self.memory = memory
        self.agent_name = agent_name
        self.primitives = PrimitiveTools(game_state, memory)
        
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return OpenAI function schemas for all 10 primitive tools"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "observe",
                    "description": "Gather information about entities in the environment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "ID of entity to observe (e.g., 'environment', 'RAVEN', 'door_1')"
                            },
                            "resolution": {
                                "type": "number",
                                "description": "Detail level: 0.0=basic, 1.0=maximum detail",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["entity_id", "resolution"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "signal",
                    "description": "Send communication to other agents AND learn from responses",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message content to broadcast"
                            },
                            "intensity": {
                                "type": "integer",
                                "description": "Priority level 1-10",
                                "minimum": 1,
                                "maximum": 10
                            },
                            "target": {
                                "type": "string",
                                "description": "Target: 'all', specific agent name, or custom group"
                            }
                        },
                        "required": ["message", "intensity", "target"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query",
                    "description": "Search memory for valuable information about current situation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "memory_type": {
                                "type": "string",
                                "description": "Type of memory: 'events', 'patterns', 'relationships'",
                                "enum": ["events", "patterns", "relationships"]
                            },
                            "search_term": {
                                "type": "string",
                                "description": "What to search for in memory"
                            }
                        },
                        "required": ["memory_type", "search_term"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "transfer",
                    "description": "Move resources, information, or trust between entities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "property_name": {
                                "type": "string",
                                "description": "What to transfer: 'resources', 'information', 'trust', etc."
                            },
                            "from_entity": {
                                "type": "string",
                                "description": "Source entity ID"
                            },
                            "to_entity": {
                                "type": "string",
                                "description": "Target entity ID"
                            },
                            "amount": {
                                "type": "string",
                                "description": "Amount to transfer (number or 'all')"
                            }
                        },
                        "required": ["property_name", "from_entity", "to_entity", "amount"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "modify",
                    "description": "Change entity properties directly",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "Entity to modify"
                            },
                            "property_name": {
                                "type": "string",
                                "description": "Property to change"
                            },
                            "operation": {
                                "type": "string",
                                "description": "Operation: 'set', 'add', 'multiply', 'append'",
                                "enum": ["set", "add", "multiply", "append"]
                            },
                            "value": {
                                "type": "string",
                                "description": "New value or amount to add/multiply"
                            }
                        },
                        "required": ["entity_id", "property_name", "operation", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "connect",
                    "description": "Create or modify relationships between entities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_a": {
                                "type": "string",
                                "description": "First entity in relationship"
                            },
                            "entity_b": {
                                "type": "string",
                                "description": "Second entity in relationship"
                            },
                            "strength": {
                                "type": "number",
                                "description": "Relationship strength: -1.0 to 1.0",
                                "minimum": -1.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["entity_a", "entity_b", "strength"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect",
                    "description": "Discover hidden patterns and relationships - reveals non-obvious information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_set": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of entity IDs to analyze (use ['all'] for all entities)"
                            },
                            "pattern_type": {
                                "type": "string",
                                "description": "Type of pattern to detect",
                                "enum": ["correlation", "trend", "anomaly", "similarity"]
                            }
                        },
                        "required": ["entity_set", "pattern_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "receive",
                    "description": "Listen for signals - learn what others are thinking and doing",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter_criteria": {
                                "type": "object",
                                "description": "Filters for signals (e.g., {'sender': 'RAVEN', 'min_intensity': 5})",
                                "properties": {
                                    "sender": {"type": "string"},
                                    "min_intensity": {"type": "integer"}
                                }
                            },
                            "time_window": {
                                "type": "number",
                                "description": "How far back to look for signals (seconds)"
                            }
                        },
                        "required": ["filter_criteria", "time_window"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "store",
                    "description": "Save important insights to collective memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "knowledge": {
                                "type": "string",
                                "description": "Important insight or knowledge to remember"
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence in this knowledge (0.0 to 1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["knowledge", "confidence"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compute",
                    "description": "Process information to derive insights",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "inputs": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Data to process"
                            },
                            "operation": {
                                "type": "string",
                                "description": "Processing operation",
                                "enum": ["sum", "average", "correlate", "predict", "analyze"]
                            }
                        },
                        "required": ["inputs", "operation"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given arguments"""
        if not self.primitives:
            return {"success": False, "error": "No context bound to MCP server"}
            
        try:
            # Handle special cases for parameter conversion
            if tool_name == "signal":
                # Add sender parameter
                arguments["sender"] = self.agent_name
            elif tool_name == "receive":
                # Add receiver parameter
                arguments["receiver"] = self.agent_name
            elif tool_name == "store":
                # Add discoverer parameter
                arguments["discoverer"] = self.agent_name
            elif tool_name == "transfer":
                # Convert amount to appropriate type
                amount = arguments.get("amount", "1")
                if amount != "all" and isinstance(amount, str):
                    try:
                        arguments["amount"] = float(amount)
                    except ValueError:
                        pass  # Keep as string if not a number
            elif tool_name == "modify":
                # Convert value to appropriate type
                value = arguments.get("value", "")
                if isinstance(value, str):
                    try:
                        # Try to convert to number if it looks like one
                        if "." in value:
                            arguments["value"] = float(value)
                        else:
                            arguments["value"] = int(value)
                    except ValueError:
                        pass  # Keep as string if not a number
            elif tool_name == "compute":
                # Convert inputs to appropriate types
                inputs = arguments.get("inputs", [])
                converted_inputs = []
                for inp in inputs:
                    if isinstance(inp, str):
                        try:
                            if "." in inp:
                                converted_inputs.append(float(inp))
                            else:
                                converted_inputs.append(int(inp))
                        except ValueError:
                            converted_inputs.append(inp)
                    else:
                        converted_inputs.append(inp)
                arguments["inputs"] = converted_inputs
            
            # Execute the tool
            result = getattr(self.primitives, tool_name)(**arguments)
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @property
    def _tools(self) -> Dict[str, Any]:
        """Return available tools for debugging"""
        return {
            "observe": "Gather information about entities",
            "signal": "Send communication to other agents", 
            "query": "Search collective memory",
            "transfer": "Move resources between entities",
            "modify": "Change entity properties",
            "connect": "Create relationships",
            "detect": "Find patterns in data",
            "receive": "Listen for signals",
            "store": "Save insights to memory",
            "compute": "Process information"
        }
