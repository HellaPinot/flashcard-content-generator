# Programming Content Generator

An automated service that generates programming educational content using OpenAI's API. The service periodically generates topic ideas, stores them in a SQLite database, and creates detailed content pieces for each topic.

## Features

- **Automatic Idea Generation**: Uses OpenAI API to generate diverse programming topic ideas
- **Smart Deduplication**: Prevents duplicate content using both exact matching and semantic similarity detection
- **Content Generation**: Creates comprehensive educational articles with code examples
- **SQLite Storage**: Persistent storage for all ideas and generated content
- **Periodic Scheduling**: Runs automatically at configurable intervals
- **Flexible Configuration**: Customizable topics, intervals, and batch sizes

## Architecture

The service consists of three main components:

1. **Database (`database.py`)**: SQLite database management with tables for ideas and content
2. **Content Generator (`content_generator.py`)**: OpenAI API integration for generating ideas and content
3. **Service (`service.py`)**: Main service orchestrator with scheduling capabilities

## Installation

1. Clone the repository or download the files

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
# Option 1: Environment variable
export OPENAI_API_KEY="your-api-key-here"

# Option 2: Create a .env file (copy from .env.example)
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### Basic Usage (One-time Run)

Generate 5 ideas and 3 content pieces:
```bash
python service.py --mode once
```

### Periodic Mode

Run continuously, generating content every hour:
```bash
python service.py --mode periodic --interval 60
```

### Advanced Options

```bash
python service.py \
  --mode periodic \
  --interval 120 \
  --ideas 10 \
  --content 5 \
  --category "web development" \
  --model gpt-4o \
  --db my_content.db
```

### Available Arguments

- `--mode`: Run mode - `once` (single run) or `periodic` (continuous)
- `--interval`: Minutes between runs in periodic mode (default: 60)
- `--ideas`: Number of ideas to generate per run (default: 5)
- `--content`: Number of content pieces to generate per run (default: 3)
- `--category`: Topic category (default: "programming")
- `--model`: OpenAI model to use (default: "gpt-4o-mini")
- `--db`: Database file path (default: "content_generator.db")

## Database Schema

### Ideas Table
- `id`: Primary key
- `topic`: Unique topic title
- `description`: Brief topic description
- `created_at`: Timestamp
- `content_generated`: Boolean flag

### Content Table
- `id`: Primary key
- `idea_id`: Foreign key to ideas table
- `title`: Article title
- `content`: Full article content (markdown)
- `created_at`: Timestamp

## How It Works

1. **Idea Generation**:
   - Requests N new topic ideas from OpenAI
   - Checks each idea against existing topics (exact match)
   - Uses semantic similarity detection to avoid near-duplicates
   - Stores unique ideas in the database

2. **Content Generation**:
   - Retrieves pending ideas (not yet generated)
   - For each idea, generates a comprehensive article
   - Stores the content in the database
   - Marks the idea as completed

3. **Periodic Operation**:
   - Runs the complete cycle at specified intervals
   - Logs statistics after each run
   - Continues indefinitely until stopped

## Example Output

```
============================================================
Running generation cycle at 2025-10-16 14:30:00
============================================================
Current stats: {'total_ideas': 15, 'ideas_with_content': 10, 'pending_ideas': 5, 'total_content_pieces': 10}

Starting idea generation cycle
Generated 5 new ideas
Checking for duplicates...
Added new idea #16: Understanding Python Decorators
Added new idea #17: Building REST APIs with FastAPI
Duplicate topic (similar): Introduction to Python Decorators
Added new idea #18: WebSocket Communication in Node.js
...

Starting content generation cycle
Found 5 pending ideas
Generating content for: Understanding Python Decorators
Stored content #11: Mastering Python Decorators: A Complete Guide
...
```

## Database Inspection

You can inspect the database using the SQLite CLI or any SQLite browser:

```bash
sqlite3 content_generator.db

# View all ideas
SELECT id, topic, content_generated FROM ideas;

# View generated content
SELECT i.topic, c.title, c.created_at
FROM content c
JOIN ideas i ON c.idea_id = i.id;

# Get statistics
SELECT
  COUNT(*) as total_ideas,
  SUM(CASE WHEN content_generated THEN 1 ELSE 0 END) as completed,
  COUNT(*) - SUM(CASE WHEN content_generated THEN 1 ELSE 0 END) as pending
FROM ideas;
```

## Cost Considerations

The service uses OpenAI's API, which incurs costs:

- **gpt-4o-mini** (default): Most cost-effective option
  - Input: ~$0.15 per 1M tokens
  - Output: ~$0.60 per 1M tokens

- **gpt-4o**: Higher quality but more expensive
  - Input: ~$2.50 per 1M tokens
  - Output: ~$10.00 per 1M tokens

Example cost per run (with gpt-4o-mini):
- 5 ideas generation: ~$0.01
- 3 content pieces: ~$0.05
- **Total per run: ~$0.06**

Running hourly for a month: ~$43

## Customization

### Changing Topic Categories

Modify the `--category` parameter to focus on specific areas:
```bash
python service.py --category "data structures and algorithms"
python service.py --category "machine learning"
python service.py --category "web development frameworks"
```

### Adjusting Content Length

Edit `content_generator.py` line 104 to change the `word_count` parameter:
```python
word_count=1200  # Longer articles
```

### Custom Prompts

Modify the prompts in `content_generator.py`:
- Line 27: Idea generation prompt
- Line 85: Content generation prompt

## Troubleshooting

**Error: "OpenAI API key must be provided"**
- Set the `OPENAI_API_KEY` environment variable
- Or create a `.env` file with your API key

**No ideas being generated**
- Check your API key is valid
- Verify you have API credits available
- Check the logs for specific error messages

**Duplicate detection too aggressive/lenient**
- Adjust the similarity detection logic in `content_generator.py:147`
- Modify the prompt to be more/less strict

## License

MIT License - feel free to modify and use as needed.

## Contributing

Contributions welcome! Please submit issues or pull requests on GitHub.
