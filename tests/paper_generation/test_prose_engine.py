"""
Unit tests for ProseEngine.

Tests ProseEngine implementation with mocked OpenAI API calls.
Validates prompt generation, retry logic, word count validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path

from src.paper_generation.prose_engine import ProseEngine
from src.paper_generation.models import PaperConfig, SectionContext
from src.paper_generation.exceptions import ProseGenerationError


@pytest.fixture
def paper_config(tmp_path):
    """Create PaperConfig for testing."""
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    (exp_dir / "analysis").mkdir()
    
    return PaperConfig(
        experiment_dir=exp_dir,
        output_dir=tmp_path / "output",
        openai_api_key="test-api-key-12345",
        model="gpt-3.5-turbo",
        temperature=0.7
    )


@pytest.fixture
def section_context():
    """Create SectionContext for testing."""
    return SectionContext(
        section_name="methodology",
        experiment_summary="Comparison of ChatDev, MetaGPT, and AutoGen frameworks",
        frameworks=["ChatDev", "MetaGPT", "AutoGen"],
        task_description="Implement a simple web application",
        metrics={"efficiency": {"mean": 120.5, "std": 15.2}},
        statistical_results={"kruskal_wallis_p": 0.023},
        key_findings=["Framework A outperformed others", "Statistical significance found"],
        min_words=800,
        prose_level="standard"
    )


class TestProseEngineInitialization:
    """Test ProseEngine initialization and configuration."""
    
    def test_initialization_with_config_api_key(self, paper_config):
        """Test initialization uses API key from config."""
        engine = ProseEngine(paper_config)
        assert engine.api_key == "test-api-key-12345"
        assert engine.model == "gpt-3.5-turbo"
        assert engine.temperature == 0.7
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-api-key-67890'})
    def test_initialization_with_env_api_key(self, tmp_path):
        """Test initialization uses API key from environment if config key is None."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        config = PaperConfig(
            experiment_dir=exp_dir,
            output_dir=tmp_path / "output"
        )
        
        engine = ProseEngine(config)
        assert engine.api_key == 'env-api-key-67890'
    
    def test_initialization_without_api_key_raises_error(self, tmp_path):
        """Test initialization without API key raises error."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        config = PaperConfig(
            experiment_dir=exp_dir,
            output_dir=tmp_path / "output"
        )
        
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ProseGenerationError, match="OpenAI API key not found"):
                ProseEngine(config)


class TestProseEnginePromptGeneration:
    """Test prompt generation for different contexts."""
    
    def test_build_prompt_includes_section_name(self, paper_config, section_context):
        """Test prompt includes section name."""
        engine = ProseEngine(paper_config)
        prompt = engine._build_prompt(section_context)
        
        assert "methodology" in prompt.lower()
    
    def test_build_prompt_includes_experiment_summary(self, paper_config, section_context):
        """Test prompt includes experiment summary."""
        engine = ProseEngine(paper_config)
        prompt = engine._build_prompt(section_context)
        
        assert "ChatDev" in prompt
        assert "MetaGPT" in prompt
        assert "AutoGen" in prompt
    
    def test_build_prompt_includes_min_words_requirement(self, paper_config, section_context):
        """Test prompt requests minimum word count."""
        engine = ProseEngine(paper_config)
        prompt = engine._build_prompt(section_context)
        
        assert "800" in prompt or "at least" in prompt.lower()
    
    def test_build_prompt_includes_frameworks_list(self, paper_config, section_context):
        """Test prompt includes frameworks being compared."""
        engine = ProseEngine(paper_config)
        prompt = engine._build_prompt(section_context)
        
        for framework in section_context.frameworks:
            assert framework in prompt
    
    def test_build_prompt_for_different_prose_levels(self, paper_config):
        """Test prompt differs based on prose_level."""
        engine = ProseEngine(paper_config)
        
        context_minimal = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["A", "B"],
            task_description="Test task",
            min_words=800,
            prose_level="minimal"
        )
        
        context_comprehensive = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["A", "B"],
            task_description="Test task",
            min_words=800,
            prose_level="comprehensive"
        )
        
        prompt_minimal = engine._build_prompt(context_minimal)
        prompt_comprehensive = engine._build_prompt(context_comprehensive)
        
        # Prompts should be different for different prose levels
        assert prompt_minimal != prompt_comprehensive


class TestProseEngineAPIInteraction:
    """Test OpenAI API interaction."""
    
    @patch('requests.post')
    def test_call_openai_api_success(self, mock_post, paper_config):
        """Test successful API call returns prose and token count."""
        engine = ProseEngine(paper_config)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': 'Generated prose content here'}}
            ],
            'usage': {'total_tokens': 500}
        }
        mock_post.return_value = mock_response
        
        prose, tokens = engine._call_openai_api("Test prompt")
        
        assert prose == 'Generated prose content here'
        assert tokens == 500
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://api.openai.com/v1/chat/completions'
        assert call_args[1]['headers']['Authorization'] == 'Bearer test-api-key-12345'
    
    @patch('requests.post')
    def test_call_openai_api_sends_correct_payload(self, mock_post, paper_config):
        """Test API call sends correct model and temperature."""
        engine = ProseEngine(paper_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'test'}}],
            'usage': {'total_tokens': 100}
        }
        mock_post.return_value = mock_response
        
        engine._call_openai_api("Test prompt")
        
        call_kwargs = mock_post.call_args[1]
        payload = json.loads(call_kwargs['data'])
        
        assert payload['model'] == 'gpt-3.5-turbo'
        assert payload['temperature'] == 0.7
        assert len(payload['messages']) >= 1
    
    @patch('requests.post')
    def test_call_openai_api_http_error(self, mock_post, paper_config):
        """Test API call handles HTTP errors."""
        engine = ProseEngine(paper_config)
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        with pytest.raises(ProseGenerationError, match="API request failed"):
            engine._call_openai_api("Test prompt")
    
    @patch('requests.post')
    def test_call_openai_api_network_error(self, mock_post, paper_config):
        """Test API call handles network errors."""
        engine = ProseEngine(paper_config)
        
        mock_post.side_effect = Exception("Network timeout")
        
        with pytest.raises(ProseGenerationError):
            engine._call_openai_api("Test prompt")


class TestProseEngineRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @patch('requests.post')
    @patch('time.sleep')
    def test_retry_on_rate_limit(self, mock_sleep, mock_post, paper_config, section_context):
        """Test retry on rate limit (HTTP 429)."""
        engine = ProseEngine(paper_config)
        
        # First call: rate limit, second call: success
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.text = "Rate limit exceeded"
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'choices': [{'message': {'content': 'Success after retry ' * 200}}],  # >800 words
            'usage': {'total_tokens': 500}
        }
        
        mock_post.side_effect = [mock_response_429, mock_response_success]
        
        prose = engine.generate_prose(section_context, max_retries=3)
        
        # Should have retried once
        assert mock_post.call_count == 2
        assert mock_sleep.call_count == 1
        assert "Success after retry" in prose
    
    @patch('requests.post')
    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_post, paper_config, section_context):
        """Test exponential backoff delays (2^attempt seconds)."""
        engine = ProseEngine(paper_config)
        
        # Fail twice, then succeed
        mock_response_error = Mock()
        mock_response_error.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'choices': [{'message': {'content': 'Success ' * 200}}],
            'usage': {'total_tokens': 500}
        }
        
        mock_post.side_effect = [
            mock_response_error,
            mock_response_error,
            mock_response_success
        ]
        
        engine.generate_prose(section_context, max_retries=3)
        
        # Should have slept with exponential backoff: 2^1=2s, 2^2=4s
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [2, 4]
    
    @patch('requests.post')
    @patch('time.sleep')
    def test_fails_after_max_retries(self, mock_sleep, mock_post, paper_config, section_context):
        """Test fails after exceeding max retries."""
        engine = ProseEngine(paper_config)
        
        # Always fail
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        with pytest.raises(ProseGenerationError, match="Failed after 3 retries"):
            engine.generate_prose(section_context, max_retries=3)
        
        # Should have tried 3 times
        assert mock_post.call_count == 3


class TestProseEngineWordCountValidation:
    """Test word count validation."""
    
    def test_validate_prose_sufficient_words(self, paper_config):
        """Test validation passes for sufficient word count."""
        engine = ProseEngine(paper_config)
        
        prose = "word " * 850  # 850 words
        word_count = engine._validate_prose(prose, min_words=800)
        
        assert word_count >= 800
    
    def test_validate_prose_insufficient_words_raises_error(self, paper_config):
        """Test validation fails for insufficient word count."""
        engine = ProseEngine(paper_config)
        
        prose = "word " * 700  # 700 words
        
        with pytest.raises(ProseGenerationError, match="Generated prose.*700.*800"):
            engine._validate_prose(prose, min_words=800)
    
    @patch('requests.post')
    def test_generate_prose_validates_word_count(self, mock_post, paper_config, section_context):
        """Test generate_prose validates word count of API response."""
        engine = ProseEngine(paper_config)
        
        # Return insufficient words
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Too short'}}],
            'usage': {'total_tokens': 50}
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(ProseGenerationError, match="insufficient.*words"):
            engine.generate_prose(section_context, max_retries=1)


class TestProseEngineAIMarkers:
    """Test AI-generated content markers."""
    
    @patch('requests.post')
    def test_generate_prose_includes_ai_markers(self, mock_post, paper_config, section_context):
        """Test generated prose includes AI markers."""
        engine = ProseEngine(paper_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Generated content here. ' * 200}}],
            'usage': {'total_tokens': 500}
        }
        mock_post.return_value = mock_response
        
        prose = engine.generate_prose(section_context)
        
        # Should include AI markers in LaTeX comment format
        assert "AI-GENERATED" in prose or "AI GENERATED" in prose
