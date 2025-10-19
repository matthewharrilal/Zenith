"""
Memory System - Foundation of Emergent Intelligence
Handles event storage, pattern recognition, and vector similarity search
"""
from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import json
import re
from datetime import datetime

class Memory:
    # Memory type constants (DRY - single source of truth)
    PERCEPTION = "perception"
    ACTION = "action"
    OUTCOME = "outcome"
    LEARNING = "learning"
    HYPOTHESIS = "hypothesis"
    
    # Tool classification mapping (DRY - avoid repeated if/else)
    PERCEPTION_TOOLS = {"observe", "query", "receive", "detect"}
    ACTION_TOOLS = {"modify", "signal", "connect", "transfer", "store", "compute"}
    
    def __init__(self):
        # Existing (backward compatibility)
        self.events: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []  
        self.relationships: Dict[str, float] = {}
        
        # New typed storage (initialize as dict for extensibility)
        self._typed_events: Dict[str, List[Dict]] = {
            self.PERCEPTION: [],
            self.ACTION: [],
            self.OUTCOME: [],
            self.LEARNING: [],
            self.HYPOTHESIS: []
        }
        
        # Vectorizers per type (lazy initialization)
        self._vectorizers: Dict[str, Optional[TfidfVectorizer]] = {
            t: None for t in self._typed_events.keys()
        }
        self._type_vectors: Dict[str, Optional[np.ndarray]] = {
            t: None for t in self._typed_events.keys()
        }
        
        # Legacy vector search setup - defer until first use
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.event_vectors: Optional[np.ndarray] = None
    
    @property
    def perceptions(self) -> List[Dict]:
        """Property for backward compatibility and clean access"""
        return self._typed_events[self.PERCEPTION]
    
    @property
    def actions(self) -> List[Dict]:
        return self._typed_events[self.ACTION]
    
    @property
    def outcomes(self) -> List[Dict]:
        return self._typed_events[self.OUTCOME]
    
    @property
    def learnings(self) -> List[Dict]:
        return self._typed_events[self.LEARNING]
    
    @property
    def hypotheses(self) -> List[Dict]:
        return self._typed_events[self.HYPOTHESIS]
    
    def classify_event(self, event: Dict[str, Any]) -> str:
        """
        Classify event into memory type.
        
        KEEP SIMPLE: No brittle logic. Tool-based classification only.
        Future: Milestone 1.3 can override with mark_critical flag.
        """
        # Already classified (from auto-generation)
        if "type" in event:
            return event["type"]
        
        tool = event.get("action", "")
        
        # Simple lookup (no nested if/else)
        if tool in self.PERCEPTION_TOOLS:
            return self.PERCEPTION
        elif tool in self.ACTION_TOOLS:
            return self.ACTION
        else:
            return self.ACTION  # Default to action
    
    def add_event(self, event: Dict[str, Any]) -> None:
        """
        Add event to both flat and typed storage.
        
        EXTENSIBLE: Future milestones can add hooks here.
        - 1.3: Check for critical flag
        - 1.4: Update plan references
        - 2.1: Update belief states
        """
        # Add to flat list (backward compatibility)
        self.events.append(event)
        
        # Classify and add to typed storage
        event_type = self.classify_event(event)
        self._typed_events[event_type].append(event)
        
        # Invalidate vectorizer for this type (lazy rebuild)
        self._vectorizers[event_type] = None
        self._type_vectors[event_type] = None
    
    def add_event_with_auto_generation(self, event: Dict[str, Any]) -> None:
        """
        Add event and auto-generate secondary events.
        
        EXTENSIBLE: Easy to add more generators without modifying this.
        """
        # Add primary event
        self.add_event(event)
        
        # Generate secondary events
        generators = [
            EventAutoGenerator.generate_outcome,
            EventAutoGenerator.generate_learning,
            EventAutoGenerator.generate_hypothesis
        ]
        
        for generator in generators:
            secondary_event = generator(event)
            if secondary_event:
                self.add_event(secondary_event)
    
    def add_event_legacy(self, actor: str, action: str, params: Dict, result: Dict, reasoning: str):
        """Store event - the core data structure of the system (legacy method)"""
        event = {
            'id': len(self.events),
            'timestamp': datetime.now().isoformat(),
            'actor': actor,
            'action': action,
            'params': params,
            'result': result, 
            'reasoning': reasoning,
            # Searchable text for vector similarity
            'searchable_text': f"{actor} {action} {reasoning} {str(params)} {str(result)}"
        }
        self.add_event(event)  # Use new typed storage
        self._update_vectors()  # Lazy vector update
        
        # No automatic pattern detection - let agents discover their own patterns
    
    def query_by_type(
        self, 
        event_type: str, 
        search_term: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query specific memory type with semantic search.
        
        SIMPLE: Reuse existing search_similar logic, just scoped to type.
        NO BLOAT: Don't reinvent TF-IDF, use existing implementation.
        """
        # Validate type
        if event_type not in self._typed_events:
            return []
        
        typed_events = self._typed_events[event_type]
        
        if not typed_events:
            return []
        
        # Use existing search logic (DRY)
        return self._semantic_search(typed_events, search_term, top_k, event_type)
    
    def _semantic_search(
        self,
        events: List[Dict],
        query: str,
        top_k: int,
        event_type: str
    ) -> List[Dict]:
        """
        Semantic search within event list using TF-IDF.
        
        EXTRACTED: Shared logic for query_by_type and search_similar.
        LAZY: Only build vectorizer when needed.
        """
        if len(events) < 2:
            return events[:top_k]
        
        # Build searchable texts
        texts = [e.get("searchable_text", "") for e in events]
        
        # Lazy vectorizer initialization
        if self._vectorizers[event_type] is None:
            self._vectorizers[event_type] = TfidfVectorizer(
                max_features=1000, 
                stop_words='english',
                ngram_range=(1, 2)
            )
            try:
                self._type_vectors[event_type] = self._vectorizers[event_type].fit_transform(texts)
            except ValueError:
                return events[-top_k:]  # Fallback to recent
        
        # Transform query
        try:
            query_vec = self._vectorizers[event_type].transform([query])
            similarities = (self._type_vectors[event_type] * query_vec.T).toarray().flatten()
            
            # Get top-k indices above threshold
            threshold = 0.1
            top_indices = [
                i for i in np.argsort(similarities)[::-1]
                if similarities[i] > threshold
            ][:top_k]
            
            return [events[i] for i in top_indices]
            
        except Exception:
            return events[-top_k:]  # Fallback to recent
        
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Vector similarity search - agents query this during reasoning"""
        if not self.events:
            return []
            
        # Lazy initialization of vectorizer
        if self.vectorizer is None:
            self._initialize_vectors()
            
        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.event_vectors)[0]
            
            # Get top results with confidence threshold
            top_indices = similarities.argsort()[-top_k:][::-1]
            results = []
            
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum relevance threshold
                    event = self.events[idx].copy()
                    event['similarity'] = float(similarities[idx])
                    results.append(event)
            
            return results
        except Exception as e:
            print(f"Memory search error: {e}")
            return self.events[-top_k:]  # Fallback to recent events
    
    def add_pattern(self, name: str, description: str, confidence: float, discoverer: str):
        """Store discovered strategies/insights"""
        pattern = {
            'id': len(self.patterns),
            'name': name,
            'description': description,
            'confidence': max(0.0, min(1.0, confidence)),
            'discovered_by': discoverer,
            'timestamp': datetime.now().isoformat(),
            'usage_count': 0  # Track how often pattern is referenced
        }
        self.patterns.append(pattern)
        
    def update_relationship(self, agent_a: str, agent_b: str, value: float):
        """Track dynamic relationships between agents"""
        key = f"{agent_a}->{agent_b}"
        self.relationships[key] = max(-1.0, min(1.0, value))
        
    def save_to_file(self, filename: str):
        """Persist memory across game sessions"""
        data = {
            'events': self.events,
            'patterns': self.patterns,
            'relationships': self.relationships,
            'typed_events': self._typed_events,
            'metadata': {'total_events': len(self.events), 'save_time': datetime.now().isoformat()}
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
            
    def load_from_file(self, filename: str):
        """Load persistent memory"""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                self.events = data['events']
                self.patterns = data['patterns']  
                self.relationships = data['relationships']
                
                # Load typed events if available (backward compatibility)
                if 'typed_events' in data:
                    self._typed_events = data['typed_events']
                else:
                    # Rebuild typed events from flat events
                    self._rebuild_typed_events()
                
                self._update_vectors()
        except Exception as e:
            print(f"Failed to load memory: {e}")
    
    def _rebuild_typed_events(self):
        """Rebuild typed events from flat events (for backward compatibility)"""
        # Clear existing typed events
        for event_type in self._typed_events:
            self._typed_events[event_type] = []
        
        # Reclassify all events
        for event in self.events:
            event_type = self.classify_event(event)
            self._typed_events[event_type].append(event)
    
    def _initialize_vectors(self):
        """Lazy vector initialization - only when needed"""
        if not self.events:
            return
            
        self.vectorizer = TfidfVectorizer(
            max_features=1000, 
            stop_words='english',
            ngram_range=(1, 2)  # Include bigrams for better context
        )
        
        texts = [event['searchable_text'] for event in self.events]
        self.event_vectors = self.vectorizer.fit_transform(texts).toarray()
    
    def _update_vectors(self):
        """Update vectors when new events added"""
        if self.vectorizer is not None:
            self._initialize_vectors()  # Rebuild all vectors


class EventAutoGenerator:
    """
    Auto-generate secondary events (outcomes, learnings, hypotheses).
    
    DESIGN PRINCIPLES:
    - Each generator is a pure function (testable)
    - No brittle regex patterns (simple keyword matching)
    - High confidence threshold (avoid noise)
    - Easy to disable per type (flag-based)
    
    EXTENSIBLE: Future milestones can add generators without modifying existing ones.
    """
    
    # Configuration (easy to tune without code changes)
    OUTCOME_ENABLED = True
    LEARNING_ENABLED = True
    HYPOTHESIS_ENABLED = True
    
    LEARNING_CONFIDENCE_THRESHOLD = 0.3
    HYPOTHESIS_CONFIDENCE_THRESHOLD = 0.5
    
    # Hypothesis keywords (simple, not brittle)
    HYPOTHESIS_KEYWORDS = {
        "explicit": ["hypothesis", "hypothesize"],
        "belief": ["believe", "think"],
        "prediction": ["might", "could", "would"]
    }
    
    @staticmethod
    def generate_outcome(action_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate outcome event from action result.
        
        SIMPLE: Just extract success/failure, no complex logic.
        """
        if not EventAutoGenerator.OUTCOME_ENABLED:
            return None
        
        result = action_event.get("result")
        if not result or not isinstance(result, dict):
            return None
        
        # Only generate for action tools
        if action_event.get("action") not in Memory.ACTION_TOOLS:
            return None
        
        return {
            "type": Memory.OUTCOME,
            "actor": action_event.get("actor"),
            "related_action_id": action_event.get("id"),
            "action_type": action_event.get("action"),
            "success": result.get("success", False),
            "error": result.get("error"),
            "timestamp": action_event.get("timestamp"),
            "searchable_text": EventAutoGenerator._build_outcome_text(action_event, result)
        }
    
    @staticmethod
    def generate_learning(tool_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate learning from detect/compute/store results.
        
        SIMPLE: Extract pattern/insight if confidence above threshold.
        """
        if not EventAutoGenerator.LEARNING_ENABLED:
            return None
        
        tool = tool_event.get("action")
        result = tool_event.get("result", {})
        
        # detect() learning
        if tool == "detect":
            pattern = result.get("pattern")
            confidence = result.get("confidence", 0.0)
            
            if pattern and pattern != "no_significant_pattern" and confidence >= EventAutoGenerator.LEARNING_CONFIDENCE_THRESHOLD:
                return {
                    "type": Memory.LEARNING,
                    "source": "detect",
                    "actor": tool_event.get("actor"),
                    "pattern": pattern,
                    "confidence": confidence,
                    "timestamp": tool_event.get("timestamp"),
                    "searchable_text": f"learning pattern {pattern}"
                }
        
        # compute() learning
        elif tool == "compute":
            if result.get("success"):
                insight = str(result.get("result", ""))
                return {
                    "type": Memory.LEARNING,
                    "source": "compute",
                    "actor": tool_event.get("actor"),
                    "insight": insight,
                    "confidence": 0.8,
                    "timestamp": tool_event.get("timestamp"),
                    "searchable_text": f"learning computation {insight}"
                }
        
        # store() learning (explicit agent storage)
        elif tool == "store":
            knowledge = tool_event.get("params", {}).get("knowledge", "")
            confidence = tool_event.get("params", {}).get("confidence", 0.9)
            
            if knowledge:
                return {
                    "type": Memory.LEARNING,
                    "source": "store",
                    "actor": tool_event.get("actor"),
                    "insight": knowledge,
                    "confidence": confidence,
                    "timestamp": tool_event.get("timestamp"),
                    "searchable_text": f"learning insight {knowledge}"
                }
        
        return None
    
    @staticmethod
    def generate_hypothesis(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract hypothesis from reasoning text.
        
        SIMPLE: Keyword matching only, no complex NLP.
        HIGH BAR: Only extract when clear indicators present.
        """
        if not EventAutoGenerator.HYPOTHESIS_ENABLED:
            return None
        
        reasoning = event.get("reasoning", "")
        if not reasoning or len(reasoning) < 20:
            return None
        
        # Try explicit patterns first (highest confidence)
        for keyword in EventAutoGenerator.HYPOTHESIS_KEYWORDS["explicit"]:
            if keyword in reasoning.lower():
                hypothesis_text = EventAutoGenerator._extract_after_keyword(reasoning, keyword)
                if hypothesis_text:
                    return EventAutoGenerator._create_hypothesis_event(
                        event, hypothesis_text, confidence=0.9
                    )
        
        # Try belief patterns (medium confidence)
        for keyword in EventAutoGenerator.HYPOTHESIS_KEYWORDS["belief"]:
            if keyword in reasoning.lower():
                hypothesis_text = EventAutoGenerator._extract_after_keyword(reasoning, keyword)
                if hypothesis_text and not EventAutoGenerator._is_action_plan(hypothesis_text):
                    return EventAutoGenerator._create_hypothesis_event(
                        event, hypothesis_text, confidence=0.7
                    )
        
        return None
    
    @staticmethod
    def _extract_after_keyword(text: str, keyword: str, max_length: int = 200) -> Optional[str]:
        """Extract text after keyword, up to sentence boundary or max_length."""
        lower_text = text.lower()
        idx = lower_text.find(keyword)
        
        if idx == -1:
            return None
        
        # Find start of hypothesis (after keyword)
        start = idx + len(keyword)
        # Skip common words after keyword
        for skip_word in [" is ", " that ", ":", " - "]:
            if lower_text[start:].startswith(skip_word):
                start += len(skip_word)
        
        # Extract until sentence boundary or max_length
        end = start + max_length
        hypothesis = text[start:end].strip()
        
        # Truncate at sentence boundary
        for boundary in [".", "!", "?", "\n"]:
            if boundary in hypothesis:
                hypothesis = hypothesis.split(boundary)[0].strip()
        
        return hypothesis if len(hypothesis) > 10 else None
    
    @staticmethod
    def _is_action_plan(text: str) -> bool:
        """Filter out action plans (not hypotheses)."""
        action_indicators = ["should", "will", "need to", "going to", "plan to"]
        return any(indicator in text.lower() for indicator in action_indicators)
    
    @staticmethod
    def _create_hypothesis_event(event: Dict, hypothesis: str, confidence: float) -> Dict:
        """Create hypothesis event from extracted text."""
        return {
            "type": Memory.HYPOTHESIS,
            "actor": event.get("actor"),
            "hypothesis": hypothesis,
            "confidence": confidence,
            "timestamp": event.get("timestamp"),
            "searchable_text": f"hypothesis {hypothesis}"
        }
    
    @staticmethod
    def _build_outcome_text(action_event: Dict, result: Dict) -> str:
        """Build searchable text for outcome event."""
        action = action_event.get("action", "")
        success = "success" if result.get("success") else "failure"
        error = result.get("error", "")
        return f"outcome {action} {success} {error}".strip()
