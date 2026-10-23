#!/usr/bin/env python3
"""
Pluggable Curation Engine Architecture

This module provides a flexible, strategy-based curation engine that allows
switching between different classification approaches:

1. LLM-Only Strategy (current implementation) - for AI demos and complex reasoning
2. Multi-Layer Strategy (production) - for performance and reliability
3. Hybrid Strategy - combines both approaches

Usage:
    # LLM-only for demos
    engine = CurationEngine(strategy="llm_only")
    
    # Production multi-layer
    engine = CurationEngine(strategy="multi_layer")
    
    # Hybrid approach
    engine = CurationEngine(strategy="hybrid")
"""

import asyncio
import time
import hashlib
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Import existing BAML integration
try:
    from BAML_Integration_Real import RealBAMLContentAnalyzer, UserContext
    BAML_AVAILABLE = True
except (ImportError, NameError, Exception) as e:
    logger.warning(f"BAML not available: {e}")
    BAML_AVAILABLE = False
    # Create mock UserContext
    class UserContext:
        def __init__(self, age_category, jurisdiction=None, parental_controls=None, sensitivity_level=None):
            self.age_category = age_category
            self.jurisdiction = jurisdiction
            self.parental_controls = parental_controls
            self.sensitivity_level = sensitivity_level
    # Mock RealBAMLContentAnalyzer for fallback
    class RealBAMLContentAnalyzer:
        def __init__(self):
            pass

class CurationStrategy(Enum):
    """Available curation strategies"""
    LLM_ONLY = "llm_only"
    MULTI_LAYER = "multi_layer"
    HYBRID = "hybrid"

@dataclass
class CurationResult:
    """Standardized result from any curation strategy"""
    action: str  # "allow", "block", "caution", "review"
    reason: str
    confidence: float
    safety_score: float
    processing_time_ms: int
    strategy_used: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "action": self.action,
            "reason": self.reason,
            "confidence": self.confidence,
            "safety_score": self.safety_score,
            "processing_time_ms": self.processing_time_ms,
            "strategy_used": self.strategy_used
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result

class CurationStrategyBase(ABC):
    """Abstract base class for all curation strategies"""
    
    @abstractmethod
    async def analyze_content(self, content: str, user_context: UserContext) -> CurationResult:
        """Analyze content and return curation decision"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of this strategy"""
        pass

class LLMOnlyStrategy(CurationStrategyBase):
    """Current LLM-only implementation for AI demos and complex reasoning"""
    
    def __init__(self):
        if BAML_AVAILABLE:
            self.analyzer = RealBAMLContentAnalyzer()
            logger.info("🧠 LLM-Only Strategy initialized with BAML")
        else:
            self.analyzer = None
            logger.error("❌ LLM-Only Strategy: BAML not available - strategy will fail")
    
    async def analyze_content(self, content: str, user_context: UserContext) -> CurationResult:
        start_time = time.time()
        
        try:
            if self.analyzer:
                # Use real BAML analysis
                result = await self.analyzer.comprehensive_analysis(content, user_context)
                
                # Extract key metrics
                safety_score = result.get('safety', {}).get('safety_score', 0.5)
                recommendation = result.get('recommendation', 'caution')
                confidence = result.get('overall_confidence', 0.7)
                reasoning = result.get('summary_reasoning', 'LLM analysis completed')
                
                return CurationResult(
                    action=recommendation,
                    reason=reasoning,
                    confidence=confidence,
                    safety_score=safety_score,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    strategy_used="llm_only",
                    metadata={
                        "full_analysis": result,
                        "baml_used": True
                    }
                )
            else:
                # BAML not available - fail gracefully
                raise ValueError("LLM-Only Strategy requires BAML but it's not available")
                
        except Exception as e:
            logger.error(f"❌ LLM-Only Strategy failed: {e}")
            raise
    
    
    def get_strategy_name(self) -> str:
        return "LLM-Only Strategy"

class FastFilterLayer:
    """Layer 1: Fast rule-based filters"""
    
    def __init__(self):
        # Common profanity and harmful patterns
        self.profanity_patterns = [
            r'\b(fuck|shit|damn|bitch)\b',
            r'\b(kill|murder|die)\s+(you|yourself|them)\b',
            r'\b(hate|kill)\s+all\s+\w+\b'
        ]
        
        # Harmful URL patterns
        self.harmful_url_patterns = [
            r'bit\.ly/[0-9a-zA-Z]+',  # Suspicious short links
            r'pornhub\.com',
            r'xxx\.',
            r'\.onion',  # Dark web
        ]
        
        # Compile regex patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.profanity_patterns]
        self.compiled_url_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.harmful_url_patterns]
    
    def check(self, content: str) -> Optional[CurationResult]:
        """Return blocking result if content violates fast filters, None otherwise"""
        start_time = time.time()
        
        # Check profanity patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return CurationResult(
                    action="block",
                    reason="Profanity or harmful language detected",
                    confidence=0.95,
                    safety_score=0.1,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    strategy_used="fast_filter",
                    metadata={"filter_type": "profanity"}
                )
        
        # Check harmful URLs
        for pattern in self.compiled_url_patterns:
            if pattern.search(content):
                return CurationResult(
                    action="block",
                    reason="Harmful URL detected",
                    confidence=0.9,
                    safety_score=0.05,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    strategy_used="fast_filter",
                    metadata={"filter_type": "harmful_url"}
                )
        
        return None  # Passed fast filters

class SpecializedAILayer:
    """Layer 2: Specialized AI models (mock implementation)"""
    
    def __init__(self):
        # In production, these would be real API clients
        self.toxicity_threshold = 0.7
        self.nsfw_threshold = 0.8
        
    async def analyze(self, content: str) -> Optional[CurationResult]:
        """Return blocking result if specialized AI detects issues, None otherwise"""
        start_time = time.time()
        
        # Toxicity detection (placeholder implementation)
        toxicity_score = await self._mock_toxicity_analysis(content)
        if toxicity_score > self.toxicity_threshold:
            return CurationResult(
                action="block",
                reason=f"High toxicity detected (score: {toxicity_score:.2f})",
                confidence=0.85,
                safety_score=1.0 - toxicity_score,
                processing_time_ms=int((time.time() - start_time) * 1000),
                strategy_used="specialized_ai",
                metadata={"ai_type": "toxicity", "toxicity_score": toxicity_score}
            )
        
        # NSFW detection (placeholder implementation)  
        nsfw_score = await self._mock_nsfw_analysis(content)
        if nsfw_score > self.nsfw_threshold:
            return CurationResult(
                action="block",
                reason=f"NSFW content detected (score: {nsfw_score:.2f})",
                confidence=0.9,
                safety_score=1.0 - nsfw_score,
                processing_time_ms=int((time.time() - start_time) * 1000),
                strategy_used="specialized_ai",
                metadata={"ai_type": "nsfw", "nsfw_score": nsfw_score}
            )
        
        return None  # Passed specialized AI checks
    
    async def _mock_toxicity_analysis(self, content: str) -> float:
        """Placeholder for Perspective API integration - replace with real toxicity detection"""
        # Simple heuristic for demo
        toxic_words = ['hate', 'kill', 'stupid', 'idiot', 'moron', 'threat']
        score = sum(1 for word in toxic_words if word in content.lower()) * 0.2
        return min(score, 1.0)
    
    async def _mock_nsfw_analysis(self, content: str) -> float:
        """Placeholder for NSFW detection service - replace with real content analysis"""
        nsfw_words = ['sex', 'porn', 'naked', 'adult', 'explicit']
        score = sum(1 for word in nsfw_words if word in content.lower()) * 0.25
        return min(score, 1.0)

class MultiLayerStrategy(CurationStrategyBase):
    """Production multi-layer strategy with performance optimization"""
    
    def __init__(self, cache_ttl: int = 3600):
        self.fast_filter = FastFilterLayer()
        self.specialized_ai = SpecializedAILayer()
        self.llm_strategy = LLMOnlyStrategy() if BAML_AVAILABLE else None
        self.cache = {}  # Enhanced in-memory cache with timestamps
        self.cache_ttl = cache_ttl  # Cache time-to-live in seconds
        logger.info("🏭 Multi-Layer Strategy initialized with caching (TTL: {}s)".format(cache_ttl))
    
    async def analyze_content(self, content: str, user_context: UserContext) -> CurationResult:
        start_time = time.time()
        
        # Check cache first with TTL validation
        cache_key = hashlib.md5(f"{content}{user_context.age_category}".encode()).hexdigest()
        if cache_key in self.cache:
            cached_entry = self.cache[cache_key]
            cache_age = time.time() - cached_entry['timestamp']
            
            # Return cached result if still valid
            if cache_age < self.cache_ttl:
                cached_result = cached_entry['result']
                # Create a new result object to avoid modifying the cached one
                result = CurationResult(
                    action=cached_result.action,
                    reason=cached_result.reason,
                    confidence=cached_result.confidence,
                    safety_score=cached_result.safety_score,
                    processing_time_ms=1,  # Cache hit is very fast
                    strategy_used=cached_result.strategy_used,
                    metadata={
                        **(cached_result.metadata or {}),
                        "cache_hit": True,
                        "cache_age_seconds": int(cache_age)
                    }
                )
                logger.info(f"⚡ Multi-layer: Cache hit (age: {int(cache_age)}s)")
                return result
            else:
                # Cache expired, remove it
                del self.cache[cache_key]
                logger.info(f"🕐 Multi-layer: Cache expired for key (age: {int(cache_age)}s)")
        
        # Layer 1: Fast filters (should be <5ms)
        fast_result = self.fast_filter.check(content)
        if fast_result:
            logger.info(f"🚫 Multi-layer: Blocked by fast filter - {fast_result.reason}")
            self._cache_result(cache_key, fast_result)
            return fast_result
        
        # Layer 2: Specialized AI (should be <1s)
        specialized_result = await self.specialized_ai.analyze(content)
        if specialized_result:
            logger.info(f"🚫 Multi-layer: Blocked by specialized AI - {specialized_result.reason}")
            self._cache_result(cache_key, specialized_result)
            return specialized_result
        
        # Layer 3: LLM for complex cases (only if needed)
        if self._requires_llm_analysis(content, user_context):
            if self.llm_strategy:
                logger.info("🧠 Multi-layer: Using LLM for complex analysis")
                try:
                    llm_result = await self.llm_strategy.analyze_content(content, user_context)
                    llm_result.strategy_used = "multi_layer_llm"
                    self._cache_result(cache_key, llm_result)
                    return llm_result
                except Exception as e:
                    # LLM failed - fallback to cautious recommendation
                    logger.error(f"❌ Multi-layer: LLM analysis failed - {e}")
                    result = CurationResult(
                        action="caution",
                        reason=f"LLM analysis encountered an error: {str(e)[:100]}",
                        confidence=0.5,
                        safety_score=0.6,
                        processing_time_ms=int((time.time() - start_time) * 1000),
                        strategy_used="multi_layer_llm_fallback",
                        metadata={"error": str(e), "fallback": True}
                    )
                    self._cache_result(cache_key, result)
                    return result
            else:
                # LLM needed but not available - use caution
                logger.warning("⚠️ Multi-layer: LLM analysis needed but BAML not available")
                result = CurationResult(
                    action="caution",
                    reason="Complex content requires LLM analysis but BAML is not available",
                    confidence=0.5,
                    safety_score=0.6,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    strategy_used="multi_layer_cautious",
                    metadata={"baml_required": True, "baml_available": False, "engine_strategy": "multi_layer"}
                )
                self._cache_result(cache_key, result)
                return result
        
        # Default: Allow content that passed all checks
        result = CurationResult(
            action="allow",
            reason="Passed all automated checks",
            confidence=0.8,
            safety_score=0.9,
            processing_time_ms=int((time.time() - start_time) * 1000),
            strategy_used="multi_layer_auto",
            metadata={"layers_passed": ["fast_filter", "specialized_ai"]}
        )
        
        self._cache_result(cache_key, result)
        logger.info("✅ Multi-layer: Content allowed")
        return result
    
    def _cache_result(self, cache_key: str, result: CurationResult):
        """Store result in cache with timestamp for TTL management"""
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        
        # Periodically clean expired entries (every 100 additions)
        if len(self.cache) % 100 == 0:
            self._clean_expired_cache()
    
    def _clean_expired_cache(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry['timestamp'] > self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.info(f"🧹 Multi-layer: Cleaned {len(expired_keys)} expired cache entries")
    
    def _requires_llm_analysis(self, content: str, user_context: UserContext) -> bool:
        """Determine if content needs complex LLM reasoning"""
        # Use LLM for complex cases
        complex_indicators = [
            len(content) > 500,  # Long content
            user_context.age_category in ['UNDER_13', 'UNDER_16'],  # Young users
            any(word in content.lower() for word in ['political', 'controversial', 'opinion', 'debate']),
            content.count('?') > 2,  # Many questions (might need context)
        ]
        
        return any(complex_indicators)
    
    def get_strategy_name(self) -> str:
        return "Multi-Layer Strategy"

class HybridStrategy(CurationStrategyBase):
    """Hybrid strategy that intelligently chooses between approaches"""
    
    def __init__(self):
        self.multi_layer = MultiLayerStrategy()
        self.llm_only = LLMOnlyStrategy()
        logger.info("🔄 Hybrid Strategy initialized")
    
    async def analyze_content(self, content: str, user_context: UserContext) -> CurationResult:
        # For demo purposes or complex reasoning needs, use LLM-only
        if self._should_use_llm_only(content, user_context):
            logger.info("🧠 Hybrid: Using LLM-only for this content")
            result = await self.llm_only.analyze_content(content, user_context)
            result.strategy_used = "hybrid_llm"
            return result
        
        # Otherwise, use efficient multi-layer approach
        logger.info("🏭 Hybrid: Using multi-layer for this content")
        result = await self.multi_layer.analyze_content(content, user_context)
        result.strategy_used = "hybrid_multi"
        return result
    
    def _should_use_llm_only(self, content: str, user_context: UserContext) -> bool:
        """Decide whether to use LLM-only based on content characteristics"""
        llm_indicators = [
            # Use LLM for demonstration purposes
            "demo" in content.lower() or "test" in content.lower(),
            
            # Use LLM for nuanced content
            any(word in content.lower() for word in [
                'cultural', 'religious', 'philosophical', 'ethical',
                'moral', 'values', 'belief', 'opinion', 'perspective'
            ]),
            
            # Use LLM for educational assessment
            any(word in content.lower() for word in [
                'learn', 'education', 'teaching', 'academic',
                'study', 'research', 'knowledge'
            ]),
            
            # Use LLM for complex political content
            len([word for word in ['political', 'government', 'policy', 'election'] 
                 if word in content.lower()]) > 1,
        ]
        
        return any(llm_indicators)
    
    def get_strategy_name(self) -> str:
        return "Hybrid Strategy"

class CurationEngine:
    """Main curation engine with pluggable strategies"""
    
    def __init__(self, strategy: Union[str, CurationStrategy] = CurationStrategy.HYBRID):
        """
        Initialize curation engine with specified strategy
        
        Args:
            strategy: Strategy to use ("llm_only", "multi_layer", "hybrid" or CurationStrategy enum)
        """
        if isinstance(strategy, str):
            strategy = CurationStrategy(strategy)
        
        self.strategy_type = strategy
        self.strategy = self._create_strategy(strategy)
        
        logger.info(f"🚀 CurationEngine initialized with {self.strategy.get_strategy_name()}")
    
    def _create_strategy(self, strategy: CurationStrategy) -> CurationStrategyBase:
        """Factory method to create strategy instances"""
        if strategy == CurationStrategy.LLM_ONLY:
            return LLMOnlyStrategy()
        elif strategy == CurationStrategy.MULTI_LAYER:
            return MultiLayerStrategy()
        elif strategy == CurationStrategy.HYBRID:
            return HybridStrategy()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    async def curate_content(self, content: str, user_context: UserContext) -> CurationResult:
        """
        Curate content using the configured strategy
        
        Args:
            content: Content to analyze
            user_context: User context for personalization
            
        Returns:
            CurationResult with decision and metadata
        """
        start_time = time.time()
        
        try:
            result = await self.strategy.analyze_content(content, user_context)
            
            # Add engine metadata
            result.metadata = result.metadata or {}
            result.metadata.update({
                "engine_strategy": self.strategy_type.value,
                "total_processing_time_ms": int((time.time() - start_time) * 1000)
            })
            
            logger.info(f"✅ Curation completed: {result.action} ({result.confidence:.2f} confidence)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Curation engine error: {e}")
            
            # Error handling - return cautious result
            return CurationResult(
                action="caution",
                reason=f"Engine error: {str(e)}",
                confidence=0.0,
                safety_score=0.5,
                processing_time_ms=int((time.time() - start_time) * 1000),
                strategy_used="error_handling",
                metadata={"error": str(e)}
            )
    
    def switch_strategy(self, new_strategy: Union[str, CurationStrategy]):
        """Switch to a different curation strategy at runtime"""
        if isinstance(new_strategy, str):
            new_strategy = CurationStrategy(new_strategy)
        
        old_strategy = self.strategy_type
        self.strategy_type = new_strategy
        self.strategy = self._create_strategy(new_strategy)
        
        logger.info(f"🔄 Strategy switched from {old_strategy.value} to {new_strategy.value}")
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about the current strategy"""
        return {
            "strategy_type": self.strategy_type.value,
            "strategy_name": self.strategy.get_strategy_name(),
            "baml_available": BAML_AVAILABLE
        }

# Demo function to show pluggable architecture
async def demo_pluggable_curation():
    """Demonstrate the pluggable curation engine"""
    
    # Sample content and user context
    test_content = "AI helps doctors diagnose diseases faster"
    
    # Import UserContext and enums from BAML client
    if BAML_AVAILABLE:
        from BAML_Integration_Real import UserContext, AgeCategory, Jurisdiction, ParentalControls, SensitivityLevel
        user_context = UserContext(
            age_category=AgeCategory.UNDER_18,
            jurisdiction=Jurisdiction.US,
            parental_controls=ParentalControls.MODERATE,
            content_preferences=['educational'],
            sensitivity_level=SensitivityLevel.MEDIUM
        )
    else:
        # Create a mock user context for demo
        user_context = {
            'age_category': 'UNDER_18',
            'jurisdiction': 'US',
            'parental_controls': 'MODERATE',
            'content_preferences': ['educational'],
            'sensitivity_level': 'MEDIUM'
        }
    
    print("🎯 Pluggable Curation Engine Demo")
    print("=" * 50)
    
    # Test all strategies
    strategies = [
        CurationStrategy.LLM_ONLY,
        CurationStrategy.MULTI_LAYER,
        CurationStrategy.HYBRID
    ]
    
    for strategy in strategies:
        print(f"\n📋 Testing {strategy.value} strategy:")
        print("-" * 30)
        
        engine = CurationEngine(strategy=strategy)
        result = await engine.curate_content(test_content, user_context)
        
        print(f"Action: {result.action}")
        print(f"Reason: {result.reason}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Safety Score: {result.safety_score:.2f}")
        print(f"Processing Time: {result.processing_time_ms}ms")
        print(f"Strategy Used: {result.strategy_used}")
        
        if result.metadata:
            print(f"Metadata: {json.dumps(result.metadata, indent=2)}")
    
    print("\n🔄 Testing Strategy Switching:")
    print("-" * 30)
    
    # Demo runtime strategy switching
    engine = CurationEngine(strategy=CurationStrategy.LLM_ONLY)
    print(f"Initial: {engine.get_strategy_info()}")
    
    engine.switch_strategy(CurationStrategy.MULTI_LAYER)
    print(f"Switched: {engine.get_strategy_info()}")

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_pluggable_curation())
