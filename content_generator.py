import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentGenerator:
    """OpenAI API wrapper for generating programming content"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the content generator

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for generation (default: gpt-4o-mini for cost efficiency)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def generate_ideas(self, count: int = 10, category: str = "programming") -> List[Dict[str, str]]:
        """
        Generate a list of programming topic ideas

        Args:
            count: Number of ideas to generate
            category: Category of programming topics (e.g., "web development", "data structures")

        Returns:
            List of dictionaries with 'topic' and 'description' keys
        """
        logger.info(f"Generating {count} {category} topic ideas...")

        prompt = f"""Generate {count} unique and interesting programming topics for educational content.
        Focus on: {category}

        For each topic, provide:
        1. A concise topic title (3-8 words)
        2. A brief description (1-2 sentences)

        Return the response as a JSON array with this exact structure:
        [
        {{"topic": "Topic Title", "description": "Brief description of the topic"}},
        ...
        ]

        Make the topics diverse, covering different skill levels (beginner to advanced) and different areas within {category}.
        Focus on practical, actionable topics that would make good tutorial or educational content."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert programming educator who creates engaging technical content ideas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher temperature for more creative ideas
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # Parse the JSON response
            try:
                result = json.loads(content)
                # Handle both direct array and wrapped object responses
                if isinstance(result, dict):
                    # Try common keys
                    ideas = result.get('ideas') or result.get('topics') or result.get('data') or []
                else:
                    ideas = result

                logger.info(f"Successfully generated {len(ideas)} ideas")
                return ideas[:count]  # Ensure we don't exceed requested count
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response content: {content}")
                return []

        except Exception as e:
            logger.error(f"Error generating ideas: {e}")
            return []

    def generate_content(self, topic: str, description: str = "",
                        word_count: int = 800) -> Optional[Dict[str, str]]:
        """
        Generate detailed content for a programming topic

        Args:
            topic: The topic to write about
            description: Additional context about the topic
            word_count: Target word count for the content

        Returns:
            Dictionary with 'title' and 'content' keys, or None if generation fails
        """
        logger.info(f"Generating content for topic: {topic}")

        context = f"\n\nContext: {description}" if description else ""

        prompt = f"""Write a comprehensive, educational article about the following programming topic:

        Topic: {topic}{context}

        Requirements:
        - Target length: approximately {word_count} words
        - Include practical examples and code snippets where appropriate
        - Structure the content with clear sections
        - Make it engaging and educational for developers
        - Include best practices and common pitfalls
        - Use markdown formatting for better readability

        Provide the response as JSON with this structure:
        {{
        "title": "An engaging title for the article",
        "content": "The full article content in markdown format"
        }}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert programming educator and technical writer who creates clear, comprehensive, and engaging educational content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            try:
                result = json.loads(content)

                if 'title' in result and 'content' in result:
                    logger.info(f"Successfully generated content: {result['title']}")
                    return result
                else:
                    logger.error("Response missing 'title' or 'content' fields")
                    return None

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return None

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return None

    def is_similar_topic(self, new_topic: str, existing_topics: List[str],
                        similarity_threshold: float = 0.8) -> bool:
        """
        Use OpenAI to determine if a new topic is too similar to existing topics

        Args:
            new_topic: The new topic to check
            existing_topics: List of existing topic strings
            similarity_threshold: Not used with LLM approach, kept for API compatibility

        Returns:
            True if the topic is similar to an existing one, False otherwise
        """
        if not existing_topics:
            return False

        logger.info(f"Checking similarity for topic: {new_topic}")

        prompt = f"""Determine if the following new topic is substantially similar to any of the existing topics.
        Consider them similar if they would result in overlapping or redundant content.

        New topic: "{new_topic}"

        Existing topics:
        {chr(10).join(f"- {topic}" for topic in existing_topics)}

        Respond with a JSON object:
        {{
        "is_similar": true or false,
        "reason": "Brief explanation of your decision"
        }}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying duplicate or overlapping content topics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent decisions
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            is_similar = result.get('is_similar', False)
            reason = result.get('reason', '')

            if is_similar:
                logger.info(f"Topic deemed similar: {reason}")
            else:
                logger.info(f"Topic is unique: {reason}")

            return is_similar

        except Exception as e:
            logger.error(f"Error checking similarity: {e}")
            # On error, be conservative and assume it's not similar
            return False
