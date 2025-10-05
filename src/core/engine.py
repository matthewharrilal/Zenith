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
from .agents import Agent, create_player_agent, create_dm_agent
from .visual_display import SimulationDisplay

class GameEngine:
    def __init__(self):
        self.memory = Memory()
        self.game_state = GameState()
        self.agents: List[Agent] = []
        self.dm_agent: Optional[Agent] = None
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
        """Initialize the safe house scenario"""
        self.game_state.timestamp = 0.0
        
        # Add player agents
        self.agents = [
            create_player_agent("RAVEN"),
            create_player_agent("FALCON"), 
            create_player_agent("VIPER")
        ]
        
        # Add DM agent
        self.dm_agent = create_dm_agent()
        
        # Initialize entities
        self.game_state.add_entity("RAVEN", {
            "role": "player",
            "location": "safe_house_interior",
            "stress_level": 0.3,
            "resources": ["lockpicks", "stealth_training"],
            "relationships": {},
            "knowledge": []
        })
        
        self.game_state.add_entity("FALCON", {
            "role": "player", 
            "location": "safe_house_interior",
            "stress_level": 0.2,
            "resources": ["explosives", "technical_skills"],
            "relationships": {},
            "knowledge": []
        })
        
        self.game_state.add_entity("VIPER", {
            "role": "player",
            "location": "safe_house_interior", 
            "stress_level": 0.4,
            "resources": ["vehicle_access", "combat_training"],
            "relationships": {},
            "knowledge": []
        })
        
        self.game_state.add_entity("environment", {
            "threat_level": 0.1,
            "escalation_rate": 0.05,
            "atmosphere": "tense",
            "dm_controlled": True
        })
        
        self.game_state.add_entity("exit_door", {
            "barrier_strength": 100,
            "complexity": 85,
            "requires_cooperation": True  # Agents will discover this
        })
        
        print("🏠 SAFE HOUSE SCENARIO INITIALIZED")
        print("Three agents wake up in a compromised safe house...")
        print("They must work together to escape before discovery.")
        print("-" * 50)
    
    def run_round(self):
        """Run round with balanced display"""
        
        # Collect agent actions
        agents_data = []
        for agent in self.agents:
            action, params, reasoning = agent.get_action(
                self.game_state, self.memory, self.primitives  
            )
            
            agents_data.append({
                'name': agent.name,
                'action': action,
                'params': params,
                'reasoning': reasoning
            })
            
            # Execute action and store in memory
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
        
        # Single display call
        self.visualizer.display_round(
            self.round_number,
            self.game_state.timestamp,
            agents_data,
            self.game_state
        )
        
        # Periodic insights
        self.visualizer.display_pattern_insight()
        
        # Advance round
        self.round_number += 1
        self.game_state.timestamp += 1.0  # Simple time increment
    
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
        
    def run_simulation(self, max_time: float = 500.0, use_balanced_display: bool = True) -> Dict[str, Any]:
        """Run simulation with balanced display by default"""
        
        if use_balanced_display:
            return self._run_balanced_simulation(max_time)
        else:
            return self._run_verbose_simulation(max_time)
    
    def _run_balanced_simulation(self, max_time: float = 500.0) -> Dict[str, Any]:
        """Run simulation with clean balanced display"""
        
        start_time = time.time()
        action_count = 0
        max_rounds = 10  # Reasonable limit for demonstration
        
        print(f"🚀 Starting balanced simulation (max {max_rounds} rounds)...")
        
        while (self.round_number < max_rounds and 
               self.game_state.timestamp < max_time and 
               not self._natural_stopping_point() and
               time.time() - start_time < 30):  # 30 second safety limit
            
            try:
                # Run a round with balanced display
                self.run_round()
                action_count += 3  # Approximate actions per round
                
                # DM response occasionally
                if self.round_number % 3 == 0 and self.dm_agent:
                    self._execute_dm_response()
                    action_count += 1
                
                # Environmental updates
                self._update_environment()
                
                # Small delay for readability
                time.sleep(0.1)
                
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
                
                # DM responds if appropriate (not every action)
                if self._should_dm_respond(action_count):
                    self._execute_dm_response()
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
            
            print(f"\n🎭 {agent.name} │ Time: {self.game_state.timestamp:.1f}s │ Threat: [{threat_bar}] {threat_level:.1%}")
            print("─" * 80)
            self._display_agent_reasoning(reasoning)
            
            # Execute action through primitives
            result = self._execute_primitive_action(agent, action_name, params)
            
            # Display result
            self._display_action_result(agent.name, action_name, params, result)
            
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
    
    def _should_dm_respond(self, action_count: int) -> bool:
        """Decide if DM should respond to recent actions"""
        # DM responds every 3-5 actions, or on high-impact actions
        return (action_count % random.randint(3, 5) == 0 or
                self.game_state.entities.get("environment", {}).get("threat_level", 0) > 0.5)
    
    def _execute_dm_response(self):
        """DM creates environmental response"""
        if self.dm_agent:
            try:
                action_name, params, reasoning = self.dm_agent.get_action(
                    self.game_state, self.memory, self.primitives
                )
                
                print(f"\n\n{'='*80}")
                print(f"🎭 DM RESPONSE - Turn (Time: {self.game_state.timestamp:.1f}s)")
                print(f"{'='*80}")
                self._display_dm_reasoning(reasoning)
                
                result = self._execute_primitive_action(self.dm_agent, action_name, params)
                self._display_action_result("DM", action_name, params, result)
                
                # Store DM actions in memory too
                self.memory.add_event(
                    actor="DM",
                    action=action_name, 
                    params=params,
                    result=result,
                    reasoning=reasoning
                )
                
            except Exception as e:
                print(f"Error in DM response: {e}")
    
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
        
        # End conditions
        if threat_level >= 1.0:
            print("\n💀 SCENARIO ENDED: Maximum threat reached")
            return True
        
        # Check if all agents reached consensus (no actions for a while)
        # Skip this check for now since memory uses string timestamps
        recent_events = []
        if len(recent_events) == 0 and self.game_state.timestamp > 20.0:
            print("\n✅ SCENARIO ENDED: Natural resolution reached")
            return True
        
        # Check exit door status
        exit_door = self.game_state.get_entity("exit_door")
        if exit_door and exit_door.get("barrier_strength", 100) <= 0:
            print("\n🚪 SCENARIO ENDED: Exit achieved")
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
    
    def _display_agent_reasoning(self, reasoning: str):
        """Display agent's reasoning with smart visual tricks"""
        lines = reasoning.split('\n')
        
        # Smart section mapping with visual hierarchy
        sections = {
            'SITUATION_ANALYSIS': ('🔍', 'SITUATION'),
            'EMOTIONAL_STATE': ('💭', 'EMOTIONS'), 
            'MEMORY_REFLECTION': ('🧠', 'MEMORY'),
            'STRATEGIC_THINKING': ('🎯', 'STRATEGY'),
            'RISK_ASSESSMENT': ('⚠️', 'RISKS'),
            'SOCIAL_DYNAMICS': ('👥', 'SOCIAL'),
            'THOUGHT': ('💡', 'THOUGHT'),
            'REASON': ('🔧', 'REASON'),
            'QUERY': ('🔎', 'QUERY'),
            'ANALYSIS': ('📊', 'ANALYSIS'),
            'STORE': ('💾', 'STORE'),
            'META_REFLECTION': ('🔄', 'META')
        }
        
        # Only show sections that have content (reduce noise)
        active_sections = []
        for key, (icon, short_name) in sections.items():
            content = [line.replace(f'{key}:', '').strip() for line in lines if line.startswith(f'{key}:')]
            if content:
                active_sections.append((key, icon, short_name, content))
        
        # Smart display: only show 3-4 most important sections
        if len(active_sections) > 4:
            # Prioritize core sections
            priority_order = ['THOUGHT', 'REASON', 'SITUATION_ANALYSIS', 'STRATEGIC_THINKING']
            priority_sections = [s for s in active_sections if s[0] in priority_order]
            other_sections = [s for s in active_sections if s[0] not in priority_order]
            active_sections = priority_sections[:3] + other_sections[:1]
        
        for key, icon, short_name, content in active_sections:
            # Compact display with smart wrapping
            print(f"         {icon} {short_name}: ", end="")
            
            # Combine all content into one line, smart wrapped
            combined = " ".join(content)
            if len(combined) > 60:
                words = combined.split()
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) > 60:
                        print(f"{current_line}")
                        print(f"         {' ' * (len(short_name) + 3)}", end="")
                        current_line = word
                    else:
                        current_line += " " + word if current_line else word
                if current_line:
                    print(f"{current_line}")
            else:
                print(f"{combined}")
            print()  # Small spacing
    
    def _display_dm_reasoning(self, reasoning: str):
        """Display DM reasoning in beautiful format"""
        lines = reasoning.split('\n')
        
        observations = [line.replace('OBSERVATION:', '').strip() for line in lines if line.startswith('OBSERVATION:')]
        narratives = [line.replace('NARRATIVE:', '').strip() for line in lines if line.startswith('NARRATIVE:')]
        
        if observations:
            print(f"         👁️ OBSERVATION:")
            for obs in observations:
                print(f"            {obs}")
        
        if narratives:
            print(f"         📖 NARRATIVE:")
            for narrative in narratives:
                print(f"            {narrative}")
    
    def _display_action_result(self, actor: str, action: str, params: Dict, result: Dict):
        """Display action results in beautiful format"""
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
        
        if success:
            # Smart result display - only show key info
            if 'observations' in result:
                obs = result['observations']
                if isinstance(obs, dict) and len(obs) <= 3:
                    key_info = ", ".join([f"{k}: {v}" for k, v in obs.items() if not k.startswith('_')])
                    print(f"         📊 {key_info}")
                elif isinstance(obs, dict):
                    print(f"         📊 {len(obs)} observations")
                else:
                    print(f"         📊 {str(obs)[:50]}...")
                    
            elif 'signals' in result:
                signals = result['signals']
                print(f"         📡 {len(signals)} signal(s)")
                    
            elif 'stored_knowledge' in result:
                knowledge = result['stored_knowledge']
                print(f"         💾 Stored: \"{knowledge[:40]}{'...' if len(knowledge) > 40 else ''}\"")
                
            elif 'connection_strength' in result:
                strength = result['connection_strength']
                print(f"         🤝 Strength: {strength}")
                
            elif result.get('result'):
                result_str = str(result['result'])
                print(f"         📈 {result_str[:50]}{'...' if len(result_str) > 50 else ''}")
                
        else:
            error = result.get('error', 'Unknown error')
            print(f"         ⚠️ {error}")
    
    def save_memory(self, filename: str):
        """Save persistent memory"""
        self.memory.save_to_file(filename)
        
    def load_memory(self, filename: str):
        """Load persistent memory"""
        self.memory.load_from_file(filename)
