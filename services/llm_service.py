import os
import logging
import json
from datetime import datetime
import requests
import time

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM-based analysis using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "default-gemini-key")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.model_name = "gemini-pro"
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def analyze_segmentation(self, segmentation_data, analysis_request=""):
        """
        Analyze segmentation results using LLM
        
        Args:
            segmentation_data: Dictionary containing segmentation results
            analysis_request: Specific analysis request from user
        
        Returns:
            dict with analysis report and metadata
        """
        try:
            # Prepare context for LLM
            context = self._prepare_segmentation_context(segmentation_data)
            
            # Create prompt
            if analysis_request:
                prompt = f"""
                As a medical AI assistant, analyze the following medical image segmentation results and respond to this specific request: "{analysis_request}"

                Segmentation Results:
                {context}

                Please provide a detailed analysis addressing the specific request while considering the segmentation findings.
                """
            else:
                prompt = f"""
                As a medical AI assistant, provide a comprehensive analysis of the following medical image segmentation results:

                Segmentation Results:
                {context}

                Please provide:
                1. Summary of segmented organs/structures
                2. Notable findings or observations
                3. Potential clinical relevance
                4. Recommendations for further evaluation if needed

                Note: This is for educational/research purposes and should not replace professional medical diagnosis.
                """
            
            # Generate response using LLM
            response = self._call_gemini_api(prompt)
            
            if response['success']:
                return {
                    'success': True,
                    'report': response['text'],
                    'confidence': response.get('confidence', 0.8),
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model_name,
                    'prompt_tokens': response.get('prompt_tokens', 0),
                    'completion_tokens': response.get('completion_tokens', 0)
                }
            else:
                return {
                    'success': False,
                    'error': response['error'],
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in segmentation analysis: {str(e)}")
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def process_query(self, query, study=None, analysis=None):
        """
        Process natural language query about medical study
        
        Args:
            query: User's natural language query
            study: MedicalStudy object
            analysis: AnalysisResult object
        
        Returns:
            dict with LLM response and metadata
        """
        try:
            # Prepare context
            context = self._prepare_study_context(study, analysis)
            
            prompt = f"""
            As a medical AI assistant, answer the following question about this medical imaging study:

            Query: "{query}"

            Study Context:
            {context}

            Please provide a helpful and informative response. If the query cannot be answered based on the available information, clearly state what additional information would be needed.

            Note: This is for educational/research purposes and should not replace professional medical diagnosis.
            """
            
            # Generate response
            response = self._call_gemini_api(prompt)
            
            if response['success']:
                return {
                    'success': True,
                    'response': response['text'],
                    'confidence': response.get('confidence', 0.8),
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model_name
                }
            else:
                return {
                    'success': False,
                    'error': response['error'],
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'success': False,
                'error': f'Query processing failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_segmentation_context(self, segmentation_data):
        """Prepare segmentation data for LLM context"""
        try:
            if not segmentation_data:
                return "No segmentation data available."
            
            context_parts = []
            
            # Basic information
            if 'timestamp' in segmentation_data:
                context_parts.append(f"Analysis Date: {segmentation_data['timestamp']}")
            
            # Segmented organs
            if 'segmented_organs' in segmentation_data:
                organs = segmentation_data['segmented_organs']
                if organs:
                    context_parts.append(f"Segmented Organs/Structures ({len(organs)}): {', '.join(organs[:20])}")
                    if len(organs) > 20:
                        context_parts.append(f"... and {len(organs) - 20} more structures")
            
            # Summary statistics
            if 'summary' in segmentation_data:
                summary = segmentation_data['summary']
                context_parts.append(f"Total Structures Identified: {summary.get('total_organs', 0)}")
            
            # Processing information
            if segmentation_data.get('is_mock'):
                context_parts.append("Note: This is mock/demonstration data for development purposes.")
            
            return "\n".join(context_parts) if context_parts else "Limited segmentation information available."
            
        except Exception as e:
            logger.error(f"Error preparing segmentation context: {str(e)}")
            return "Error preparing segmentation context."
    
    def _prepare_study_context(self, study, analysis):
        """Prepare study and analysis data for LLM context"""
        try:
            context_parts = []
            
            if study:
                context_parts.append(f"Patient ID: {study.patient_id}")
                context_parts.append(f"Study ID: {study.study_id}")
                context_parts.append(f"Modality: {study.modality}")
                context_parts.append(f"Study Date: {study.study_date}")
                if study.description:
                    context_parts.append(f"Description: {study.description}")
                context_parts.append(f"Processing Status: {study.processing_status}")
            
            if analysis:
                context_parts.append(f"Analysis Type: {analysis.analysis_type}")
                context_parts.append(f"Analysis Status: {analysis.status}")
                if analysis.confidence_score:
                    context_parts.append(f"Confidence Score: {analysis.confidence_score:.2f}")
                if analysis.result_data:
                    # Add summary of analysis results
                    result_summary = self._summarize_analysis_results(analysis.result_data)
                    context_parts.append(f"Analysis Results: {result_summary}")
            
            return "\n".join(context_parts) if context_parts else "Limited study information available."
            
        except Exception as e:
            logger.error(f"Error preparing study context: {str(e)}")
            return "Error preparing study context."
    
    def _summarize_analysis_results(self, result_data):
        """Create a brief summary of analysis results"""
        try:
            if isinstance(result_data, dict):
                summary_parts = []
                
                if 'segmented_organs' in result_data:
                    organs = result_data['segmented_organs']
                    summary_parts.append(f"{len(organs)} structures segmented")
                
                if 'summary' in result_data:
                    summary = result_data['summary']
                    if 'total_organs' in summary:
                        summary_parts.append(f"Total organs: {summary['total_organs']}")
                
                return ", ".join(summary_parts) if summary_parts else "Analysis completed"
            else:
                return "Analysis data available"
                
        except Exception as e:
            return "Analysis summary unavailable"
    
    def _call_gemini_api(self, prompt):
        """
        Call Google Gemini API with retry logic
        
        Args:
            prompt: Text prompt for the LLM
        
        Returns:
            dict with success status and response
        """
        headers = {
            'Content-Type': 'application/json',
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                url = f"{self.api_url}?key={self.api_key}"
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'candidates' in result and len(result['candidates']) > 0:
                        candidate = result['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            text = candidate['content']['parts'][0].get('text', '')
                            
                            return {
                                'success': True,
                                'text': text,
                                'confidence': 0.8,  # Default confidence
                                'prompt_tokens': len(prompt.split()),
                                'completion_tokens': len(text.split())
                            }
                    
                    return {
                        'success': False,
                        'error': 'Invalid response format from Gemini API'
                    }
                
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                
                else:
                    error_msg = f"API error {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg
                    }
                    
            except requests.exceptions.Timeout:
                logger.warning(f"API timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        'success': False,
                        'error': 'API timeout after multiple retries'
                    }
            
            except Exception as e:
                logger.error(f"API call error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        'success': False,
                        'error': f'API call failed: {str(e)}'
                    }
        
        return {
            'success': False,
            'error': 'All API attempts failed'
        }
    
    def validate_api_key(self):
        """Validate that the Gemini API key is working"""
        try:
            test_prompt = "Hello, please respond with 'API test successful' if you can read this."
            response = self._call_gemini_api(test_prompt)
            
            return {
                'valid': response['success'],
                'error': response.get('error', '') if not response['success'] else None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'API validation failed: {str(e)}'
            }
