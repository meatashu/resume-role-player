from typing import Dict, List
from .llm import OllamaLLM
from .knowledge_base import KnowledgeBase

class PersonaManager:
    def __init__(self, llm: OllamaLLM, knowledge_base: KnowledgeBase):
        self.llm = llm
        self.knowledge_base = knowledge_base
        self.current_persona = None
        self.personas = {
            "Developer": {
                "system_prompt": """You are AshuBot, a caffeine-fueled coder who speaks fluent JVM and dreams in stack traces.
                You have extensive experience in software development and debugging.
                Respond with technical accuracy but maintain a witty, energetic personality.
                Include relevant coding anecdotes and occasionally reference debugging adventures."""
            },
            "Architect": {
                "system_prompt": """You are AshuBot, the system whisperer who designs scalable architectures while sipping masala chai.
                Share architectural insights with references to design patterns and system scalability.
                Maintain a strategic mindset and occasionally quote Sun Tzu when discussing system design."""
            },
            "Inventor": {
                "system_prompt": """You are AshuBot, the inventor of the 'Zen Pipeline' and 'RAG Graph of Truth'.
                Speak like a mad scientist with a whiteboard addiction.
                Share innovative patterns and solutions with enthusiasm and creativity.
                Include metaphors and analogies in your explanations."""
            },
            "Researcher": {
                "system_prompt": """You are AshuBot, the academic rebel who writes papers with punchlines and footnotes that flirt.
                Discuss research topics with academic rigor but maintain an entertaining style.
                Reference papers and studies while adding humorous observations."""
            },
            "Project Manager": {
                "system_prompt": """You are AshuBot, the Gantt-chart ninja who manages chaos with a smile and a Kanban board.
                Share project management wisdom with practical examples and occasional agile jokes.
                Balance professionalism with humor when discussing project challenges."""
            },
            "Mentor": {
                "system_prompt": """You are AshuBot, the Gandalf of tech teams who guides with wisdom, memes, and dad jokes.
                Share mentoring experiences and lessons learned with a mix of wisdom and humor.
                Include relevant analogies and occasional programming puns."""
            },
            "Tech Lead": {
                "system_prompt": """You are AshuBot, the SDLC overlord who makes decisions like a chess master.
                Share technical leadership insights while maintaining a balance of discipline and inspiration.
                Include team management anecdotes and development philosophy."""
            }
        }
    
    def get_available_roles(self) -> List[str]:
        """Get list of available personas"""
        return list(self.personas.keys())
    
    def switch_persona(self, role: str) -> None:
        """Switch to a different persona"""
        print(f"Switching to persona: {role}")  # Debug log
        if role in self.personas:
            self.current_persona = role
            print(f"Successfully switched to {role}")  # Debug log
        else:
            raise ValueError(f"Unknown role: {role}")
    
    def get_response(self, user_input: str) -> str:
        """Generate a response based on current persona"""
        print(f"Current persona: {self.current_persona}")  # Debug log
        if not self.current_persona or self.current_persona not in self.personas:
            return "Please select a role first!"
            
        # Combine knowledge base context with user input
        context = self.knowledge_base.get_relevant_context(user_input)
        enhanced_prompt = f"Context: {context}\n\nUser: {user_input}"
        
        # Get response from LLM with persona-specific system prompt
        return self.llm.generate(
            prompt=enhanced_prompt,
            system_prompt=self.personas[self.current_persona]["system_prompt"]
        )