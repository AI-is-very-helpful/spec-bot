"""Infrastructure layer package - Lazy imports for optional dependencies"""

def __getattr__(name: str):
    """Lazy import to avoid hard dependency on PyGithub"""
    if name == "PyGitHubRepository":
        from src.infrastructure.repositories.github import PyGitHubRepository
        return PyGitHubRepository
    elif name == "AzureOpenAIService":
        from src.infrastructure.services.openai import AzureOpenAIService
        return AzureOpenAIService
    elif name == "TeamsCardBuilder":
        from src.infrastructure.services.card import TeamsCardBuilder
        return TeamsCardBuilder
    elif name == "MermaidInkRenderer":
        from src.infrastructure.services.mermaid import MermaidInkRenderer
        return MermaidInkRenderer
    elif name == "TeamsBotService":
        from src.infrastructure.services.teams_bot import TeamsBotService
        return TeamsBotService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AzureOpenAIService",
    "MermaidInkRenderer", 
    "PyGitHubRepository",
    "TeamsBotService",
    "TeamsCardBuilder",
]
