import logging
from typing import Optional
from dataclasses import dataclass
from agents.error_detector import ErrorReport, ErrorType

logger = logging.getLogger(__name__)

@dataclass
class RecoveryAction:
    """Defines a recovery action for a detected error."""
    applicable: bool
    description: str
    command: Optional[str] = None  # Auto-executable command (e.g., "pip install torch")
    requires_user_approval: bool = False
    estimated_time: int = 10  # seconds
    success_message: str = "Recovery successful"

class RecoveryEngine:
    """
    Intelligent error recovery system.
    Proposes and applies fixes based on error type.
    """
    
    @staticmethod
    async def propose_fix(error: ErrorReport) -> RecoveryAction:
        """
        Analyzes error and proposes appropriate fix.
        """
        logger.info(f"Proposing fix for error type: {error.type.value}")
        
        if error.type == ErrorType.DEPENDENCY_MISSING:
            return RecoveryEngine._fix_missing_dependency(error)
        
        elif error.type == ErrorType.GPU_OOM:
            return RecoveryEngine._fix_gpu_oom(error)
        
        elif error.type == ErrorType.NETWORK_TIMEOUT:
            return RecoveryEngine._fix_network_timeout(error)
        
        elif error.type == ErrorType.SYNTAX_ERROR:
            return RecoveryEngine._fix_syntax_error(error)
        
        elif error.type == ErrorType.SSH_AUTH_FAILURE:
            return RecoveryEngine._fix_ssh_auth(error)
        
        else:
            # v1.5: RAG-based Self-Healing
            # Bilinmeyen hata tipleri için yüklenmiş dokümanlarda çözüm ara
            try:
                from services.memory_core import MemoryCore
                
                # Hata mesajını kullanarak RAG'da arama yap
                error_query = f"{error.type.value}: {error.message}" if hasattr(error, 'message') else str(error.type.value)
                
                # Senkron bağlamda async fonksiyon çağırmak için
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Zaten bir event loop varsa, create_task kullan
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, MemoryCore.search(error_query, top_k=3))
                            rag_results = future.result()
                    else:
                        rag_results = loop.run_until_complete(MemoryCore.search(error_query, top_k=3))
                except RuntimeError:
                    rag_results = asyncio.run(MemoryCore.search(error_query, top_k=3))
                
                if rag_results and len(rag_results) > 0:
                    # En iyi sonucu al
                    best_match = rag_results[0]
                    content = best_match.get("content", "")[:500]  # İlk 500 karakter
                    source = best_match.get("source", "knowledge base")
                    score = best_match.get("score", 0)
                    
                    logger.info(f"RAG found solution for unknown error (score: {score:.2f})")
                    
                    return RecoveryAction(
                        applicable=True,
                        description=f"🤖 AI Önerisi (Kaynak: {source}, Güven: {score:.0%}):\n{content}",
                        command=None,  # Manuel uygulama gerekli
                        requires_user_approval=True,
                        estimated_time=0,
                        success_message="AI önerisi uygulandı"
                    )
                else:
                    logger.info("RAG search returned no results for unknown error")
                    
            except Exception as e:
                logger.warning(f"RAG search failed for self-healing: {e}")
            
            # RAG'dan sonuç bulunamazsa varsayılan yanıt
            return RecoveryAction(
                applicable=False,
                description="Bilinmeyen hata - bilgi tabanında çözüm bulunamadı, manuel müdahale gerekli",
                requires_user_approval=True
            )
    
    @staticmethod
    def _fix_missing_dependency(error: ErrorReport) -> RecoveryAction:
        """Auto-install missing Python package."""
        package = error.context.get("missing_package", "unknown")
        
        return RecoveryAction(
            applicable=True,
            description=f"Install missing package: {package}",
            command=f"pip install {package}",
            requires_user_approval=False,
            estimated_time=30,
            success_message=f"✅ Package '{package}' installed successfully"
        )
    
    @staticmethod
    def _fix_gpu_oom(error: ErrorReport) -> RecoveryAction:
        """
        GPU OOM cannot be auto-fixed, but we can suggest alternatives.
        In future: Call Sniper to find node with more VRAM.
        """
        return RecoveryAction(
            applicable=False,
            description="GPU Out of Memory - Consider reducing batch size or upgrading GPU",
            requires_user_approval=True,
            command=None  # Would require script modification or GPU change
        )
    
    @staticmethod
    def _fix_network_timeout(error: ErrorReport) -> RecoveryAction:
        """Retry with longer timeout."""
        return RecoveryAction(
            applicable=True,
            description="Retry with increased timeout",
            command=None,  # Handled by retry logic, not a shell command
            requires_user_approval=False,
            estimated_time=5,
            success_message="⏳ Retrying with longer timeout..."
        )
    
    @staticmethod
    def _fix_syntax_error(error: ErrorReport) -> RecoveryAction:
        """
        Syntax errors require code changes.
        Future: Use AI to suggest fix.
        """
        return RecoveryAction(
            applicable=False,
            description="Syntax error detected - please review and fix script",
            requires_user_approval=True,
            command=None
        )
    
    @staticmethod
    def _fix_ssh_auth(error: ErrorReport) -> RecoveryAction:
        """SSH auth failures require new credentials."""
        return RecoveryAction(
            applicable=False,
            description="SSH authentication failed - please verify credentials",
            requires_user_approval=True,
            command=None
        )
    
    @staticmethod
    async def apply_fix(
        action: RecoveryAction,
        ssh_info: dict
    ) -> tuple[bool, str]:
        """
        Executes recovery action via SSH.
        Returns (success, message).
        """
        if not action.applicable or not action.command:
            return False, "Action not applicable or no command defined"
        
        try:
            from services.ssh_manager import SSHManager
            
            logger.info(f"Executing recovery command: {action.command}")
            
            output_lines = []
            async for line in SSHManager.execute_command_stream(
                hostname=ssh_info.get('hostname'),
                username=ssh_info.get('username'),
                private_key_str=ssh_info.get('private_key'),
                port=int(ssh_info.get('port', 22)),
                command=action.command
            ):
                output_lines.append(line)
            
            # Check if command succeeded (basic check)
            output = "\n".join(output_lines)
            if "error" in output.lower() or "failed" in output.lower():
                return False, f"Recovery command failed: {output}"
            
            return True, action.success_message
            
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return False, f"Recovery error: {str(e)}"
