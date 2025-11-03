# AshuBot - The Multipotentialite in a Hoodie

A witty, role-switching chatbot that lets interviewers explore your career through interactive personas. Think of it as a living CV that answers questions, cracks jokes, and shifts gears between roles like a polymath on roller skates.

## Features

- 🎭 Multiple personas (Developer, Architect, Inventor, etc.)
- 🧠 Powered by Ollama LLM
- 📚 Rich knowledge base integration
- 😄 Built-in humor and personality
- 🌐 Web interface with admin dashboard
- � Interaction analytics and feedback system
- 🔒 Content moderation and access control

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ashubot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Update the knowledge base:
Edit the JSON files in the `knowledge_base` directory with your information:
- `cv.json`: Your professional experience and skills
- `projects.json`: Notable projects and achievements
- `patents.json`: Patents and innovations

## Usage

### Web Interface (Recommended)

1. Start the Streamlit app:
```bash
streamlit run web/app.py
```

2. Choose mode:
   - **Interviewer Mode**: Open to all, provides chat interface
   - **Admin Mode**: Password protected, access to analytics and management

3. Select a persona and start chatting!

Default admin password: `admin123` (change this in production!)

### CLI Interface (Alternative)

1. Start the CLI chatbot:
```bash
python src/main.py
```

2. Choose a persona from the available roles
3. Start chatting!

## Admin Features

1. **Analytics Dashboard**
   - Daily interaction metrics
   - Persona usage statistics
   - Recent conversations

2. **Knowledge Base Management**
   - Update CV, projects, and patents
   - Real-time content editing
   - Version tracking

3. **Content Moderation**
   - Restrict specific queries
   - Block sensitive topics
   - Manage allowed content

4. **Feedback System**
   - User ratings and comments
   - Persona-specific feedback
   - Improvement tracking

## Available Roles

1. 👨‍💻 Software Developer - The caffeine-fueled coder
2. 🏛️ Architect - The system whisperer
3. 🧪 Inventor - The mad scientist of software patterns
4. 📚 Researcher - The academic rebel
5. 🧑‍💼 Project Manager - The Gantt-chart ninja
6. 🧙 Mentor - The Gandalf of tech teams
7. 🧠 Tech Lead - The SDLC overlord

## Contributing

Feel free to submit issues and enhancement requests!# resume-role-player
