"""
Simple Meta-Agent for basic system monitoring
"""

from typing import Dict, Any, List
from .game_state import GameState
from .memory import Memory

class MetaAgent:
    """Simple meta-agent that monitors basic system health"""
    
    def __init__(self):
        self.name = "META_AGENT"
        self.role = "meta_monitor"
    
    def analyze_system_state(self, game_state: GameState, memory: Memory) -> Dict[str, Any]:
        """Analyze basic system state"""
        
        # Get all agents
        agents = [entity for entity in game_state.entities.values() 
                 if entity.get('type') == 'agent']
        
        # Simple analysis
        analysis = {
            "observation_loops": self._detect_observation_loops(memory),
            "communication_breakdown": self._detect_communication_breakdown(memory),
            "overall_health": self._assess_overall_health(memory)
        }
        
        # Determine if intervention is needed
        intervention_needed = (
            analysis["observation_loops"]["detected"] or
            analysis["communication_breakdown"]["detected"]
        )
        
        analysis["intervention_needed"] = intervention_needed
        analysis["intervention_rationale"] = "System needs intervention" if intervention_needed else "System healthy"
        
        return analysis
    
    def _detect_observation_loops(self, memory: Memory) -> Dict[str, Any]:
        """Detect if agents are stuck in observation loops"""
        
        if not hasattr(memory, 'events') or not memory.events:
            return {"detected": False, "details": "No events to analyze"}
        
        # Get recent events
        recent_events = memory.events[-20:] if len(memory.events) > 20 else memory.events
        
        # Count observation actions
        observation_count = sum(1 for event in recent_events if event.get('action') == 'observe')
        total_actions = len(recent_events)
        
        if total_actions == 0:
            return {"detected": False, "details": "No actions to analyze"}
        
        observation_ratio = observation_count / total_actions
        loop_detected = observation_ratio > 0.7
        
        return {
            "detected": loop_detected,
            "ratio": observation_ratio,
            "details": f"Observation ratio: {observation_ratio:.1%}"
        }
    
    def _detect_communication_breakdown(self, memory: Memory) -> Dict[str, Any]:
        """Detect communication breakdown between agents"""
        
        if not hasattr(memory, 'events') or not memory.events:
            return {"detected": False, "details": "No events to analyze"}
        
        # Get recent events
        recent_events = memory.events[-20:] if len(memory.events) > 20 else memory.events
        
        # Count communication actions
        comm_actions = ['signal', 'receive', 'connect', 'transfer']
        comm_count = sum(1 for event in recent_events if event.get('action') in comm_actions)
        total_actions = len(recent_events)
        
        if total_actions == 0:
            return {"detected": False, "details": "No actions to analyze"}
        
        comm_ratio = comm_count / total_actions
        breakdown_detected = comm_ratio < 0.2
        
        return {
            "detected": breakdown_detected,
            "ratio": comm_ratio,
            "details": f"Communication ratio: {comm_ratio:.1%}"
        }
    
    def _assess_overall_health(self, memory: Memory) -> Dict[str, Any]:
        """Assess overall system health"""
        
        if not hasattr(memory, 'events') or not memory.events:
            return {"score": 0.5, "details": "No events to analyze"}
        
        recent_events = memory.events[-10:] if len(memory.events) > 10 else memory.events
        
        # Calculate health score based on action diversity
        action_types = [event.get('action', '') for event in recent_events]
        unique_actions = len(set(action_types))
        total_actions = len(action_types)
        
        if total_actions == 0:
            return {"score": 0.5, "details": "No actions to analyze"}
        
        diversity_score = unique_actions / total_actions
        health_score = min(1.0, diversity_score * 2)
        
        return {
            "score": health_score,
            "details": f"System health: {health_score:.1%}"
        }
    
    def generate_intervention(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate simple interventions"""
        
        interventions = []
        
        if analysis["observation_loops"]["detected"]:
            interventions.append({
                "type": "encourage_communication",
                "description": "Encourage agents to communicate more",
                "priority": "high"
            })
        
        if analysis["communication_breakdown"]["detected"]:
            interventions.append({
                "type": "facilitate_communication",
                "description": "Facilitate communication between agents",
                "priority": "high"
            })
        
        return interventions
    
    def apply_intervention(self, intervention: Dict[str, Any], game_state: GameState, memory: Memory) -> bool:
        """Apply a simple intervention"""
        
        try:
            if intervention["type"] == "encourage_communication":
                memory.add_event({
                    "actor": "META_AGENT",
                    "action": "intervention",
                    "message": "Try more communication - signal and receive",
                    "timestamp": game_state.timestamp
                })
                return True
            
            elif intervention["type"] == "facilitate_communication":
                memory.add_event({
                    "actor": "META_AGENT",
                    "action": "intervention",
                    "message": "Focus on building relationships - connect and transfer",
                    "timestamp": game_state.timestamp
                })
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to apply intervention: {e}")
            return False