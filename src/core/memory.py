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
from datetime import datetime

class Memory:
    def __init__(self):
        # Simple lists - easily debuggable and extensible
        self.events: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []  
        self.relationships: Dict[str, float] = {}
        
        # Vector search setup - defer until first use
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.event_vectors: Optional[np.ndarray] = None
        
    def add_event(self, actor: str, action: str, params: Dict, result: Dict, reasoning: str):
        """Store event - the core data structure of the system"""
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
        self.events.append(event)
        self._update_vectors()  # Lazy vector update
        
        # Auto-detect patterns when enough events accumulate
        if len(self.events) >= 5 and len(self.events) % 3 == 0:
            self._auto_detect_patterns()
        
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
                self._update_vectors()
        except Exception as e:
            print(f"Failed to load memory: {e}")
    
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
    
    def _auto_detect_patterns(self):
        """Automatically detect patterns from recent events"""
        if len(self.events) < 5:
            return
        
        # Get recent events
        recent_events = self.events[-10:]  # Last 10 events
        
        # Detect cooperation patterns
        cooperation_events = [e for e in recent_events if e['action'] in ['transfer', 'connect', 'signal']]
        if len(cooperation_events) >= 3:
            self.add_pattern(
                name="Cooperation Emergence",
                description="Agents are beginning to work together through communication and resource sharing",
                confidence=0.7,
                discoverer="system"
            )
        
        # Detect exploration patterns
        exploration_events = [e for e in recent_events if e['action'] in ['observe', 'query', 'detect']]
        if len(exploration_events) >= 4:
            self.add_pattern(
                name="Information Gathering",
                description="Agents are actively exploring and learning about their environment",
                confidence=0.6,
                discoverer="system"
            )
        
        # Detect communication patterns
        comm_events = [e for e in recent_events if e['action'] in ['signal', 'receive']]
        if len(comm_events) >= 3:
            unique_actors = len(set(e['actor'] for e in comm_events))
            if unique_actors >= 2:
                self.add_pattern(
                    name="Communication Network",
                    description="Multiple agents are engaging in information exchange",
                    confidence=0.8,
                    discoverer="system"
                )
        
        # Detect tool diversity patterns
        unique_actions = len(set(e['action'] for e in recent_events))
        if unique_actions >= 5:
            self.add_pattern(
                name="Tool Diversity",
                description="Agents are using a wide variety of capabilities, indicating adaptive behavior",
                confidence=0.7,
                discoverer="system"
            )
