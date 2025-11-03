import json
from pathlib import Path
from typing import Dict, List, Optional

class KnowledgeBase:
    def __init__(self, base_path: str = "../knowledge_base"):
        self.base_path = Path(base_path)
        self.data = self._load_knowledge()
    
    def _load_knowledge(self) -> Dict:
        """Load all knowledge base files"""
        knowledge = {}
        
        # Load CV data
        cv_path = self.base_path / "cv.json"
        if cv_path.exists():
            with open(cv_path) as f:
                knowledge["cv"] = json.load(f)
                
        # Load projects data
        projects_path = self.base_path / "projects.json"
        if projects_path.exists():
            with open(projects_path) as f:
                knowledge["projects"] = json.load(f)
                
        # Load patents data
        patents_path = self.base_path / "patents.json"
        if patents_path.exists():
            with open(patents_path) as f:
                knowledge["patents"] = json.load(f)
        
        return knowledge
    
    def get_relevant_context(self, query: str) -> str:
        """
        Retrieve relevant context based on user query
        Simple keyword-based retrieval for now
        Could be enhanced with embeddings and semantic search
        """
        context_parts = []
        
        # Add CV information if relevant
        if "experience" in query.lower() or "work" in query.lower():
            if "cv" in self.data:
                context_parts.append("Experience: " + json.dumps(self.data["cv"].get("experience", [])))
        
        # Add project information if relevant
        if "project" in query.lower():
            if "projects" in self.data:
                context_parts.append("Projects: " + json.dumps(self.data["projects"]))
        
        # Add patent information if relevant
        if "patent" in query.lower() or "invention" in query.lower():
            if "patents" in self.data:
                context_parts.append("Patents: " + json.dumps(self.data["patents"]))
        
        return "\n".join(context_parts) if context_parts else ""