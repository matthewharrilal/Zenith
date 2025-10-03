"""
GameState - Flexible Entity System
Everything is an entity that can be modified and extended dynamically
"""
from typing import Dict, Any, List
from datetime import datetime
import copy

class GameState:
    def __init__(self):
        self.timestamp = 0.0
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.signals: List[Dict[str, Any]] = []  # Active communications
        self.metadata: Dict[str, Any] = {}       # Game-specific data
        
    def add_entity(self, entity_id: str, properties: Dict[str, Any]):
        """Add new entity to world - can be agent, object, location, concept"""
        self.entities[entity_id] = copy.deepcopy(properties)
        
    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get entity properties - returns empty dict if not found"""
        return self.entities.get(entity_id, {})
        
    def modify_entity(self, entity_id: str, property_name: str, value: Any):
        """Modify entity property - create if doesn't exist"""
        if entity_id not in self.entities:
            self.entities[entity_id] = {}
        self.entities[entity_id][property_name] = value
        
    def add_signal(self, sender: str, message: str, intensity: int, target: str):
        """Add communication signal to environment"""
        signal = {
            'sender': sender,
            'message': message, 
            'intensity': intensity,
            'target': target,
            'timestamp': self.timestamp,
            'id': len(self.signals)
        }
        self.signals.append(signal)
        
    def get_recent_signals(self, time_window: float, target_filter: str = None) -> List[Dict]:
        """Get signals within time window, optionally filtered by target"""
        recent_signals = []
        cutoff_time = self.timestamp - time_window
        
        for signal in self.signals:
            if signal['timestamp'] >= cutoff_time:
                if target_filter is None or signal['target'] in ['all', target_filter]:
                    recent_signals.append(signal)
                    
        return recent_signals
        
    def cleanup_old_signals(self, max_age: float = 100.0):
        """Remove old signals to prevent memory bloat"""
        cutoff_time = self.timestamp - max_age
        self.signals = [s for s in self.signals if s['timestamp'] >= cutoff_time]
        
    def get_all_agent_entities(self) -> Dict[str, Dict[str, Any]]:
        """Get all entities that appear to be agents"""
        agents = {}
        for entity_id, properties in self.entities.items():
            # Heuristic: entities with 'role' or typical agent properties
            if ('role' in properties or 
                'stress_level' in properties or 
                'resources' in properties or
                entity_id in ['RAVEN', 'FALCON', 'VIPER', 'DM']):
                agents[entity_id] = properties
        return agents
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for debugging/analysis"""
        return {
            'timestamp': self.timestamp,
            'entities': self.entities,
            'signal_count': len(self.signals),
            'metadata': self.metadata
        }
