# Developer Guide: AshuBot Resume Assistant

This guide explains how to set up, extend, and maintain the AshuBot Resume Assistant system.

## Project Structure

```
ashubot/
├── src/
│   ├── main.py           # Main chat interface
│   ├── llm.py           # Ollama LLM integration
│   ├── persona.py       # Persona management
│   ├── kb_ingest.py     # Knowledge base ingestion
│   ├── staging.py       # Staging system
│   └── ingest_cli.py    # CLI for ingestion
├── web/
│   └── app.py           # Streamlit web interface
├── knowledge_base/      # KB JSON files
│   ├── cv.json
│   ├── projects.json
│   ├── patents.json
│   └── certifications.json
├── data/
│   └── staging/        # Staged changes
└── docs/              # Documentation
```

## Setup Development Environment

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Ollama:
Visit [ollama.ai](https://ollama.ai) and follow installation instructions.

## Running Tests

```bash
# Run a quick import test
python -c "import importlib; importlib.import_module('src.kb_ingest'); print('OK')"
```

## Core Components

### 1. Knowledge Base Ingestion (`kb_ingest.py`)
- Handles PDF/DOCX parsing
- Sanitizes personal information
- Extracts structured data
- LinkedIn profile scraping

```python
from src.kb_ingest import ingest_files

# Example usage
result = ingest_files(
    ["resume.pdf"], 
    linkedin_url="https://linkedin.com/in/...",
    use_staging=True
)
```

### 2. Staging System (`staging.py`)
- Manages staged content before KB merge
- Provides review/approval workflow
- Handles conflict resolution

```python
from src.staging import stage_parsed_content, approve_staged_entry

# Stage content
stage_id = stage_parsed_content(parsed_data, source_info)

# Approve changes
result = approve_staged_entry(stage_id)
```

### 3. Persona Management (`persona.py`)
- Manages different chat personas
- Handles role switching
- Integrates with Ollama LLM

```python
from src.persona import PersonaManager

# Initialize
persona_mgr = PersonaManager(llm, knowledge)

# Switch persona
persona_mgr.switch_persona("Developer")
```

## Adding New Features

### 1. Adding a New Persona
Edit `src/persona.py`:
```python
self.personas["NewRole"] = {
    "system_prompt": """Your new role description here..."""
}
```

### 2. Adding KB Fields
1. Update `kb_ingest.py` parsing logic
2. Update JSON schema in knowledge_base
3. Update staging preview logic

### 3. Adding UI Features
1. Edit `web/app.py` for new Streamlit components
2. Update admin dashboard as needed

## Common Development Tasks

### Update Dependencies
1. Add new package to `requirements.txt`
2. Run `pip install -r requirements.txt`
3. Test imports and functionality

### Debug Knowledge Base
1. Check staged entries in `data/staging/`
2. Review KB JSON files directly
3. Use CLI tools for inspection:
```bash
python src/ingest_cli.py --list-staged
```

### Troubleshoot LLM
1. Check Ollama is running:
```bash
curl http://localhost:11434/api/tags
```
2. Review LLM responses in logs

## API Documentation

### KB Ingest Module
```python
def ingest_files(
    file_paths: List[str],
    linkedin_url: Optional[str] = None,
    name_hint: Optional[str] = None,
    use_staging: bool = True
) -> Dict:
    """
    Ingest files into knowledge base.
    
    Args:
        file_paths: List of files to process
        linkedin_url: Optional LinkedIn profile
        name_hint: Name to add to CV
        use_staging: Use staging system
        
    Returns:
        Dict with results and warnings
    """
```

### Staging Module
```python
def stage_parsed_content(
    parsed: Dict,
    source_info: Dict
) -> str:
    """
    Stage content for review.
    
    Args:
        parsed: Parsed content
        source_info: Source metadata
        
    Returns:
        Staging ID
    """
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Submit PR with description

## Troubleshooting

### Common Issues

1. PDF Extraction Fails
- Check pdfplumber installation
- Verify PDF is not encrypted
- Try converting to text first

2. LinkedIn Scraping Issues
- Check network connectivity
- Verify URL format
- Profile might be private

3. LLM Connection Errors
- Verify Ollama is running
- Check port 11434
- Review API endpoint

### Debug Tools

1. List staged content:
```bash
python src/ingest_cli.py --list-staged
```

2. Preview changes:
```bash
python src/ingest_cli.py --preview-id <stage_id>
```

3. Check KB integrity:
```bash
python -c "import json; print(json.load(open('knowledge_base/cv.json')))"
```

## Performance Optimization

1. Document Processing
- Use batch processing for multiple files
- Implement caching for parsed content
- Consider async processing for large files

2. LLM Integration
- Cache common responses
- Implement request batching
- Use streaming for long responses

3. Knowledge Base
- Implement indexing for faster searches
- Use compression for large datasets
- Regular cleanup of old staged data