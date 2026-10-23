#!/usr/bin/env python3
"""
Real BAML Integration for AI Curation Engine
============================================

This module provides actual BAML integration with generated Python client.
Uses the real BoundaryML (BAML) functions for content classification.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging with BAML file logging
os.makedirs('logs', exist_ok=True)

# Setup BAML file logging
baml_file_handler = logging.FileHandler('logs/baml.log')
baml_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
baml_file_handler.setFormatter(baml_formatter)
baml_file_handler.setLevel(logging.DEBUG)

# Configure root logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add BAML loggers
baml_loggers = ['baml', 'baml_client', 'baml_py', 'BAML', 'BoundaryML']
for logger_name in baml_loggers:
    baml_logger = logging.getLogger(logger_name)
    baml_logger.addHandler(baml_file_handler)
    baml_logger.setLevel(logging.DEBUG)

logger.info("🔍 BAML logging configured - logs will be saved to logs/baml.log")

# Add the generated BAML client to Python path
baml_client_path = Path(__file__).parent.parent.parent / "src" / "core"
sys.path.insert(0, str(baml_client_path))

try:
    # Import the generated BAML client
    from baml_client import b, types
    from baml_client.types import (
        AgeCategory, Jurisdiction, ParentalControls, SensitivityLevel,
        VulnerabilityType, ScamType,
        UserContext, SafetyClassification, EducationalValue, 
        ViewpointAnalysis, ComprehensiveClassification, ScamDetection
    )
    import baml_py
    BAML_AVAILABLE = True
    logger.info("✅ Real BAML client imported successfully")
except (ImportError, Exception) as e:
    logger.error(f"❌ Failed to import BAML client: {e}")
    BAML_AVAILABLE = False
    # Create mock types for fallback
    class MockEnum:
        def __init__(self, value):
            self.value = value
        UNDER_13 = "UNDER_13"
        UNDER_16 = "UNDER_16"
        UNDER_18 = "UNDER_18"
        ADULT = "ADULT"
        US = "US"
        MODERATE = "MODERATE"
        MEDIUM = "MEDIUM"
    
    AgeCategory = MockEnum
    Jurisdiction = MockEnum
    ParentalControls = MockEnum
    SensitivityLevel = MockEnum
    
    # Mock UserContext
    class UserContext:
        def __init__(self, age_category, jurisdiction, parental_controls, sensitivity_level):
            self.age_category = age_category
            self.jurisdiction = jurisdiction
            self.parental_controls = parental_controls
            self.sensitivity_level = sensitivity_level


class RealBAMLContentAnalyzer:
    """
    Real BAML-powered content analyzer using generated client.
    Falls back to mock classification if BAML is unavailable.
    """
    
    def __init__(self):
        self.baml_available = BAML_AVAILABLE
        
        if self.baml_available:
            # Set up BAML Collector for logging
            self.collector = baml_py.baml_py.Collector("content-analyzer-collector")
            self.log_file = open('logs/baml-collector.log', 'a', encoding='utf-8')
            logger.info("🧠 RealBAMLContentAnalyzer initialized with actual BAML client")
            logger.info("📋 BAML Collector configured for detailed logging")
        else:
            self.collector = None
            self.log_file = None
            logger.warning("⚠️  RealBAMLContentAnalyzer falling back to mock mode")
    
    def __del__(self):
        """Clean up resources."""
        if self.log_file:
            self.log_file.close()
    
    def create_user_context(self, age: int = 16, jurisdiction: str = "US", 
                          parental_controls: str = "MODERATE", 
                          sensitivity: str = "MEDIUM") -> UserContext:
        """Create a UserContext object from parameters."""
        if not self.baml_available:
            return {
                'age_category': age,
                'jurisdiction': jurisdiction,
                'parental_controls': parental_controls,
                'sensitivity_level': sensitivity
            }
        
        # Map age to category
        if age < 13:
            age_category = AgeCategory.UNDER_13
        elif age < 16:
            age_category = AgeCategory.UNDER_16
        elif age < 18:
            age_category = AgeCategory.UNDER_18
        else:
            age_category = AgeCategory.ADULT
        
        # Map string values to enums
        jurisdiction_enum = getattr(Jurisdiction, jurisdiction.upper(), Jurisdiction.US)
        parental_enum = getattr(ParentalControls, parental_controls.upper(), ParentalControls.MODERATE)
        sensitivity_enum = getattr(SensitivityLevel, sensitivity.upper(), SensitivityLevel.MEDIUM)
        
        return UserContext(
            age_category=age_category,
            jurisdiction=jurisdiction_enum,
            parental_controls=parental_enum,
            sensitivity_level=sensitivity_enum
        )
    
    async def classify_safety(self, content: str, user_context: UserContext) -> Dict[str, Any]:
        """Classify content safety using real BAML ClassifySafety function."""
        if not self.baml_available:
            return self._mock_safety_classification(content, user_context)
        
        try:
            logger.info(f"🛡️  Classifying safety for content (length: {len(content)} chars)")
            result = await b.ClassifySafety(content=content, user_context=user_context)
            
            # Convert BAML result to dict for consistency
            return {
                'safety_score': result.safety_score,
                'violence_level': result.violence_level,
                'adult_content': result.adult_content,
                'hate_speech': result.hate_speech,
                'misinformation_risk': result.misinformation_risk,
                'age_appropriateness': result.age_appropriateness,
                'reasoning': result.reasoning,
                'content_warnings': result.content_warnings,
                'model': 'BAML-Real'
            }
            
        except Exception as e:
            logger.error(f"❌ Safety classification failed: {e}")
            return self._mock_safety_classification(content, user_context)
    
    async def classify_educational(self, content: str) -> Dict[str, Any]:
        """Classify educational value using real BAML ClassifyEducational function."""
        if not self.baml_available:
            return self._mock_educational_classification(content)
        
        try:
            logger.info(f"📚 Classifying educational value for content")
            result = await b.ClassifyEducational(content=content)
            
            return {
                'educational_score': result.educational_score,
                'learning_objectives': result.learning_objectives,
                'subject_areas': result.subject_areas,
                'cognitive_level': result.cognitive_level,
                'reading_level': result.reading_level,
                'factual_accuracy': result.factual_accuracy,
                'reasoning': result.reasoning,
                'model': 'BAML-Real'
            }
            
        except Exception as e:
            logger.error(f"❌ Educational classification failed: {e}")
            return self._mock_educational_classification(content)
    
    async def classify_viewpoint(self, content: str) -> Dict[str, Any]:
        """Classify viewpoint/bias using real BAML ClassifyViewpoint function."""
        if not self.baml_available:
            return self._mock_viewpoint_classification(content)
        
        try:
            logger.info(f"🏛️  Classifying viewpoint for content")
            result = await b.ClassifyViewpoint(content=content)
            
            return {
                'political_leaning': result.political_leaning,
                'bias_score': result.bias_score,
                'perspective_diversity': result.perspective_diversity,
                'controversy_level': result.controversy_level,
                'source_credibility': result.source_credibility,
                'reasoning': result.reasoning,
                'model': 'BAML-Real'
            }
            
        except Exception as e:
            logger.error(f"❌ Viewpoint classification failed: {e}")
            return self._mock_viewpoint_classification(content)
    
    async def comprehensive_analysis(self, content: str, user_context: UserContext) -> Dict[str, Any]:
        """Perform comprehensive analysis using real BAML ComprehensiveContentAnalysis function."""
        if not self.baml_available:
            return await self._mock_comprehensive_analysis(content, user_context)
        
        try:
            logger.info(f"🔍 Performing comprehensive analysis for content")
            
            # Call BAML function with collector for logging
            if self.collector:
                logger.info(f"🔍 Using BAML Collector: {self.collector.id}")
                result = await b.ComprehensiveContentAnalysis(
                    content=content, 
                    user_context=user_context,
                    baml_options={"collector": self.collector}
                )
                
                # Debug: Log collector state
                logger.info(f"📊 Collector after call - Last: {self.collector.last}, Logs count: {len(self.collector.logs)}")
                
                # Always write something to verify file access
                debug_entry = f"{datetime.now().isoformat()} - BAML Function Called\n"
                debug_entry += f"Content: {content[:50]}...\n"
                debug_entry += f"Collector ID: {self.collector.id}\n"
                debug_entry += f"Collector Last: {self.collector.last}\n"
                debug_entry += f"Logs Count: {len(self.collector.logs)}\n"
                debug_entry += "=" * 50 + "\n"
                self.log_file.write(debug_entry)
                self.log_file.flush()
                logger.info(f"📝 Debug log written to baml-collector.log")
                
                # Save collector logs to file if available
                if self.collector.last:
                    log_entry = f"{datetime.now().isoformat()} - BAML Function Call:\n"
                    log_entry += f"Function: ComprehensiveContentAnalysis\n"
                    log_entry += f"Content: {content[:100]}...\n"
                    log_entry += f"Collector ID: {self.collector.id}\n"
                    log_entry += "=" * 80 + "\n"
                    self.log_file.write(log_entry)
                    self.log_file.flush()
                    logger.info(f"📝 BAML logs saved to baml-collector.log")
                
                # Also log all collected logs
                if len(self.collector.logs) > 0:
                    for log_entry_item in self.collector.logs:
                        detailed_log = f"{datetime.now().isoformat()} - BAML Log Entry:\n"
                        detailed_log += f"Log: {log_entry_item}\n"
                        detailed_log += "-" * 40 + "\n"
                        self.log_file.write(detailed_log)
                    self.log_file.flush()
            else:
                logger.warning("⚠️ No collector available, calling BAML without collector")
                result = await b.ComprehensiveContentAnalysis(content=content, user_context=user_context)
            
            return {
                'safety': {
                    'score': result.safety.safety_score,
                    'age_appropriate': result.safety.age_appropriateness,
                    'warnings': result.safety.content_warnings,
                    'reasoning': result.safety.reasoning
                },
                'educational': {
                    'score': result.educational.educational_score,
                    'learning_objectives': result.educational.learning_objectives,
                    'subject_areas': result.educational.subject_areas,
                    'cognitive_level': result.educational.cognitive_level
                },
                'viewpoint': {
                    'political_leaning': result.viewpoint.political_leaning,
                    'bias_score': result.viewpoint.bias_score,
                    'credibility': result.viewpoint.source_credibility,
                    'reasoning': result.viewpoint.reasoning
                },
                'recommendation': result.recommendation,
                'confidence': result.overall_confidence,
                'summary': result.summary_reasoning,
                'model': 'BAML-Real'
            }
            
        except Exception as e:
            logger.error(f"❌ Comprehensive analysis failed: {e}")
            return await self._mock_comprehensive_analysis(content, user_context)
    
    # Mock fallback methods
    def _mock_safety_classification(self, content: str, user_context) -> Dict[str, Any]:
        """Mock safety classification when BAML unavailable."""
        import random
        
        content_lower = content.lower()
        violence_keywords = ['violence', 'fight', 'attack', 'kill', 'hurt', 'fighting']
        concerning_keywords = ['inappropriate', 'mature', 'concerning', 'scary']
        
        violence_score = min(0.9, sum(0.2 for word in violence_keywords if word in content_lower))
        has_concerning = any(word in content_lower for word in concerning_keywords)
        
        safety_score = max(0.1, 0.9 - violence_score - (0.3 if has_concerning else 0))
        
        warnings = []
        if violence_score > 0.2:
            warnings.append('violence')
        if has_concerning:
            warnings.append('mature themes')
        
        return {
            'safety_score': round(safety_score, 2),
            'violence_level': round(violence_score, 2),
            'adult_content': has_concerning,
            'hate_speech': round(random.uniform(0.0, 0.2), 2),
            'misinformation_risk': round(random.uniform(0.0, 0.3), 2),
            'age_appropriateness': '18+' if has_concerning else '13+' if violence_score > 0.2 else 'all',
            'reasoning': f'Mock analysis - BAML unavailable. Safety score: {safety_score:.2f}',
            'content_warnings': warnings,
            'model': 'Mock-Fallback'
        }
    
    def _mock_educational_classification(self, content: str) -> Dict[str, Any]:
        """Mock educational classification when BAML unavailable."""
        import random
        
        content_lower = content.lower()
        educational_keywords = ['learn', 'education', 'study', 'research', 'science', 'school']
        
        educational_score = min(0.95, 0.3 + sum(0.15 for word in educational_keywords if word in content_lower))
        
        return {
            'educational_score': round(educational_score, 2),
            'learning_objectives': ['understanding concepts'] if educational_score > 0.6 else [],
            'subject_areas': ['general knowledge'] if educational_score > 0.5 else [],
            'cognitive_level': 'understand' if educational_score > 0.7 else 'remember',
            'reading_level': random.randint(8, 12),
            'factual_accuracy': round(random.uniform(0.7, 0.95), 2),
            'reasoning': f'Mock analysis - BAML unavailable. Educational score: {educational_score:.2f}',
            'model': 'Mock-Fallback'
        }
    
    def _mock_viewpoint_classification(self, content: str) -> Dict[str, Any]:
        """Mock viewpoint classification when BAML unavailable."""
        import random
        
        return {
            'political_leaning': 'neutral',
            'bias_score': round(random.uniform(0.1, 0.4), 2),
            'perspective_diversity': round(random.uniform(0.5, 0.9), 2),
            'controversy_level': round(random.uniform(0.1, 0.5), 2),
            'source_credibility': round(random.uniform(0.6, 0.9), 2),
            'reasoning': 'Mock analysis - BAML unavailable. Neutral viewpoint assumed.',
            'model': 'Mock-Fallback'
        }
    
    async def _mock_comprehensive_analysis(self, content: str, user_context) -> Dict[str, Any]:
        """Mock comprehensive analysis when BAML unavailable."""
        safety = self._mock_safety_classification(content, user_context)
        educational = self._mock_educational_classification(content)
        viewpoint = self._mock_viewpoint_classification(content)
        
        # Determine recommendation
        if safety['safety_score'] < 0.6:
            recommendation = 'block'
        elif safety['safety_score'] < 0.8 or safety['content_warnings']:
            recommendation = 'caution'
        else:
            recommendation = 'allow'
        
        return {
            'safety': {
                'score': safety['safety_score'],
                'age_appropriate': safety['age_appropriateness'],
                'warnings': safety['content_warnings'],
                'reasoning': safety['reasoning']
            },
            'educational': {
                'score': educational['educational_score'],
                'learning_objectives': educational['learning_objectives'],
                'subject_areas': educational['subject_areas'],
                'cognitive_level': educational['cognitive_level']
            },
            'viewpoint': {
                'political_leaning': viewpoint['political_leaning'],
                'bias_score': viewpoint['bias_score'],
                'credibility': viewpoint['source_credibility'],
                'reasoning': viewpoint['reasoning']
            },
            'recommendation': recommendation,
            'confidence': round((safety['safety_score'] + educational['educational_score'] + (1 - viewpoint['bias_score'])) / 3, 2),
            'summary': f'Mock comprehensive analysis. Recommendation: {recommendation}',
            'model': 'Mock-Fallback'
        }


# Content Curation Pipeline with real BAML
class ContentCurationPipeline:
    """Main pipeline for content curation using real BAML classification."""
    
    def __init__(self):
        self.analyzer = RealBAMLContentAnalyzer()
        logger.info("🚀 ContentCurationPipeline initialized")
    
    async def curate_content(self, content: str, user_context: UserContext = None) -> Dict[str, Any]:
        """
        Main curation function that processes content and returns classification results.
        
        Args:
            content: Text content to analyze
            user_context: User context for personalized analysis
            
        Returns:
            Dict containing classification results and recommendation
        """
        import time
        start_time = time.time()
        
        if user_context is None:
            user_context = self.analyzer.create_user_context()
        
        try:
            # Perform comprehensive analysis
            result = await self.analyzer.comprehensive_analysis(content, user_context)
            
            # Add processing metadata
            processing_time = time.time() - start_time
            result['processing_time'] = round(processing_time, 2)
            result['timestamp'] = time.time()
            result['content_length'] = len(content)
            
            logger.info(f"✅ Content curation completed in {processing_time:.2f}s - Recommendation: {result.get('recommendation', 'unknown')}")
            
            return {
                'status': 'success',
                'classification': result,
                'recommendation': {
                    'action': result.get('recommendation', 'allow'),
                    'confidence': result.get('confidence', 0.8),
                    'reasoning': result.get('summary', 'Content analysis completed')
                },
                'processing_time_seconds': processing_time
            }
            
        except Exception as e:
            logger.error(f"❌ Content curation failed: {e}")
            processing_time = time.time() - start_time
            
            return {
                'status': 'error',
                'error': str(e),
                'processing_time_seconds': processing_time,
                'classification': None,
                'recommendation': {
                    'action': 'block',
                    'confidence': 0.0,
                    'reasoning': f'Analysis failed: {str(e)}'
                }
            }


# Example usage and testing
async def main():
    """Example usage of the real BAML integration."""
    print("🧪 Testing Real BAML Integration")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = ContentCurationPipeline()
    
    # Test content samples
    test_cases = [
        {
            'content': 'This is a story about a friendly cat playing with a ball of yarn. It teaches children about kindness and friendship.',
            'age': 8,
            'description': 'Child-friendly educational content'
        },
        {
            'content': 'Just had the best day at the beach with friends! 🏖️ The weather was perfect and we played volleyball for hours.',
            'age': 14,
            'description': 'Teen social media post'
        },
        {
            'content': 'This content contains discussions about violence and inappropriate themes that would not be suitable for younger audiences.',
            'age': 8,
            'description': 'Concerning content for children'
        },
        {
            'content': 'Scientists have developed a new artificial intelligence system that can help doctors diagnose diseases more accurately.',
            'age': 16,
            'description': 'Educational technology news'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['description']}")
        print(f"Content: '{test_case['content'][:60]}...'")
        print(f"Child Age: {test_case['age']} years")
        
        # Create user context
        analyzer = RealBAMLContentAnalyzer()
        user_context = analyzer.create_user_context(age=test_case['age'])
        
        # Analyze content
        result = await pipeline.curate_content(test_case['content'], user_context)
        
        # Display results
        if result['status'] == 'success':
            classification = result['classification']
            recommendation = result['recommendation']
            
            print(f"📊 Results:")
            print(f"   • Safety Score: {classification['safety']['score']:.2f}")
            print(f"   • Educational Score: {classification['educational']['score']:.2f}")
            print(f"   • Recommendation: {recommendation['action'].upper()}")
            print(f"   • Confidence: {recommendation['confidence']:.2f}")
            print(f"   • Processing Time: {result['processing_time_seconds']:.2f}s")
            print(f"   • Model: {classification.get('model', 'Unknown')}")
            
            if classification['safety']['warnings']:
                print(f"   • Warnings: {', '.join(classification['safety']['warnings'])}")
                
        else:
            print(f"❌ Error: {result['error']}")
        
        print("-" * 50)
    
    print(f"\n✅ Real BAML Integration Test Complete!")
    print(f"🧠 BAML Available: {pipeline.analyzer.baml_available}")


if __name__ == "__main__":
    # Set up environment variables for testing (optional)
    os.environ.setdefault('OPENAI_API_KEY', 'your-openai-key-here')
    os.environ.setdefault('ANTHROPIC_API_KEY', 'your-anthropic-key-here')
    
    # Run the test
    asyncio.run(main())
