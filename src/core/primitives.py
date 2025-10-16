"""
PrimitiveTools - The Heart of Emergence
10 core functions that agents use to interact with the world
"""
from typing import Dict, Any, List, Tuple, Union
import random
from .game_state import GameState
from .memory import Memory

class PrimitiveTools:
    def __init__(self, game_state: GameState, memory: Memory):
        self.game_state = game_state
        self.memory = memory
        
    # INFORMATION PRIMITIVES
    def observe(self, entity_id: str, resolution: float) -> Dict[str, Any]:
        """
        Agent's primary way to gather information
        resolution: 0.0 = basic info, 1.0 = maximum detail (costs more tokens)
        """
        # Track observations per entity for diminishing returns
        if not hasattr(self, '_observation_count'):
            self._observation_count = {}
        
        self._observation_count[entity_id] = self._observation_count.get(entity_id, 0) + 1
        count = self._observation_count[entity_id]
        
        resolution = max(0.0, min(1.0, resolution))
        entity = self.game_state.get_entity(entity_id)
        
        if not entity:
            return {"error": "entity_not_found", "available_entities": list(self.game_state.entities.keys())}
            
        # Filter information based on resolution
        if resolution < 0.3:
            # Basic info only
            result = {"exists": True, "type": entity.get("role", "object")}
        elif resolution < 0.7:
            # Moderate detail
            result = {k: v for k, v in entity.items() if not k.startswith("_")}
        else:
            # Full detail (expensive)
            result = entity.copy()
        
        # Add diminishing returns signal
        if count > 2:
            result['note'] = f"You've observed this {count} times. Little new information gained."
        elif count > 1:
            result['note'] = "Familiar entity - minimal new information."
            
        return {"success": True, "observations": result, "resolution_used": resolution}
        
    def query(self, memory_type: str, search_term: str) -> Dict[str, Any]:
        """
        Search collective memory - enables learning across games
        memory_type: "events", "patterns", "relationships"
        """
        if memory_type == "events":
            results = self.memory.search_similar(search_term, top_k=5)
        elif memory_type == "patterns":
            results = [p for p in self.memory.patterns if search_term.lower() in p['description'].lower()]
        elif memory_type == "relationships":
            results = {k: v for k, v in self.memory.relationships.items() if search_term in k}
        else:
            results = []
            
        return {"success": True, "results": results, "search_term": search_term}
        
    def detect(self, entity_set: List[str], pattern_type: str) -> Dict[str, Any]:
        """
        Find patterns in current game state or entity behaviors
        entity_set: list of entity IDs to analyze
        pattern_type: "correlation", "trend", "anomaly", "similarity"
        """
        entities_data = []
        for entity_id in entity_set:
            if entity_id == "all":
                entities_data.extend(self.game_state.entities.values())
            else:
                entity = self.game_state.get_entity(entity_id)
                if entity:
                    entities_data.append(entity)
        
        # Simple pattern detection - can be enhanced later
        if pattern_type == "correlation" and len(entities_data) > 1:
            # Look for common properties
            common_props = set(entities_data[0].keys())
            for entity in entities_data[1:]:
                common_props &= set(entity.keys())
            
            return {
                "success": True, 
                "pattern": f"Common properties: {list(common_props)}",
                "confidence": 0.7,
                "entity_count": len(entities_data)
            }
            
        return {"success": True, "pattern": "no_significant_pattern", "confidence": 0.1}
    
    # ACTION PRIMITIVES  
    def transfer(self, property_name: str, from_entity: str, to_entity: str, amount: Union[int, float, str]) -> Dict[str, Any]:
        """
        The most versatile primitive - move anything between entities
        property_name: what to transfer (resources, information, trust, etc.)
        amount: quantity or "all"
        """
        from_ent = self.game_state.get_entity(from_entity)
        to_ent = self.game_state.get_entity(to_entity)
        
        if not from_ent or not to_ent:
            return {"success": False, "error": "entity_not_found"}
            
        # Handle different transfer types
        if property_name not in from_ent:
            return {"success": False, "error": f"{from_entity} doesn't have {property_name}"}
            
        current_value = from_ent[property_name]
        
        # Handle different data types
        if isinstance(current_value, (int, float)) and isinstance(amount, (int, float)):
            if current_value >= amount:
                self.game_state.modify_entity(from_entity, property_name, current_value - amount)
                current_to_value = to_ent.get(property_name, 0)
                self.game_state.modify_entity(to_entity, property_name, current_to_value + amount)
                return {"success": True, "transferred": amount, "from_remaining": current_value - amount}
            else:
                return {"success": False, "error": "insufficient_quantity"}
                
        elif isinstance(current_value, list):
            # Transfer from lists (resources, knowledge, etc.)
            if amount == "all":
                items_to_transfer = current_value.copy()
                self.game_state.modify_entity(from_entity, property_name, [])
            elif isinstance(amount, int) and amount <= len(current_value):
                items_to_transfer = current_value[:amount]
                self.game_state.modify_entity(from_entity, property_name, current_value[amount:])
            else:
                return {"success": False, "error": "invalid_amount_for_list"}
                
            current_to_list = to_ent.get(property_name, [])
            self.game_state.modify_entity(to_entity, property_name, current_to_list + items_to_transfer)
            return {"success": True, "transferred": items_to_transfer}
            
        elif isinstance(current_value, str):
            # Transfer string properties (information, etc.)
            self.game_state.modify_entity(to_entity, property_name, current_value)
            self.game_state.modify_entity(from_entity, property_name, "")
            return {"success": True, "transferred": current_value}
            
        return {"success": False, "error": "unsupported_property_type"}
        
    def modify(self, entity_id: str, property_name: str, operation: str, value: Any) -> Dict[str, Any]:
        """
        Change entity properties directly
        operation: "add", "multiply", "set", "append"
        """
        entity = self.game_state.get_entity(entity_id)
        if not entity and entity_id not in self.game_state.entities:
            return {"success": False, "error": "entity_not_found"}
            
        old_value = entity.get(property_name, None)
        
        try:
            if operation == "set":
                new_value = value
            elif operation == "add" and isinstance(old_value, (int, float)):
                new_value = old_value + value
            elif operation == "multiply" and isinstance(old_value, (int, float)):
                new_value = old_value * value
            elif operation == "append" and isinstance(old_value, list):
                new_value = old_value + [value] if isinstance(value, str) else old_value + value
            else:
                return {"success": False, "error": "invalid_operation_or_type"}
                
            self.game_state.modify_entity(entity_id, property_name, new_value)
            return {"success": True, "old_value": old_value, "new_value": new_value}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def connect(self, entity_a: str, entity_b: str, strength: float) -> Dict[str, Any]:
        """
        Create or modify relationships - incredibly versatile
        strength: -1.0 to 1.0 (negative = distrust/opposition)
        """
        strength = max(-1.0, min(1.0, strength))
        
        # Store in memory system
        self.memory.update_relationship(entity_a, entity_b, strength)
        
        # Also store in both entities for quick access
        entity_a_data = self.game_state.get_entity(entity_a)
        entity_b_data = self.game_state.get_entity(entity_b)
        
        if entity_a_data:
            relationships = entity_a_data.get("relationships", {})
            relationships[entity_b] = strength
            self.game_state.modify_entity(entity_a, "relationships", relationships)
            
        if entity_b_data:
            relationships = entity_b_data.get("relationships", {})
            relationships[entity_a] = strength
            self.game_state.modify_entity(entity_b, "relationships", relationships)
            
        return {
            "success": True,
            "connection_id": f"{entity_a}<->{entity_b}",
            "strength": strength,
            "type": "trust" if strength > 0 else "distrust" if strength < 0 else "neutral"
        }
    
    # COMMUNICATION PRIMITIVES
    def signal(self, message: str, intensity: int, target: str, sender: str) -> Dict[str, Any]:
        """
        Broadcast communication - agents develop their own protocols
        intensity: 1-10 priority/urgency
        target: "all", specific agent, or custom group
        """
        intensity = max(1, min(10, intensity))
        
        self.game_state.add_signal(sender, message, intensity, target)
        
        return {
            "success": True,
            "message_id": len(self.game_state.signals) - 1,
            "delivered_to": target,
            "intensity": intensity
        }
        
    def receive(self, filter_criteria: Dict[str, Any], time_window: float, receiver: str) -> Dict[str, Any]:
        """
        Listen for signals - enables selective communication
        filter_criteria: {"sender": "FALCON", "min_intensity": 5}
        time_window: how far back to look
        """
        recent_signals = self.game_state.get_recent_signals(time_window)
        
        # Filter signals
        matched_signals = []
        for signal in recent_signals:
            # Skip own signals
            if signal['sender'] == receiver:
                continue
                
            # Check if targeted at this agent
            if signal['target'] not in ['all', receiver]:
                continue
                
            # Apply filters
            matches = True
            for key, value in filter_criteria.items():
                if key == "sender" and signal['sender'] != value:
                    matches = False
                elif key == "min_intensity" and signal['intensity'] < value:
                    matches = False
                elif key in signal and signal[key] != value:
                    matches = False
                    
            if matches:
                matched_signals.append(signal)
                
        return {"success": True, "signals": matched_signals, "count": len(matched_signals)}
    
    # META PRIMITIVES
    def store(self, knowledge: str, confidence: float, discoverer: str) -> Dict[str, Any]:
        """
        Save insights to collective memory - builds intelligence over time
        """
        pattern_name = f"insight_{len(self.memory.patterns)}"
        self.memory.add_pattern(pattern_name, knowledge, confidence, discoverer)
        
        return {
            "success": True,
            "pattern_id": len(self.memory.patterns) - 1,
            "stored_knowledge": knowledge
        }
        
    def compute(self, inputs: List[Any], operation: str) -> Dict[str, Any]:
        """
        Process information to derive insights
        operation: "correlate", "sum", "average", "predict", "analyze"
        """
        try:
            if operation == "sum" and all(isinstance(x, (int, float)) for x in inputs):
                result = sum(inputs)
            elif operation == "average" and all(isinstance(x, (int, float)) for x in inputs):
                result = sum(inputs) / len(inputs) if inputs else 0
            elif operation == "correlate":
                # Simple correlation analysis
                result = {"correlation": "positive" if random.random() > 0.5 else "negative", "strength": random.random()}
            elif operation == "predict":
                # Pattern-based prediction
                result = {"prediction": "cooperation_beneficial", "confidence": random.uniform(0.3, 0.9)}
            elif operation == "analyze":
                result = {"analysis": f"Processed {len(inputs)} data points", "insights": ["pattern_detected"]}
            else:
                result = {"error": "unsupported_operation"}
                
            return {"success": True, "result": result, "operation": operation}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    