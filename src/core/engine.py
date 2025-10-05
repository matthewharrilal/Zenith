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
from .visual_display import SimulationDisplay

class GameEngine:
    def __init__(self):
        self.memory = Memory()
        self.game_state = GameState()
        self.agents: List[Agent] = []
        self.primitives: Optional[PrimitiveTools] = None
        self.visualizer = SimulationDisplay()
        self.round_number = 0
        
    def setup_scenario(self, scenario_name: str):
        """Initialize scenario - currently only safehouse"""
        if scenario_name == "safehouse":
            self._setup_safehouse()
        else:
            raise ValueError(f"Unknown scenario: {scenario_name}")
            
        # Create primitive tools interface
        self.primitives = PrimitiveTools(self.game_state, self.memory)
        
    def _setup_safehouse(self):
        """Initialize the safe house scenario with enhanced complexity"""
        self.game_state.timestamp = 0.0
        
        # Add player agents
        self.agents = [
            create_player_agent("RAVEN"),
            create_player_agent("FALCON"), 
            create_player_agent("VIPER")
        ]
        
        # DM agent removed/disabled
        
        # Initialize entities with more complex relationships
        self.game_state.add_entity("RAVEN", {
            "role": "player",
            "location": "safe_house_interior",
            "stress_level": 0.3,
            "resources": ["lockpicks", "stealth_training", "intel_contacts"],
            "relationships": {"FALCON": 0.2, "VIPER": -0.1},  # Slight trust, slight distrust
            "knowledge": ["safe_house_layout", "security_protocols"],
            "health": 85,
            "specialization": "infiltration"
        })
        
        self.game_state.add_entity("FALCON", {
            "role": "player", 
            "location": "safe_house_interior",
            "stress_level": 0.2,
            "resources": ["explosives", "technical_skills", "hacking_tools"],
            "relationships": {"RAVEN": 0.2, "VIPER": 0.1},
            "knowledge": ["electronic_systems", "explosive_chemistry"],
            "health": 90,
            "specialization": "technical"
        })
        
        self.game_state.add_entity("VIPER", {
            "role": "player",
            "location": "safe_house_interior", 
            "stress_level": 0.4,
            "resources": ["vehicle_access", "combat_training", "weapons"],
            "relationships": {"RAVEN": -0.1, "FALCON": 0.1},
            "knowledge": ["escape_routes", "combat_tactics"],
            "health": 80,
            "specialization": "combat"
        })
        
        # Enhanced environment with multiple pressure sources
        self.game_state.add_entity("environment", {
            "threat_level": 0.15,  # Slightly higher initial threat
            "escalation_rate": 0.08,  # Faster escalation
            "atmosphere": "tense",
            "dm_controlled": True,
            "security_breach_detected": False,
            "time_until_discovery": 45.0,  # Countdown timer
            "weather": "stormy",  # Additional pressure
            "visibility": 0.6
        })
        
        # Multiple exit options requiring different approaches
        self.game_state.add_entity("main_exit", {
            "barrier_strength": 100,
            "complexity": 85,
            "requires_cooperation": True,
            "lock_type": "electronic",
            "tools_needed": ["technical_skills", "hacking_tools"]
        })
        
        self.game_state.add_entity("emergency_exit", {
            "barrier_strength": 60,
            "complexity": 40,
            "requires_cooperation": False,
            "lock_type": "mechanical",
            "tools_needed": ["lockpicks"],
            "risk_level": 0.7  # Higher risk but easier
        })
        
        self.game_state.add_entity("window_exit", {
            "barrier_strength": 30,
            "complexity": 20,
            "requires_cooperation": False,
            "lock_type": "none",
            "tools_needed": ["stealth_training"],
            "risk_level": 0.9,  # Very high risk
            "height": 15  # Requires help
        })
        
        # Additional environmental elements
        self.game_state.add_entity("security_system", {
            "status": "active",
            "sensitivity": 0.7,
            "cameras": 3,
            "motion_detectors": 2,
            "can_be_disabled": True
        })
        
        self.game_state.add_entity("supplies", {
            "food": 3,
            "water": 2,
            "medical": 1,
            "tools": ["rope", "flashlight", "radio"]
        })
        
        print("🏠 SAFE HOUSE SCENARIO INITIALIZED")
        print("Three agents wake up in a compromised safe house...")
        print("They must work together to escape before discovery.")
        print("Multiple exit options available - each with different risks and requirements.")
        print("Time until discovery: 45 minutes")
        print("-" * 50)
    
    def run_round(self):
        """Run round with sequential agent turns for better interaction"""
        
        print(f"[DEBUG] Starting round {self.round_number}")
        
        # Collect agent actions sequentially
        agents_data = []
        for i, agent in enumerate(self.agents):
            print(f"[DEBUG] Processing agent {agent.name} ({i+1}/{len(self.agents)})")
            try:
                # Get agent action
                action, params, reasoning = agent.get_action(
                    self.game_state, self.memory, self.primitives  
                )
                print(f"[DEBUG] {agent.name} chose: {action}")
            except Exception as e:
                print(f"[DEBUG] {agent.name} error: {e}")
                action, params, reasoning = "observe", {"entity_id": "environment", "resolution": 0.5}, f"Error: {e}"
            
            agents_data.append({
                'name': agent.name,
                'action': action,
                'params': params,
                'reasoning': reasoning
            })
            
            # Execute action immediately and store in memory
            if action != "none":
                result = self._execute_action(action, params, agent.name)
                
                # Store in memory
                self.memory.add_event(
                    actor=agent.name,
                    action=action,
                    params=params,
                    result=result,
                    reasoning=reasoning
                )
        
        # Display round with all actions
        print(f"[DEBUG] About to display round {self.round_number}")
        self.visualizer.display_round(
            self.round_number,
            self.game_state.timestamp,
            agents_data,
            self.game_state
        )
        print(f"[DEBUG] Display completed for round {self.round_number}")
        
        # Periodic insights
        self.visualizer.display_pattern_insight()
        
        # Advance round
        self.round_number += 1
        self.game_state.timestamp += 1.0  # Standard time increment
        print(f"[DEBUG] Round {self.round_number-1} completed, advancing to {self.round_number}")
    
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
                
                return primitive_func(**normalized_params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def run_simulation(self, max_time: float = 500.0, use_balanced_display: bool = False) -> Dict[str, Any]:
        """Run simulation with balanced display by default"""
        
        if use_balanced_display:
            return self._run_balanced_simulation(max_time)
        else:
            return self._run_verbose_simulation(max_time)
    
    def _run_balanced_simulation(self, max_time: float = 500.0) -> Dict[str, Any]:
        """Run simulation with clean balanced display"""
        
        start_time = time.time()
        action_count = 0
        max_rounds = 25  # Increased for more meaningful simulations
        safety_timeout = 300  # 5 minutes safety limit for API calls
        
        print(f"🚀 Starting balanced simulation (max {max_rounds} rounds)...")
        
        while (self.round_number < max_rounds and 
               self.game_state.timestamp < max_time and 
               not self._natural_stopping_point() and
               time.time() - start_time < safety_timeout):  # Increased safety limit
            
            try:
                print(f"[DEBUG] About to run round {self.round_number}")
                # Run a round with balanced display
                self.run_round()
                print(f"[DEBUG] Completed round {self.round_number}")
                action_count += 3  # Approximate actions per round
                
                # Environmental updates
                self._update_environment()
                
            except KeyboardInterrupt:
                print("\n⏸️ Simulation interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error in round {self.round_number}: {e}")
                break
        
        print(f"\n✅ Simulation completed after {self.round_number} rounds")
        
        # Analyze results
        return self._analyze_game_results(action_count)
    
    def _run_verbose_simulation(self, max_time: float = 500.0) -> Dict[str, Any]:
        """Run simulation with verbose display (legacy)"""
        
        start_time = time.time()
        action_count = 0
        
        while (self.game_state.timestamp < max_time and 
               not self._natural_stopping_point() and
               time.time() - start_time < 300):  # 5 minute safety limit
            
            # Get next acting agent
            acting_agent = self._choose_next_agent()
            
            if acting_agent:
                # Execute agent action
                self._execute_agent_turn(acting_agent)
                action_count += 1
                
                # Environmental updates
                self._update_environment()
                
                # Advance time based on action complexity
                time_increment = random.uniform(0.5, 2.0)
                self.game_state.timestamp += time_increment
                
            else:
                # No agents can act - end simulation
                break
        
        # Analyze results
        return self._analyze_game_results(action_count)
    
    def _choose_next_agent(self) -> Optional[Agent]:
        """Choose which agent acts next - simple round robin for MVP"""
        active_agents = [a for a in self.agents if self._agent_can_act(a)]
        
        if not active_agents:
            return None
            
        # Simple selection - can be enhanced with stress levels, etc.
        return random.choice(active_agents)
    
    def _agent_can_act(self, agent: Agent) -> bool:
        """Check if agent is capable of acting"""
        agent_state = self.game_state.get_entity(agent.name)
        return (agent_state.get("stress_level", 0) < 1.0 and  # Not incapacitated
                agent_state.get("status", "active") == "active")
    
    def _execute_agent_turn(self, agent: Agent):
        """Execute single agent action"""
        try:
            # Get agent decision
            action_name, params, reasoning = agent.get_action(
                self.game_state, self.memory, self.primitives
            )
            
            # Smart turn display with progress indicator
            threat_level = self.game_state.get_entity("environment").get("threat_level", 0)
            threat_bar = "█" * int(threat_level * 20) + "░" * (20 - int(threat_level * 20))
            
            print("")
            print(f"🎭 {agent.name} │ Time: {self.game_state.timestamp:.1f}s │ Threat: [{threat_bar}] {threat_level:.1%}")
            print("―" * 80)
            parsed = self._display_agent_reasoning(reasoning)
            
            # Execute action through primitives
            result = self._execute_primitive_action(agent, action_name, params)
            
            # Display result
            self._display_action_result(
                agent.name,
                action_name,
                params,
                result,
                why=parsed.get('why') if isinstance(parsed, dict) else None,
                not_chosen=parsed.get('not_chosen') if isinstance(parsed, dict) else None
            )
            
            # Store in memory (normalize parameters first)
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
            
        except Exception as e:
            print(f"Error executing {agent.name}'s turn: {e}")
    
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
        """Update environmental pressures"""
        environment = self.game_state.get_entity("environment")
        if environment:
            # Threat escalation
            current_threat = environment.get("threat_level", 0.1)
            escalation_rate = environment.get("escalation_rate", 0.05)
            new_threat = min(1.0, current_threat + escalation_rate * 0.1)
            
            self.game_state.modify_entity("environment", "threat_level", new_threat)
            
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
        if self.game_state.timestamp > 50.0:  # Increased from 20.0
            recent_events = [e for e in self.memory.events if 
                           float(e.get('timestamp', '0').split('T')[1].split(':')[2]) > self.game_state.timestamp - 10.0]
            if len(recent_events) == 0:
                print("\n✅ SCENARIO ENDED: Natural resolution reached")
                return True
        
        # Check exit door status - require more cooperation
        exit_door = self.game_state.get_entity("exit_door")
        if exit_door and exit_door.get("barrier_strength", 100) <= 10:  # More realistic threshold
            print("\n🚪 SCENARIO ENDED: Exit achieved")
            return True
        
        # Check if agents have discovered key patterns (emergence indicator)
        if len(self.memory.patterns) >= 3 and self.game_state.timestamp > 15.0:
            print("\n🧠 SCENARIO ENDED: Sufficient emergence patterns discovered")
            return True
        
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
    
    def _display_agent_reasoning(self, reasoning: str) -> Dict[str, Any]:
        """Display compact PLAN/CHOOSE/REFLECT with alternatives (high-signal) and return parsed parts.
        Adds subtle visual separators and graceful fallbacks when sections are absent.
        """
        if not reasoning:
            return {"plan": [], "why": "", "not_chosen": "", "reflect": ""}
        lines = [l.strip() for l in reasoning.split('\n') if l.strip()]
        
        # Extract PLAN bullets (following a line starting with 'PLAN:')
        plan_items: List[str] = []
        in_plan = False
        for line in lines:
            upper = line.upper()
            if upper.startswith('PLAN:'):
                in_plan = True
                # capture inline content if present
                inline = line.split(':', 1)[1].strip()
                if inline:
                    plan_items.append(inline)
                continue
            if in_plan:
                if upper.startswith(('CHOOSE:', 'ACT:', 'REFLECT:')):
                    in_plan = False
                elif line.startswith(('-', '•', '*')):
                    plan_items.append(line.lstrip('-•* ').strip())
                else:
                    # stop plan on non-bullet free text
                    in_plan = False
        
        # Extract CHOOSE (full line after 'CHOOSE:')
        choose_text = next((line.split(':', 1)[1].strip() for line in lines if line.upper().startswith('CHOOSE:')), '')
        
        # Try to split CHOOSE into reason and not-chosen clause
        why_text = choose_text
        not_chosen_text = ''
        if 'Not chosen:' in choose_text:
            parts = choose_text.split('Not chosen:', 1)
            why_text = parts[0].strip()
            not_chosen_text = parts[1].strip()
        elif 'Not Chosen:' in choose_text:
            parts = choose_text.split('Not Chosen:', 1)
            why_text = parts[0].strip()
            not_chosen_text = parts[1].strip()
        
        # Extract REFLECT (single line)
        reflect_text = next((line.split(':', 1)[1].strip() for line in lines if line.upper().startswith('REFLECT:')), '')
        
        # Render compact view
        # Visual spacing: thin rule between blocks for readability
        if plan_items:
            shown = '; '.join([f"- {p}" for p in plan_items[:2]])
            print(f"         🧭 Plan: {shown}")
        if why_text:
            print(f"         ✅ Choice: {why_text}")
        if not_chosen_text:
            print(f"         🔎 Alternatives: {not_chosen_text}")
        if reflect_text:
            print(f"         🔄 Reflect: {reflect_text}")
        # subtle divider
        print(f"         ·")
        
        return {"plan": plan_items, "why": why_text, "not_chosen": not_chosen_text, "reflect": reflect_text}
    
    # DM display removed
    
    def _display_action_result(self, actor: str, action: str, params: Dict, result: Dict, why: Optional[str] = None, not_chosen: Optional[str] = None):
        """Display action results with concise, relevant key facts and reasoning context.
        If 'why' is missing, derive a short fallback based on action type.
        """
        success = result.get('success', False)
        
        # Create action signature
        param_pairs = []
        for k, v in params.items():
            if isinstance(v, str):
                param_pairs.append(f"{k}='{v}'")
            else:
                param_pairs.append(f"{k}={v}")
        action_sig = f"{action}({', '.join(param_pairs)})"
        
        # Compact action display
        status_icon = "✅" if success else "❌"
        print(f"         {status_icon} {action_sig}")
        # Fallback rationale if missing
        if not why or not why.strip():
            action_lower = (action or "").lower()
            if action_lower == "observe":
                why = "Establish situational baseline before coordination."
            elif action_lower == "signal":
                why = "Elicit intentions and open a communication loop."
            elif action_lower == "receive":
                why = "Gather incoming information to inform next step."
            elif action_lower == "query":
                why = "Leverage memory to avoid repeating past mistakes."
            elif action_lower == "detect":
                why = "Reveal hidden patterns/relationships not visible via observation."
            elif action_lower == "connect":
                why = "Formalize a relationship to enable cooperation."
            elif action_lower == "transfer":
                why = "Demonstrate commitment or re-balance resources."
            elif action_lower == "modify":
                why = "Change the environment/entity to enable progress."
            elif action_lower == "store":
                why = "Preserve newfound insights for later use."
            elif action_lower == "compute":
                why = "Synthesize inputs to guide next action."
            else:
                why = "No explicit rationale provided."
        print(f"         🧠 Why: {why}")
        if not_chosen:
            print(f"         ↪️ Alternatives: {not_chosen}")
        # extra whitespace for readability between actions
        print("")
        
        if success:
            # Prefer a small set of salient fields for readability
            if 'observations' in result:
                obs = result['observations']
                if isinstance(obs, dict):
                    preferred_keys = ['threat_level', 'visibility', 'barrier_strength', 'status', 'resources', 'location']
                    shown_pairs: List[str] = []
                    for key in preferred_keys:
                        if key in obs:
                            shown_pairs.append(f"{key}={obs[key]}")
                    if not shown_pairs:
                        # fallback to at most 3 generic entries
                        items = [(k, v) for k, v in obs.items() if not str(k).startswith('_')][:3]
                        shown_pairs = [f"{k}={v}" for k, v in items]
                    print(f"         📊 {'; '.join(shown_pairs)}")
                else:
                    text = str(obs)
                    print(f"         📊 {text[:80]}{'...' if len(text) > 80 else ''}")
            elif 'signals' in result:
                signals = result['signals']
                count = len(signals) if isinstance(signals, list) else 1
                print(f"         📡 {count} signal(s)")
            elif 'stored_knowledge' in result:
                knowledge = result['stored_knowledge']
                snippet = knowledge if isinstance(knowledge, str) else str(knowledge)
                print(f"         💾 {snippet[:80]}{'...' if len(snippet) > 80 else ''}")
            elif 'connection_strength' in result:
                strength = result['connection_strength']
                print(f"         🤝 Strength: {strength}")
            elif result.get('result'):
                result_str = str(result['result'])
                print(f"         📈 {result_str[:80]}{'...' if len(result_str) > 80 else ''}")
                
        else:
            error = result.get('error', 'Unknown error')
            print(f"         ⚠️ {error}")
    
    def save_memory(self, filename: str):
        """Save persistent memory"""
        self.memory.save_to_file(filename)
        
    def load_memory(self, filename: str):
        """Load persistent memory"""
        self.memory.load_from_file(filename)
