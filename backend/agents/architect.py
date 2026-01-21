from typing import List, Dict
from pydantic import BaseModel

class EnvironmentConfig(BaseModel):
    image: str
    setup_commands: List[str]

class Architect:
    """
    Module 3: THE ARCHITECT (Environment Manager)
    Determines code runtime environment.
    """

    @staticmethod
    def plan_environment(framework: str, requirements_txt: str = None) -> EnvironmentConfig:
        image = "python:3.10-slim"
        commands = []
        
        # 1. Image Selection
        if framework == "pytorch":
            image = "ray-project/ray-ml:latest-gpu"
        elif framework == "tensorflow":
            image = "tensorflow/tensorflow:latest-gpu"
        elif framework == "jax":
            image = "nvidia/jax:latest"
            
        # 2. Setup Commands
        if requirements_txt:
            # In a real scenario, we might write this to a file, but here we just list the command
            commands.append("pip install -r requirements.txt")
        else:
            # Minimal install if no requirements provided but framework detected?
            # Usually base images have them, keeping it clean.
            pass
            
        return EnvironmentConfig(image=image, setup_commands=commands)
