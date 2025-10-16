#!/usr/bin/env python3
"""
Programming Content Generator Service

A periodic service that generates programming content ideas using OpenAI API,
stores them in SQLite, and generates detailed content pieces.
"""

import time
import logging
import argparse
from typing import Optional
from datetime import datetime
import schedule

from database import Database
from content_generator import ContentGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentGeneratorService:
    """Main service for periodic content generation"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "gpt-4o-mini",
                 db_path: str = "content_generator.db",
                 ideas_per_run: int = 5,
                 content_per_run: int = 3,
                 category: str = "programming"):
        """
        Initialize the content generator service

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            db_path: Path to SQLite database
            ideas_per_run: Number of ideas to generate per run
            content_per_run: Number of content pieces to generate per run
            category: Category of programming topics
        """
        self.db = Database(db_path)
        self.generator = ContentGenerator(api_key=api_key, model=model)
        self.ideas_per_run = ideas_per_run
        self.content_per_run = content_per_run
        self.category = category

    def generate_and_store_ideas(self):
        """Generate new ideas and store them in the database"""
        logger.info("=" * 60)
        logger.info("Starting idea generation cycle")
        logger.info("=" * 60)

        try:
            # Generate ideas using OpenAI
            raw_ideas = self.generator.generate_ideas(
                count=self.ideas_per_run,
                category=self.category
            )

            if not raw_ideas:
                logger.warning("No ideas generated")
                return

            # Get existing topics for deduplication
            existing_ideas = self.db.get_all_ideas()
            existing_topics = [idea['topic'] for idea in existing_ideas]

            new_count = 0
            duplicate_count = 0

            # Process each generated idea
            for idea in raw_ideas:
                topic = idea.get('topic', '').strip()
                description = idea.get('description', '').strip()

                if not topic:
                    logger.warning("Skipping idea with empty topic")
                    continue

                # Check if topic already exists (simple string match)
                if self.db.idea_exists(topic):
                    logger.info(f"Duplicate topic (exact match): {topic}")
                    duplicate_count += 1
                    continue

                # Check for semantic similarity using OpenAI
                is_similar = self.generator.is_similar_topic(topic, existing_topics)

                if is_similar:
                    logger.info(f"Duplicate topic (similar): {topic}")
                    duplicate_count += 1
                    continue

                # Add new idea to database
                idea_id = self.db.add_idea(topic, description)

                if idea_id:
                    logger.info(f"Added new idea #{idea_id}: {topic}")
                    existing_topics.append(topic)  # Add to list for subsequent checks
                    new_count += 1
                else:
                    duplicate_count += 1

            logger.info(f"Idea generation complete: {new_count} new, {duplicate_count} duplicates")

        except Exception as e:
            logger.error(f"Error in idea generation: {e}", exc_info=True)

    def generate_and_store_content(self):
        """Generate content for pending ideas"""
        logger.info("=" * 60)
        logger.info("Starting content generation cycle")
        logger.info("=" * 60)

        try:
            # Get pending ideas
            pending_ideas = self.db.get_pending_ideas(limit=self.content_per_run)

            if not pending_ideas:
                logger.info("No pending ideas to generate content for")
                return

            logger.info(f"Found {len(pending_ideas)} pending ideas")

            generated_count = 0

            for idea in pending_ideas:
                idea_id = idea['id']
                topic = idea['topic']
                description = idea.get('description', '')

                logger.info(f"Generating content for: {topic}")

                # Generate content using OpenAI
                result = self.generator.generate_content(
                    topic=topic,
                    description=description,
                    word_count=800
                )

                if result:
                    title = result['title']
                    content = result['content']

                    # Store in database
                    content_id = self.db.add_content(idea_id, title, content)
                    logger.info(f"Stored content #{content_id}: {title}")
                    generated_count += 1
                else:
                    logger.error(f"Failed to generate content for: {topic}")

            logger.info(f"Content generation complete: {generated_count} pieces created")

        except Exception as e:
            logger.error(f"Error in content generation: {e}", exc_info=True)

    def run_cycle(self):
        """Run one complete cycle of idea and content generation"""
        logger.info("\n" + "=" * 60)
        logger.info(f"Running generation cycle at {datetime.now()}")
        logger.info("=" * 60)

        # Show current stats
        stats = self.db.get_stats()
        logger.info(f"Current stats: {stats}")

        # Generate new ideas
        self.generate_and_store_ideas()

        # Generate content for pending ideas
        self.generate_and_store_content()

        # Show updated stats
        stats = self.db.get_stats()
        logger.info(f"Updated stats: {stats}")
        logger.info("Cycle complete\n")

    def run_once(self):
        """Run the service once and exit"""
        logger.info("Running in one-shot mode")
        self.run_cycle()

    def run_periodic(self, interval_minutes: int = 60):
        """
        Run the service periodically

        Args:
            interval_minutes: How often to run the generation cycle (in minutes)
        """
        logger.info(f"Starting periodic service (interval: {interval_minutes} minutes)")

        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.run_cycle)

        # Run immediately on startup
        self.run_cycle()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Service stopped by user")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Programming Content Generator Service"
    )

    parser.add_argument(
        '--mode',
        choices=['once', 'periodic'],
        default='once',
        help='Run mode: once (single run) or periodic (continuous)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Interval in minutes for periodic mode (default: 60)'
    )

    parser.add_argument(
        '--ideas',
        type=int,
        default=5,
        help='Number of ideas to generate per run (default: 5)'
    )

    parser.add_argument(
        '--content',
        type=int,
        default=3,
        help='Number of content pieces to generate per run (default: 3)'
    )

    parser.add_argument(
        '--category',
        type=str,
        default='programming',
        help='Category of topics (default: programming)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o-mini',
        help='OpenAI model to use (default: gpt-4o-mini)'
    )

    parser.add_argument(
        '--db',
        type=str,
        default='content_generator.db',
        help='Database file path (default: content_generator.db)'
    )

    args = parser.parse_args()

    # Create service instance
    service = ContentGeneratorService(
        model=args.model,
        db_path=args.db,
        ideas_per_run=args.ideas,
        content_per_run=args.content,
        category=args.category
    )

    # Run based on mode
    if args.mode == 'once':
        service.run_once()
    else:
        service.run_periodic(interval_minutes=args.interval)


if __name__ == "__main__":
    main()
