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
        """
        Return OpenAI function schemas for all 10 primitive tools.
        
        DESIGN: Descriptions are scenario-agnostic abstractions.
        - NO scenario-specific examples (no "escape routes")
        - YES universal patterns (entities, patterns, strategies)
        - CLEAR purpose and usage guidance
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "observe",
                    "description": (
                        "Gather information about entities to identify blockers or opportunities. "
                        "Use when you need to understand current state before acting. "
                        "Each observation provides detail based on resolution level. "
                        "Avoid repeated observations of same entity - observe once then act."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "ID of entity to observe (agents, objects, environment)"
                            },
                            "resolution": {
                                "type": "number",
                                "description": "Detail level: 0.0=basic, 1.0=maximum (higher detail costs more tokens)",
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
                    "description": (
                        "Send communication to coordinate with other agents when you need help or want to share information. "
                        "Use to unblock yourself or inform others of your actions. "
                        "Signal your intent once, then act - avoid endless discussion."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Information to communicate"
                            },
                            "intensity": {
                                "type": "integer",
                                "description": "Priority/urgency level (1=low, 10=critical)",
                                "minimum": 1,
                                "maximum": 10
                            },
                            "target": {
                                "type": "string",
                                "description": "Recipients: 'all' for broadcast, or specific agent name"
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
                    "description": (
                        "Search memory by type to find specific information. "
                        "Memory types: 'perception' (observations), 'action' (what you tried), "
                        "'outcome' (results), 'learning' (insights), 'hypothesis' (theories). "
                        "Use typed queries to find relevant information quickly."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "memory_type": {
                                "type": "string",
                                "description": "Type of memory to search",
                                "enum": ["perception", "action", "outcome", "learning", "hypothesis", "all"]
                            },
                            "search_term": {
                                "type": "string",
                                "description": "What to search for"
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
                    "description": (
                        "Move resources, information, or properties between entities. "
                        "Use when entities need to exchange capabilities or knowledge. "
                        "Supports numerical values, lists, and string properties."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "property_name": {
                                "type": "string",
                                "description": "What to transfer (resources, information, capabilities)"
                            },
                            "from_entity": {
                                "type": "string",
                                "description": "Source entity ID"
                            },
                            "to_entity": {
                                "type": "string",
                                "description": "Destination entity ID"
                            },
                            "amount": {
                                "type": "string",
                                "description": "Quantity to transfer (number or 'all')"
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
                    "description": (
                        "Change entity properties to make progress toward goals. "
                        "Use to update state, overcome blockers, or complete objectives. "
                        "Operations: 'set' (replace), 'add' (increment), 'multiply' (scale), 'append' (add to list). "
                        "Can modify yourself or other entities."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "Entity to modify (your agent name, objects, environment)"
                            },
                            "property_name": {
                                "type": "string",
                                "description": "Property to change"
                            },
                            "operation": {
                                "type": "string",
                                "description": "How to change it",
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
                    "description": (
                        "Create or modify relationships between entities. "
                        "Use to build trust, establish alliances, or track connections. "
                        "Strength ranges from -1.0 (opposition) to +1.0 (strong alliance)."
                    ),
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
                                "description": "Relationship strength (-1.0 to +1.0)",
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
                    "description": (
                        "Find correlations, trends, or anomalies in entity data. "
                        "Use when you need to understand relationships between multiple entities. "
                        "Reveals patterns that aren't obvious from individual observations. "
                        "Pattern types: 'correlation' (commonalities), 'trend' (changes over time), "
                        "'anomaly' (outliers), 'similarity' (comparable entities)."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_set": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Entity IDs to analyze (minimum 2 entities)"
                            },
                            "pattern_type": {
                                "type": "string",
                                "description": "Type of pattern to find",
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
                    "description": (
                        "Listen for signals from other agents. "
                        "Use to check what others have communicated. "
                        "Filter by sender or minimum priority to focus on relevant messages."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter_criteria": {
                                "type": "object",
                                "description": "Message filters (sender, min_intensity)",
                                "properties": {
                                    "sender": {"type": "string"},
                                    "min_intensity": {"type": "integer"}
                                }
                            },
                            "time_window": {
                                "type": "number",
                                "description": "How far back to look (seconds)"
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
                    "description": (
                        "Save discoveries about entities, patterns, or strategies for later reference. "
                        "Use when you learn something important about the world or other agents. "
                        "Stored insights become learnings that persist across turns. "
                        "Examples: discovered capabilities, effective strategies, entity relationships."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "knowledge": {
                                "type": "string",
                                "description": "Insight or discovery to remember"
                            },
                            "confidence": {
                                "type": "number",
                                "description": "How certain you are (0.0=guess, 1.0=verified)",
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
                    "description": (
                        "Calculate statistics or analyze patterns from numerical data. "
                        "Use when you need to process multiple observations or measurements. "
                        "Operations: 'sum' (total), 'average' (mean), 'correlate' (relationship strength), "
                        "'predict' (forecast), 'analyze' (interpret patterns). "
                        "Results become learnings for future decisions."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "inputs": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Numerical data to process"
                            },
                            "operation": {
                                "type": "string",
                                "description": "Computation to perform",
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
            # Handle typed query
            if tool_name == "query":
                memory_type = arguments.get("memory_type", "all")
                search_term = arguments.get("search_term", "")
                
                if memory_type == "all":
                    # Query all types, return dict
                    results = {}
                    for t in ["perception", "action", "outcome", "learning", "hypothesis"]:
                        results[t] = self.memory.query_by_type(t, search_term)
                    return {"success": True, "results": results}
                else:
                    # Query specific type
                    results = self.memory.query_by_type(memory_type, search_term)
                    return {"success": True, "results": results}
            
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
