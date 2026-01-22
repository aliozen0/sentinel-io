from typing import List, Dict, Optional
from pydantic import BaseModel
import re
import logging

logger = logging.getLogger(__name__)


class EnvironmentConfig(BaseModel):
    """Complete environment configuration for remote execution."""
    base_image: str
    python_packages: List[str] = []
    system_packages: List[str] = []
    setup_commands: List[str] = []
    environment_vars: Dict[str, str] = {}
    estimated_setup_time_min: int = 5
    gpu_required: bool = True
    cuda_version: Optional[str] = None


class Architect:
    """
    Module 3: THE ARCHITECT (Environment Manager)
    Intelligently determines code runtime environment based on:
    - Detected framework
    - Code analysis (imports, model sizes)
    - Requirements parsing
    """

    # Common ML/DL package mappings
    PACKAGE_IMAGES = {
        "torch": "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
        "tensorflow": "tensorflow/tensorflow:latest-gpu",
        "jax": "nvidia/jax:latest",
        "transformers": "huggingface/transformers-pytorch-gpu:latest",
        "ray": "rayproject/ray-ml:latest-gpu",
        "lightning": "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
    }

    # System dependencies for common packages
    SYSTEM_DEPS = {
        "opencv": ["libgl1-mesa-glx", "libglib2.0-0"],
        "cv2": ["libgl1-mesa-glx", "libglib2.0-0"],
        "pillow": ["libjpeg-dev", "zlib1g-dev"],
        "audio": ["libsndfile1", "ffmpeg"],
        "soundfile": ["libsndfile1"],
    }

    # CUDA version mappings
    CUDA_VERSIONS = {
        "torch>=2.0": "12.1",
        "torch>=1.0": "11.8",
        "tensorflow>=2.10": "11.8",
        "jax": "12.1",
    }

    SYSTEM_PROMPT = """
    You are a Senior DevOps & MLOps Architect.
    Plan a production-grade Docker environment for the provided Python AI/ML code.
    
    Return ONLY a valid JSON object matching this schema:
    {
        "base_image": "docker_image_name",
        "python_packages": ["pkg1", "pkg2==1.0.0"],
        "system_packages": ["libgl1", "git"],
        "setup_commands": ["apt-get update && ...", "pip install ..."],
        "environment_vars": {"KEY": "VAL"},
        "estimated_setup_time_min": int,
        "cuda_version": "12.1"
    }

    Rules:
    - Choose the most appropriate base image (e.g. pytorch/pytorch, tensorflow/tensorflow, nvidia/cuda).
    - Pin versions where possible.
    - Include all necessary system dependencies for libraries like opencv, audio, etc.
    """

    @staticmethod
    async def plan_environment(
        framework: str,
        code: Optional[str] = None,
        requirements_txt: Optional[str] = None,
        vram_gb: int = 8
    ) -> EnvironmentConfig:
        """
        Creates comprehensive environment config based on analysis.
        Tries LLM first, falls back to legacy logic.
        """
        logger.info(f"Planning environment for framework: {framework}")
        
        # Try LLM
        try:
            try:
                from backend.ai_client import ask_io_intelligence_async
            except ImportError:
                from ai_client import ask_io_intelligence_async

            combined_context = f"FRAMEWORK: {framework}\nVRAM: {vram_gb}GB\n"
            if requirements_txt:
                combined_context += f"REQUIREMENTS.TXT:\n{requirements_txt}\n"
            if code:
                combined_context += f"CODE CONTEXT:\n{code[:20000]}"

            llm_response = await ask_io_intelligence_async(
                system_prompt=Architect.SYSTEM_PROMPT,
                user_prompt=combined_context
            )
            
            import json
            cleaned = llm_response.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)
            return EnvironmentConfig(**data)

        except Exception as e:
            logger.warning(f"LLM Architect failed: {e}. Using fallback logic.")

        # ================= LEGACY FALLBACK =================
        
        # 1. Determine base image
        image = Architect._select_image(framework, code)
        
        # 2. Parse Python packages
        packages = Architect._parse_requirements(requirements_txt, code)
        
        # 3. Detect system dependencies
        system_packages = Architect._detect_system_deps(packages, code)
        
        # 4. Build setup commands
        commands = Architect._build_setup_commands(packages, system_packages)
        
        # 5. Environment variables
        env_vars = Architect._get_env_vars(framework, vram_gb)
        
        # 6. Estimate setup time
        setup_time = Architect._estimate_setup_time(packages, system_packages)
        
        # 7. CUDA version
        cuda_version = Architect._detect_cuda_version(framework, packages)
        
        return EnvironmentConfig(
            base_image=image,
            python_packages=packages,
            system_packages=system_packages,
            setup_commands=commands,
            environment_vars=env_vars,
            estimated_setup_time_min=setup_time,
            gpu_required=vram_gb > 0,
            cuda_version=cuda_version
        )

    @staticmethod
    def _select_image(framework: str, code: Optional[str] = None) -> str:
        """Selects best Docker image based on framework and code."""
        
        # Check for specific libraries in code
        if code:
            code_lower = code.lower()
            
            # HuggingFace transformers
            if "transformers" in code_lower or "from transformers" in code_lower:
                return Architect.PACKAGE_IMAGES["transformers"]
            
            # Ray distributed
            if "import ray" in code_lower or "ray.init" in code_lower:
                return Architect.PACKAGE_IMAGES["ray"]
        
        # Framework-based selection
        framework_lower = framework.lower()
        
        if framework_lower == "pytorch":
            return Architect.PACKAGE_IMAGES["torch"]
        elif framework_lower == "tensorflow":
            return Architect.PACKAGE_IMAGES["tensorflow"]
        elif framework_lower == "jax":
            return Architect.PACKAGE_IMAGES["jax"]
        
        # Default fallback
        return "python:3.10-slim"

    @staticmethod
    def _parse_requirements(
        requirements_txt: Optional[str] = None,
        code: Optional[str] = None
    ) -> List[str]:
        """Parses requirements.txt and extracts imports from code."""
        packages = []
        
        # Parse requirements.txt
        if requirements_txt:
            for line in requirements_txt.strip().split("\n"):
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Skip git/http installs for now
                if line.startswith(("git+", "http://", "https://")):
                    continue
                # Remove inline comments
                if "#" in line:
                    line = line.split("#")[0].strip()
                if line:
                    packages.append(line)
        
        # Extract imports from code if no requirements provided
        if not packages and code:
            imports = Architect._extract_imports(code)
            # Map common imports to pip packages
            import_to_package = {
                "torch": "torch",
                "torchvision": "torchvision",
                "numpy": "numpy",
                "pandas": "pandas",
                "sklearn": "scikit-learn",
                "cv2": "opencv-python",
                "PIL": "Pillow",
                "transformers": "transformers",
                "datasets": "datasets",
                "accelerate": "accelerate",
                "wandb": "wandb",
                "tqdm": "tqdm",
                "matplotlib": "matplotlib",
                "seaborn": "seaborn",
            }
            
            for imp in imports:
                if imp in import_to_package:
                    packages.append(import_to_package[imp])
        
        return list(set(packages))  # Remove duplicates

    @staticmethod
    def _extract_imports(code: str) -> List[str]:
        """Extracts import statements from Python code."""
        imports = []
        
        # Match: import x, from x import y
        import_pattern = r'(?:from\s+(\w+)|import\s+(\w+))'
        matches = re.findall(import_pattern, code)
        
        for match in matches:
            module = match[0] or match[1]
            if module and module not in ["__future__"]:
                imports.append(module)
        
        return list(set(imports))

    @staticmethod
    def _detect_system_deps(packages: List[str], code: Optional[str] = None) -> List[str]:
        """Detects required system packages."""
        system_pkgs = []
        
        # Check packages
        for pkg in packages:
            pkg_lower = pkg.lower().split("==")[0].split(">=")[0].split("<=")[0]
            for key, deps in Architect.SYSTEM_DEPS.items():
                if key in pkg_lower:
                    system_pkgs.extend(deps)
        
        # Check code for common patterns
        if code:
            code_lower = code.lower()
            for key, deps in Architect.SYSTEM_DEPS.items():
                if key in code_lower:
                    system_pkgs.extend(deps)
        
        return list(set(system_pkgs))

    @staticmethod
    def _build_setup_commands(packages: List[str], system_packages: List[str]) -> List[str]:
        """Builds shell commands for environment setup."""
        commands = []
        
        # System packages first
        if system_packages:
            apt_cmd = f"apt-get update && apt-get install -y {' '.join(system_packages)}"
            commands.append(apt_cmd)
        
        # Python packages
        if packages:
            pip_cmd = f"pip install --no-cache-dir {' '.join(packages)}"
            commands.append(pip_cmd)
        
        return commands

    @staticmethod
    def _get_env_vars(framework: str, vram_gb: int) -> Dict[str, str]:
        """Returns recommended environment variables."""
        env_vars = {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        
        if framework.lower() == "pytorch":
            env_vars["TORCH_HOME"] = "/tmp/torch_cache"
            # Memory optimization for large models
            if vram_gb >= 16:
                env_vars["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
        
        if framework.lower() == "tensorflow":
            env_vars["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Reduce TF verbosity
            env_vars["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
        
        return env_vars

    @staticmethod
    def _estimate_setup_time(packages: List[str], system_packages: List[str]) -> int:
        """Estimates setup time in minutes."""
        base_time = 2  # Base container start time
        
        # Heavy packages add more time
        heavy_packages = ["torch", "tensorflow", "jax", "transformers"]
        for pkg in packages:
            if any(heavy in pkg.lower() for heavy in heavy_packages):
                base_time += 3
        
        # System packages add time
        base_time += len(system_packages) * 0.5
        
        return int(min(base_time, 15))  # Cap at 15 minutes

    @staticmethod
    def _detect_cuda_version(framework: str, packages: List[str]) -> Optional[str]:
        """Detects required CUDA version."""
        for pkg in packages:
            for pattern, version in Architect.CUDA_VERSIONS.items():
                if pattern.split(">=")[0] in pkg.lower():
                    return version
        
        # Framework defaults
        if framework.lower() in ["pytorch", "jax"]:
            return "12.1"
        elif framework.lower() == "tensorflow":
            return "11.8"
        
        return None


# Backward compatibility wrapper
async def plan_environment(framework: str, requirements_txt: str = None) -> EnvironmentConfig:
    """Legacy wrapper for backward compatibility."""
    return await Architect.plan_environment(framework=framework, requirements_txt=requirements_txt)
