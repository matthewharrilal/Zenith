"""
GameEngine - Orchestration & Flow
Manages the simulation loop and emergence detection
"""
from typing import Dict, Any, List, Optional
import time
import random
from .memory import Memory
from .game_state import GameState
from .primitives import PrimitiveTools
from .agents import Agent, create_player_agent
from .meta_agent import MetaAgent

class GameEngine:
    def __init__(self):
        self.memory = Memory()
        self.game_state = GameState()
        self.agents: List[Agent] = []
        self.primitives: Optional[PrimitiveTools] = None
        self.meta_agent = MetaAgent()
        self.action_count = 0
        
    def setup_scenario(self, scenario_name: str):
        """Initialize scenario - currently only safehouse"""
        if scenario_name == "safehouse":
            self._setup_safehouse()
        else:
            raise ValueError(f"Unknown scenario: {scenario_name}")
            
        # Create primitive tools interface
        self.primitives = PrimitiveTools(self.game_state, self.memory)
        
    def _setup_safehouse(self):
        """Initialize safehouse escape scenario"""
        self.game_state.timestamp = 0.0
        
        # Add player agents with escape goal
        self.agents = [
            create_player_agent("AGENT_A"),
            create_player_agent("AGENT_B"), 
            create_player_agent("AGENT_C")
        ]
        
        # Agent entities with escape context
        for agent in self.agents:
            self.game_state.add_entity(agent.name, {
                "status": "active",
                "goal": "escape_safehouse",
                "location": "safehouse_interior"
            })
        
        # Environment with escape scenario
        self.game_state.add_entity("environment", {
            "status": "active",
            "location": "safehouse",
            "threat_level": 0.0,
            "escape_route": "unknown",
            "exits": ["front_door", "back_door", "window"]
        })
        
        # Add escape-related entities
        self.game_state.add_entity("front_door", {
            "status": "locked",
            "type": "exit",
            "difficulty": "high"
        })
        
        self.game_state.add_entity("back_door", {
            "status": "locked", 
            "type": "exit",
            "difficulty": "medium"
        })
        
        self.game_state.add_entity("window", {
            "status": "accessible",
            "type": "exit", 
            "difficulty": "low"
        })
        
        print("🏠 SAFEHOUSE ESCAPE SCENARIO INITIALIZED")
        print("Three agents are trapped in a safehouse and need to escape.")
        print("The threat level is rising - they must work together to escape!")
        print("Available exits: front door (locked), back door (locked), window (accessible)")
        print("-" * 50)
    
    
    def _execute_action(self, action: str, params: Dict, agent_name: str):
        """Execute a single action"""
        try:
            if action == "none":
                return {"success": True, "result": {"message": "No action taken"}}
            
            # Use primitives to execute action
            action_name_lower = action.lower()
            primitive_func = getattr(self.primitives, action_name_lower, None)
            if primitive_func:
                # Normalize parameter names for common issues
                normalized_params = params.copy()
                if action_name_lower == "query" and "search" in normalized_params and "search_term" not in normalized_params:
                    normalized_params["search_term"] = normalized_params.pop("search")
                
                result = primitive_func(**normalized_params)
                
                # Update social dynamics
                self.game_state.update_social_dynamics(agent_name, action, self.memory)
                
                return result
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _run_meta_agent_analysis(self):
        """Run Meta-Agent analysis and apply interventions if needed"""
        try:
            # Analyze system state
            analysis = self.meta_agent.analyze_system_state(self.game_state, self.memory)
            
            # Check if intervention is needed
            if analysis["intervention_needed"]:
                print(f"\n🧠 META-AGENT INTERVENTION: {analysis['intervention_rationale']}")
                
                # Generate interventions
                interventions = self.meta_agent.generate_intervention(analysis)
                
                # Apply interventions
                for intervention in interventions:
                    success = self.meta_agent.apply_intervention(intervention, self.game_state, self.memory)
                    if success:
                        print(f"✅ Applied intervention: {intervention['type']}")
                    else:
                        print(f"❌ Failed to apply intervention: {intervention['type']}")
                        
        except Exception as e:
            print(f"⚠️ Meta-Agent analysis failed: {e}")
        
    def run_simulation(self, max_time: float = 500.0) -> Dict[str, Any]:
        """Run simulation with simple display"""
        return self._run_balanced_simulation(max_time)
    
    def _run_balanced_simulation(self, max_time: float = 500.0) -> Dict[str, Any]:
        """Run simulation with dynamic agent selection"""
        
        start_time = time.time()
        action_count = 0
        max_actions = 100  # Maximum total actions
        
        print(f"🚀 Starting simulation (max {max_actions} actions)...")
        
        while (action_count < max_actions and 
               self.game_state.timestamp < max_time and 
               not self._natural_stopping_point() and
               time.time() - start_time < 300):
            
            try:
                # Choose next agent to act
                acting_agent = self._choose_next_agent()
                
                if acting_agent:
                    self._execute_agent_turn(acting_agent)
                    action_count += 1
                    self.action_count = action_count
                    self._update_environment()
                    
                    # Run meta-agent analysis every 10 actions
                    if action_count % 10 == 0:
                        self._run_meta_agent_analysis()
                else:
                    # No agents can act - end simulation
                    break
                
            except KeyboardInterrupt:
                print("\n⏸️ Simulation interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error in action {action_count}: {e}")
                break
        
        print(f"\n✅ Simulation completed after {action_count} actions")
        return self._analyze_game_results(action_count)
    
    
    def _choose_next_agent(self) -> Optional[Agent]:
        """Choose which agent acts next - dynamic selection based on urgency and activity"""
        active_agents = [a for a in self.agents if self._agent_can_act(a)]
        
        if not active_agents:
            return None
        
        # Weight selection based on agent state and recent activity
        weights = []
        for agent in active_agents:
            agent_state = self.game_state.get_entity(agent.name)
            weight = 1.0
            
            # Increase weight for agents with higher stress (more urgent)
            stress = agent_state.get("stress_level", 0.0)
            weight += stress * 0.5
            
            # Decrease weight for agents who acted recently (less likely to act again immediately)
            recent_actions = [e for e in self.memory.events[-5:] if e.get('actor') == agent.name]
            if recent_actions:
                weight *= 0.7
            
            # Increase weight for agents with escape urgency
            if agent_state.get("escape_urgency", False):
                weight *= 1.5
                
            weights.append(weight)
        
        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(active_agents)
            
        r = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return active_agents[i]
        
        return active_agents[-1]  # Fallback
    
    def _agent_can_act(self, agent: Agent) -> bool:
        """Check if agent is capable of acting"""
        agent_state = self.game_state.get_entity(agent.name)
        return (agent_state.get("stress_level", 0) < 1.0 and  # Not incapacitated
                agent_state.get("status", "active") == "active")
    
    def _execute_agent_turn(self, agent: Agent):
        """Execute agent actions (multiple tool calls)"""
        try:
            # Get agent decision (multiple tool calls)
            tool_calls, reasoning = agent.get_action(
                self.game_state, self.memory, self.primitives
            )
            
            # Clean display with better spacing
            threat_level = self.game_state.get_entity("environment").get("threat_level", 0)
            print(f"\n🎭 {agent.name} │ Time: {self.game_state.timestamp:.1f}s │ Threat: {threat_level:.1%}")
            
            # Show detailed reasoning that explains the "why" - no truncation
            if reasoning and reasoning.strip():
                # Extract meaningful reasoning lines, skipping headers
                reasoning_lines = reasoning.split('\n')
                meaningful_lines = []
                for line in reasoning_lines:
                    line = line.strip()
                    if (line and 
                        not line.startswith('TOOL STRATEGY:') and 
                        not line.startswith('REFLECTION:') and 
                        not line.startswith('**') and 
                        not line.startswith('PLAN:') and
                        not line.startswith('CHOOSE:') and
                        not line.startswith('ACT:') and
                        not line.startswith('-') and
                        len(line) > 20):
                        meaningful_lines.append(line)
                
                if meaningful_lines:
                    # Show up to 3 meaningful lines for context - no truncation
                    for line in meaningful_lines[:3]:
                        # Add whitespace between sentences for better readability
                        sentences = line.split('. ')
                        if len(sentences) > 1:
                            for i, sentence in enumerate(sentences):
                                if sentence.strip():
                                    if not sentence.endswith('.'):
                                        sentence += '.'
                                    print(f"💭 {sentence.strip()}")
                        else:
                            print(f"💭 {line}")
                else:
                    # Fallback to any non-empty line - no truncation
                    for line in reasoning_lines:
                        line = line.strip()
                        if line and len(line) > 20:
                            # Add whitespace between sentences for better readability
                            sentences = line.split('. ')
                            if len(sentences) > 1:
                                for i, sentence in enumerate(sentences):
                                    if sentence.strip():
                                        if not sentence.endswith('.'):
                                            sentence += '.'
                                        print(f"💭 {sentence.strip()}")
                            else:
                                print(f"💭 {line}")
                            break
            
            print()  # Add spacing before actions
            
            # Execute all tool calls with clean display
            for i, (action_name, params) in enumerate(tool_calls):
                if action_name != "none":
                    # Execute action through primitives
                    result = self._execute_primitive_action(agent, action_name, params)
                    
                    # Clean action display with better spacing
                    action_num = f"[{i+1}/{len(tool_calls)}]" if len(tool_calls) > 1 else ""
                    print(f"  {action_num} {action_name.upper()}({self._format_params(params)})", end="")
                    
                    # Show result inline
                    if result.get("success"):
                        result_summary = self._format_result_summary(result)
                        if result_summary != "Action completed":
                            print(f" → {result_summary}")
                        else:
                            print()
                    else:
                        print(f" → ❌ {result.get('error', 'Failed')}")
                    
                    # Store in memory
                    normalized_params = params.copy()
                    if action_name == "query" and "search" in normalized_params and "search_term" not in normalized_params:
                        normalized_params["search_term"] = normalized_params.pop("search")
                    
                    self.memory.add_event(
                        actor=agent.name,
                        action=action_name,
                        params=normalized_params,
                        result=result,
                        reasoning=reasoning
                    )
            
            print()  # Add spacing after actions
            
        except Exception as e:
            print(f"Error executing {agent.name}'s turn: {e}")
    
    def _format_params(self, params: Dict) -> str:
        """Format parameters for display - no truncation"""
        if not params:
            return ""
        
        # Show key parameters only - no truncation
        key_params = []
        for key, value in params.items():
            if key in ['entity_id', 'target', 'message', 'memory_type', 'search_term', 'intensity', 'resolution']:
                key_params.append(f"{key}={value}")
        
        return ", ".join(key_params)  # Show all key params
    
    def _format_result_summary(self, result: Dict) -> str:
        """Format result summary for display"""
        if not result:
            return "No result"
        
        # Extract key information based on result type
        if "observations" in result:
            obs = result["observations"]
            if isinstance(obs, dict):
                key_info = []
                for k, v in obs.items():
                    if k in ["exists", "type", "status", "threat_level"]:
                        key_info.append(f"{k}={v}")
                return "; ".join(key_info[:3]) if key_info else "Observation completed"
            return "Observation completed"
        
        elif "signals" in result:
            count = result.get("count", 0)
            return f"Found {count} signals"
        
        elif "transferred" in result:
            return f"Transferred: {result['transferred']}"
        
        elif "connection_id" in result:
            return f"Connection: {result['connection_id']} (strength: {result.get('strength', 'N/A')})"
        
        elif "pattern" in result:
            return f"Pattern: {result['pattern']}"
        
        elif "results" in result:
            count = len(result["results"]) if isinstance(result["results"], list) else 0
            return f"Found {count} results"
        
        else:
            return "Action completed"
    
    def _execute_primitive_action(self, agent: Agent, action_name: str, params: Dict) -> Dict[str, Any]:
        """Execute action through MCP system or primitive tools with validation"""
        try:
            # Handle "none" action gracefully
            if action_name == "none":
                return {"success": True, "result": {"message": "No action taken"}}
            
            # Use the agent's MCP system for execution if available
            if hasattr(agent, 'mcp_server') and agent.mcp_server:
                # Bind context to ensure primitives are available
                agent.mcp_server.bind_context(self.game_state, self.memory, agent.name)
                
                # Execute through MCP system (handles parameter filling automatically)
                result = agent.mcp_server.execute_tool(action_name, params)
                
                # Extract the actual result from MCP response
                if result.get("success"):
                    return result.get("result", {})
                else:
                    return {"success": False, "error": result.get("error", "Unknown error")}
            else:
                # Fallback to direct primitive call (for backward compatibility)
                action_name_lower = action_name.lower()
                primitive_func = getattr(self.primitives, action_name_lower, None)
                if primitive_func:
                    # Normalize parameter names for common issues
                    normalized_params = params.copy()
                    if action_name_lower == "query" and "search" in normalized_params and "search_term" not in normalized_params:
                        normalized_params["search_term"] = normalized_params.pop("search")
                    
                    return primitive_func(**normalized_params)
                else:
                    return {"success": False, "error": f"Unknown action: {action_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _update_environment(self):
        """Update environmental pressures with escape urgency"""
        environment = self.game_state.get_entity("environment")
        if environment:
            # Threat escalation (escape urgency)
            current_threat = environment.get("threat_level", 0.1)
            escalation_rate = environment.get("escalation_rate", 0.05)
            new_threat = min(1.0, current_threat + escalation_rate * 0.15)  # Faster escalation
            
            self.game_state.modify_entity("environment", "threat_level", new_threat)
            
            # Add escape urgency to agents
            if new_threat > 0.3:  # High threat = escape urgency
                for agent in self.agents:
                    if agent.name in self.game_state.entities:
                        agent_entity = self.game_state.entities[agent.name]
                        agent_entity['escape_urgency'] = True
                        agent_entity['threat_level'] = new_threat
            
            # Cleanup old signals
            self.game_state.cleanup_old_signals()
    
    def _natural_stopping_point(self) -> bool:
        """Check if simulation should end naturally"""
        environment = self.game_state.get_entity("environment")
        threat_level = environment.get("threat_level", 0) if environment else 0
        
        # End conditions - made more realistic
        if threat_level >= 0.95:  # Slightly less aggressive
            print("\n💀 SCENARIO ENDED: Critical threat level reached")
            return True
        
        # Check if agents have been inactive for too long (more lenient)
        if self.game_state.timestamp > 100.0:  # Increased from 50.0 to allow longer exploration
            # Simple check: if no events in last 20 time units, end simulation
            recent_events = [e for e in self.memory.events if 
                           hasattr(e, 'timestamp') and float(e.timestamp) > self.game_state.timestamp - 20.0]
            if len(recent_events) == 0:
                print("\n✅ SCENARIO ENDED: Natural resolution reached")
                return True
        
        # Check exit door status - require more cooperation
        exit_door = self.game_state.get_entity("exit_door")
        if exit_door and exit_door.get("barrier_strength", 100) <= 10:  # More realistic threshold
            print("\n🚪 SCENARIO ENDED: Exit achieved")
            return True
        
        # Check if agents have discovered key patterns (emergence indicator)
        # Disabled premature ending - let agents explore longer
        # if len(self.memory.patterns) >= 3 and self.game_state.timestamp > 15.0:
        #     print("\n🧠 SCENARIO ENDED: Sufficient emergence patterns discovered")
        #     return True
        
        return False
    
    def _analyze_game_results(self, action_count: int) -> Dict[str, Any]:
        """Analyze completed game for emergence patterns"""
        
        cooperation_events = len([e for e in self.memory.events if "transfer" in e['action']])
        communication_events = len([e for e in self.memory.events if "signal" in e['action']])
        
        results = {
            "duration": self.game_state.timestamp,
            "total_actions": action_count,
            "cooperation_events": cooperation_events,
            "communication_events": communication_events,
            "patterns_discovered": len(self.memory.patterns),
            "final_threat_level": self.game_state.get_entity("environment").get("threat_level", 0),
            "agents_status": {agent.name: self.game_state.get_entity(agent.name) for agent in self.agents}
        }
        
        print(f"\n{'='*50}")
        print("GAME ANALYSIS:")
        print(f"Duration: {results['duration']:.1f} time units")
        print(f"Total actions: {results['total_actions']}")
        print(f"Cooperation events: {results['cooperation_events']}")
        print(f"Communication events: {results['communication_events']}")
        print(f"Patterns discovered: {results['patterns_discovered']}")
        
        return results
    
    
    def save_memory(self, filename: str):
        """Save persistent memory"""
        self.memory.save_to_file(filename)
        
    def load_memory(self, filename: str):
        """Load persistent memory"""
        self.memory.load_from_file(filename)
