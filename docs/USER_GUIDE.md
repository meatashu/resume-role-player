# User Guide: AshuBot Resume Assistant

Welcome to AshuBot, your interactive resume assistant! This guide will help you use the system effectively.

## Getting Started

### Installation

1. Ensure you have Python 3.8+ installed
2. Install Ollama from [ollama.ai](https://ollama.ai)
3. Clone the repository and install:
```bash
git clone <repository-url>
cd ashubot
pip install -r requirements.txt
```

## Using AshuBot

### 1. Web Interface (Recommended)

Start the web interface:
```bash
streamlit run web/app.py
```

#### Interviewer Mode
1. Choose "Interviewer" mode from the sidebar
2. Select a persona:
   - 👨‍💻 Developer: Technical discussions
   - 🏛️ Architect: System design talks
   - 🧪 Inventor: Innovation discussions
   - 📚 Researcher: Academic perspective
   - 🧑‍💼 Project Manager: Project discussions
   - 🧙 Mentor: Career guidance
   - 🧠 Tech Lead: Leadership talks

3. Start chatting!
4. Provide feedback using the feedback form

#### Admin Mode
1. Choose "Admin" mode
2. Enter password (default: admin123)
3. Access features:
   - Analytics Dashboard
   - Knowledge Base Management
   - Content Moderation
   - Feedback Review

### 2. CLI Interface

For quick chats:
```bash
python src/main.py
```

## Updating Your Resume Data

### 1. Using Web Interface (Admin)

1. Log in to Admin mode
2. Go to "Knowledge Base Management"
3. Choose "Review Staged Changes"
4. Upload new files or edit existing data
5. Review and approve changes

### 2. Using Command Line

Stage new resume data:
```bash
python src/ingest_cli.py "your_resume.pdf" --linkedin "your-linkedin-url"
```

List staged changes:
```bash
python src/ingest_cli.py --list-staged
```

Approve changes:
```bash
python src/ingest_cli.py --approve-id <stage_id>
```

### Supported File Types
- PDF resumes
- Word documents (.docx)
- Plain text files
- LinkedIn profiles (public URL)

## Best Practices

### 1. Resume Preparation
- Use standard PDF or DOCX format
- Include clear section headings
- Structure experience with bullet points
- Include dates and metrics

### 2. LinkedIn Integration
- Ensure profile is public
- Complete all relevant sections
- Keep experience up to date
- Add certifications and patents

### 3. Regular Updates
- Review KB content monthly
- Update with new achievements
- Remove outdated information
- Keep personas current

## Features

### 1. Multi-Persona Chat
- Switch between roles
- Context-aware responses
- Professional yet witty style
- Deep knowledge integration

### 2. Knowledge Management
- Automated data extraction
- PII sanitization
- Safe staging system
- Version tracking

### 3. Analytics & Feedback
- Usage statistics
- Persona effectiveness
- User satisfaction
- Interaction patterns

## Tips & Tricks

### 1. Getting Better Responses
- Be specific in questions
- Mention timeframes
- Ask for examples
- Use follow-up questions

### 2. Effective Updates
- Stage multiple files together
- Review changes before approval
- Add context in descriptions
- Keep source links updated

### 3. Content Organization
- Group related experiences
- Highlight key achievements
- Include measurable results
- Tag with relevant skills

## Troubleshooting

### Common Issues

1. Chat Not Responding
- Check if Ollama is running
- Restart the application
- Clear chat history

2. File Upload Issues
- Check file format
- Ensure file is not corrupted
- Try text extraction first

3. LinkedIn Integration
- Verify profile URL
- Check profile privacy
- Try manual data entry

### Getting Help
- Check error messages
- Review documentation
- Contact system admin
- Submit feedback

## Security Notes

- Keep admin password secure
- Don't share sensitive data
- Review staged changes carefully
- Log out from admin mode

## Customization

### Personal Branding
1. Update knowledge base:
   - Professional experience
   - Projects and achievements
   - Patents and publications
   - Certifications

2. Adjust persona styles:
   - Tone and personality
   - Response patterns
   - Industry focus
   - Expertise areas

### Content Focus
1. Highlight key areas:
   - Technical skills
   - Leadership experience
   - Innovation track record
   - Domain expertise

2. Set interaction style:
   - Formal vs casual
   - Detail level
   - Use of analogies
   - Story integration

## Future Updates

Stay tuned for:
- Mobile interface
- More file formats
- Additional personas
- Enhanced analytics
- API integration

## Feedback

Your feedback helps improve AshuBot:
- Use the feedback form
- Rate interactions
- Suggest improvements
- Report issues

Thank you for using AshuBot! For technical details, see the Developer Guide.