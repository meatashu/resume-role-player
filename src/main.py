#!/usr/bin/env python3

import typer
from rich.console import Console
from rich.prompt import Prompt
from src.llm import OllamaLLM
from src.persona import PersonaManager
from src.knowledge_base import KnowledgeBase

app = typer.Typer()
console = Console()

@app.command()
def chat():
    """Start an interactive chat session with AshuBot"""
    console.print("[bold green]🤖 Welcome to AshuBot - The Multipotentialite in a Hoodie![/bold green]")
    
    # Initialize components
    llm = OllamaLLM()
    knowledge = KnowledgeBase()
    persona_manager = PersonaManager(llm, knowledge)
    
    # Display available roles
    console.print("\n[bold cyan]Available Roles:[/bold cyan]")
    for role in persona_manager.get_available_roles():
        console.print(f"🎭 {role}")
    
    while True:
        # Get role selection
        role = Prompt.ask("\n[bold yellow]Choose a role[/bold yellow]", 
                         choices=persona_manager.get_available_roles())
        
        # Switch persona
        persona_manager.switch_persona(role)
        
        # Get user input
        user_input = Prompt.ask("\n[bold white]You")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            console.print("[bold green]👋 Thanks for chatting! Keep being awesome![/bold green]")
            break
            
        # Generate and display response
        response = persona_manager.get_response(user_input)
        console.print(f"\n[bold blue]AshuBot ({role})[/bold blue]: {response}")

if __name__ == "__main__":
    app()