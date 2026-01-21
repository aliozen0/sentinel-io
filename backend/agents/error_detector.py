import re
import logging
from typing import Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Error classification categories."""
    DEPENDENCY_MISSING = "dependency"
    GPU_OOM = "gpu_oom"
    NETWORK_TIMEOUT = "network"
    SYNTAX_ERROR = "syntax"
    SSH_AUTH_FAILURE = "ssh_auth"
    UNKNOWN = "unknown"

@dataclass
class ErrorReport:
    """Structured error information."""
    type: ErrorType
    severity: str  # "critical", "warning", "info"
    message: str
    auto_fixable: bool
    context: dict  # Additional context (e.g., missing_package, required_vram)

class ErrorDetector:
    """
    Real-time log parser that detects and classifies errors.
    """
    
    # Error pattern definitions
    PATTERNS = {
        ErrorType.DEPENDENCY_MISSING: [
            r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]",
            r"ImportError: cannot import name ['\"]([^'\"]+)['\"]",
            r"No module named ['\"]([a-zA-Z0-9_-]+)['\"]",  # Broader pattern for print/log messages
            r"\[ERROR\].*No module named ['\"]?([a-zA-Z0-9_-]+)['\"]?",  # Matches [ERROR] prefix
            r"Error: Package ['\"]?([a-zA-Z0-9_-]+)['\"]? not found"
        ],
        ErrorType.GPU_OOM: [
            r"CUDA out of memory",
            r"RuntimeError: out of memory",
            r"Allocation of ([0-9.]+)([KMGT]?)B exceeds"
        ],
        ErrorType.NETWORK_TIMEOUT: [
            r"timeout|timed out",
            r"ConnectionError|Connection refused",
            r"Failed to connect|Network is unreachable"
        ],
        ErrorType.SYNTAX_ERROR: [
            r"SyntaxError: (.+)",
            r"IndentationError: (.+)",
            r"NameError: name ['\"]([^'\"]+)['\"] is not defined"
        ],
        ErrorType.SSH_AUTH_FAILURE: [
            r"AuthenticationException|Authentication failed",
            r"Permission denied \(publickey\)",
            r"Host key verification failed"
        ]
    }
    
    @staticmethod
    def analyze_line(log_line: str) -> Optional[ErrorReport]:
        """
        Analyzes a single log line for errors.
        Returns ErrorReport if error detected, None otherwise.
        """
        for error_type, patterns in ErrorDetector.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, log_line, re.IGNORECASE)
                if match:
                    return ErrorDetector._create_report(
                        error_type, 
                        log_line, 
                        match
                    )
        return None
    
    @staticmethod
    def _create_report(
        error_type: ErrorType, 
        log_line: str, 
        match: re.Match
    ) -> ErrorReport:
        """Creates a structured error report based on type."""
        
        if error_type == ErrorType.DEPENDENCY_MISSING:
            package = match.group(1) if match.lastindex else "unknown"
            return ErrorReport(
                type=error_type,
                severity="warning",
                message=f"Missing dependency: {package}",
                auto_fixable=True,
                context={"missing_package": package}
            )
        
        elif error_type == ErrorType.GPU_OOM:
            return ErrorReport(
                type=error_type,
                severity="critical",
                message="GPU out of memory",
                auto_fixable=False,  # Requires GPU upgrade or batch size reduction
                context={"suggestion": "reduce_batch_size_or_upgrade_gpu"}
            )
        
        elif error_type == ErrorType.NETWORK_TIMEOUT:
            return ErrorReport(
                type=error_type,
                severity="warning",
                message="Network connection timeout",
                auto_fixable=True,
                context={"retry_with_longer_timeout": True}
            )
        
        elif error_type == ErrorType.SYNTAX_ERROR:
            error_msg = match.group(1) if match.lastindex else log_line
            return ErrorReport(
                type=error_type,
                severity="critical",
                message=f"Syntax error in script: {error_msg}",
                auto_fixable=False,  # Requires code change
                context={"error_detail": error_msg}
            )
        
        elif error_type == ErrorType.SSH_AUTH_FAILURE:
            return ErrorReport(
                type=error_type,
                severity="critical",
                message="SSH authentication failed",
                auto_fixable=False,  # Requires new key
                context={"requires_user_action": True}
            )
        
        else:
            return ErrorReport(
                type=ErrorType.UNKNOWN,
                severity="info",
                message=log_line,
                auto_fixable=False,
                context={}
            )
    
    @staticmethod
    async def monitor_stream(
        log_stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[tuple[str, Optional[ErrorReport]], None]:
        """
        Monitors log stream and yields (log_line, error_report).
        If no error in line, error_report is None.
        """
        async for log_line in log_stream:
            error = ErrorDetector.analyze_line(log_line)
            yield (log_line, error)
