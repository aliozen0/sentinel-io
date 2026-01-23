"""
io-Guard v1.5 - Operational Chat Agent (OpsAgent)
=================================================

Sadece sohbet etmeyen, aksiyon alan ajan. Mevcut ChatAgent'ın yanına eklenen yeni yetenek.

TOOL USE (Araç Kullanımı):
- "Bakiyem ne kadar?" → db.get_credits(user_id)
- Teknik soru → MemoryCore.search(query) ile RAG'dan ara
- "Job ID: 123'ü durdur" → stop_job(job_id) simülasyonu
- "Son analizi özetle" → state.last_analysis bilgisini yorumla
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from state_manager import state
from ai_client import ask_io_intelligence_async
from db.client import get_db
from services.memory_core import MemoryCore

logger = logging.getLogger("OpsAgent")


class ToolType(Enum):
    """Kullanılabilir araç tipleri."""
    GET_BALANCE = "get_balance"
    RAG_SEARCH = "rag_search"
    STOP_JOB = "stop_job"
    GET_ANALYSIS = "get_analysis"
    GET_JOB_STATUS = "get_job_status"
    NONE = "none"


@dataclass
class ToolResult:
    """Araç çağrısı sonucu."""
    tool: ToolType
    success: bool
    data: Any
    message: str


class OpsAgent:
    """
    Operational Chat Agent.
    
    Kullanıcı isteklerini analiz eder, gerekirse araç çağrıları yapar,
    ve sonuçları LLM ile zenginleştirir.
    """
    
    SYSTEM_PROMPT = """Sen io-Guard Operasyonel Asistanısın.
Kullanıcının isteklerini anlayıp aksiyon alabilirsin.

YETENEKLERİN:
1. Bakiye Sorgulama: Kullanıcının kredi bakiyesini sorgulayabilirsin.
2. Bilgi Arama (RAG): Yüklenen dokümanlarda arama yapabilirsin.
3. Job Yönetimi: Çalışan işleri sorgulayabilir, durdurabilirsin.
4. Analiz Özeti: Son kod analizi sonuçlarını özetleyebilirsin.

KURALLAR:
- Araç sonuçlarını doğal ve anlaşılır şekilde açıkla
- Teknik detayları basitleştir
- Türkçe veya İngilizce yanıt ver (kullanıcının diline göre)
- Hata durumlarında yardımcı ol

SYSTEM_DATA bölümünde sana araç sonuçları verilecek. Bu bilgileri kullan.
"""

    # Intent detection patterns
    INTENT_PATTERNS = {
        ToolType.GET_BALANCE: [
            r"bakiye", r"kredi", r"credit", r"balance", r"para", r"money",
            r"ne kadar (param|kredim|bakiyem)", r"how much"
        ],
        ToolType.STOP_JOB: [
            r"durdur", r"stop", r"iptal", r"cancel", r"kapat", r"kill",
            r"job.*durdur", r"job.*stop"
        ],
        ToolType.GET_ANALYSIS: [
            r"son analiz", r"last analysis", r"analiz sonucu", r"analysis result",
            r"özet", r"summary", r"ne önerdin", r"recommendation"
        ],
        ToolType.GET_JOB_STATUS: [
            r"job durumu", r"job status", r"is.*running", r"çalışıyor mu",
            r"job.*ne oldu"
        ]
    }
    
    @staticmethod
    def _detect_intent(message: str) -> Tuple[ToolType, Optional[str]]:
        """
        Kullanıcı mesajından intent ve parametreleri çıkarır.
        
        Returns:
            (ToolType, optional_param) - örn: (STOP_JOB, "job-123")
        """
        message_lower = message.lower()
        
        for tool_type, patterns in OpsAgent.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    # Parametreleri çıkar
                    param = None
                    
                    if tool_type == ToolType.STOP_JOB:
                        # Job ID çıkar: "job-123", "123", "Job ID: abc"
                        job_match = re.search(r"(?:job\s*(?:id)?:?\s*)?([a-zA-Z0-9\-_]+)", message, re.IGNORECASE)
                        if job_match:
                            param = job_match.group(1)
                    
                    return tool_type, param
        
        # Hiçbir intent eşleşmediyse, RAG search dene (teknik sorular için)
        # Anahtar kelimeler: GPU, VRAM, error, hata, nasıl, how, what, nedir
        rag_triggers = [
            r"nasıl", r"how", r"what", r"nedir", r"ne demek",
            r"gpu", r"vram", r"error", r"hata", r"problem",
            r"çözüm", r"solution", r"fix", r"docker", r"tensorflow",
            r"pytorch", r"cuda", r"memory", r"bellek"
        ]
        
        for trigger in rag_triggers:
            if re.search(trigger, message_lower):
                return ToolType.RAG_SEARCH, message
        
        return ToolType.NONE, None
    
    @staticmethod
    async def _execute_tool(
        tool: ToolType, 
        param: Optional[str], 
        user_id: str
    ) -> ToolResult:
        """Belirlenen aracı çalıştırır."""
        
        try:
            if tool == ToolType.GET_BALANCE:
                db = get_db()
                credits = db.get_credits(user_id)
                return ToolResult(
                    tool=tool,
                    success=True,
                    data={"credits": credits},
                    message=f"Kullanıcının mevcut bakiyesi: ${credits:.2f}"
                )
            
            elif tool == ToolType.RAG_SEARCH:
                if param:
                    results = await MemoryCore.search(param, top_k=3)
                    if results:
                        return ToolResult(
                            tool=tool,
                            success=True,
                            data={"results": results},
                            message=f"RAG'dan {len(results)} sonuç bulundu"
                        )
                    else:
                        return ToolResult(
                            tool=tool,
                            success=True,
                            data={"results": []},
                            message="Bilgi tabanında ilgili sonuç bulunamadı"
                        )
                return ToolResult(
                    tool=tool,
                    success=False,
                    data=None,
                    message="Arama sorgusu belirtilmedi"
                )
            
            elif tool == ToolType.STOP_JOB:
                # Simülasyon - gerçek implementasyonda JobManager kullanılır
                job_id = param or "unknown"
                logger.info(f"[SIMULATION] Stopping job: {job_id}")
                return ToolResult(
                    tool=tool,
                    success=True,
                    data={"job_id": job_id, "status": "stopped"},
                    message=f"Job '{job_id}' durdurma komutu gönderildi (simülasyon)"
                )
            
            elif tool == ToolType.GET_ANALYSIS:
                if state.last_analysis:
                    analysis = state.last_analysis
                    summary = {
                        "framework": analysis.get("summary", {}).get("framework", "Unknown"),
                        "vram_required": analysis.get("summary", {}).get("vram_required", "Unknown"),
                        "health_score": analysis.get("summary", {}).get("health_score", "N/A"),
                        "recommended_gpu": analysis.get("summary", {}).get("recommended_gpu", "N/A"),
                        "critical_issues": len(analysis.get("audit", {}).get("critical_issues", [])),
                    }
                    
                    # Top market recommendation
                    if analysis.get("market_recommendations"):
                        top = analysis["market_recommendations"][0]
                        summary["top_match"] = {
                            "gpu": top.get("gpu_model"),
                            "price": top.get("price_hourly"),
                            "score": top.get("score")
                        }
                    
                    return ToolResult(
                        tool=tool,
                        success=True,
                        data=summary,
                        message="Son analiz sonuçları alındı"
                    )
                else:
                    return ToolResult(
                        tool=tool,
                        success=False,
                        data=None,
                        message="Henüz bir analiz yapılmamış"
                    )
            
            elif tool == ToolType.GET_JOB_STATUS:
                # Basit job durumu sorgulama
                return ToolResult(
                    tool=tool,
                    success=True,
                    data={"active_jobs": 0, "completed_jobs": 0},  # Placeholder
                    message="Job durumu sorgulandı"
                )
            
            else:
                return ToolResult(
                    tool=ToolType.NONE,
                    success=True,
                    data=None,
                    message="Standart sohbet modu"
                )
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(
                tool=tool,
                success=False,
                data=None,
                message=f"Araç hatası: {str(e)}"
            )
    
    @staticmethod
    async def chat(
        messages: List[Dict[str, str]], 
        user_id: str,
        model: str = None
    ) -> str:
        """
        Operasyonel sohbet - araç kullanımı ile zenginleştirilmiş.
        
        Args:
            messages: Sohbet geçmişi [{"role": "user/assistant", "content": "..."}]
            user_id: Kullanıcı ID'si (bakiye vb. için)
            model: Kullanılacak AI modeli
        
        Returns:
            AI yanıtı
        """
        try:
            # Son mesajı al
            last_message = messages[-1]["content"] if messages else ""
            
            # Intent tespit et
            intent, param = OpsAgent._detect_intent(last_message)
            logger.info(f"Detected intent: {intent.value}, param: {param}")
            
            # Aracı çalıştır
            tool_result = await OpsAgent._execute_tool(intent, param, user_id)
            
            # System prompt'a araç sonuçlarını ekle
            system_data = f"""
SYSTEM_DATA (Araç Sonuçları):
- Tool: {tool_result.tool.value}
- Success: {tool_result.success}
- Message: {tool_result.message}
- Data: {json.dumps(tool_result.data, ensure_ascii=False, default=str) if tool_result.data else 'None'}

PROJE DURUMU:
"""
            
            # Ek context ekle
            if state.last_analysis:
                system_data += f"""
- Son Analiz: Framework={state.last_analysis.get('summary', {}).get('framework', 'N/A')}, VRAM={state.last_analysis.get('summary', {}).get('vram_required', 'N/A')}
"""
            else:
                system_data += "- Son Analiz: Henüz yapılmadı\n"
            
            # Recent agent logs
            recent_logs = state.get_agent_logs(limit=3)
            if recent_logs:
                system_data += "- Son Aktiviteler:\n"
                for log in recent_logs:
                    system_data += f"  - {log.get('agent', 'System')}: {log.get('action', log.get('message', 'N/A'))}\n"
            
            full_system_prompt = f"{OpsAgent.SYSTEM_PROMPT}\n\n{system_data}"
            
            # Sohbet geçmişini formatla
            history_context = ""
            if len(messages) > 1:
                history_context = "CONVERSATION HISTORY:\n"
                for m in messages[:-1]:
                    history_context += f"{m['role'].upper()}: {m['content']}\n"
            
            final_user_prompt = f"{history_context}\nUSER: {last_message}"
            
            # LLM çağır
            response = await ask_io_intelligence_async(
                system_prompt=full_system_prompt,
                user_prompt=final_user_prompt,
                model=model
            )
            
            return response
            
        except Exception as e:
            logger.error(f"OpsAgent chat error: {e}")
            return f"Üzgünüm, bir hata oluştu: {str(e)}"
    
    @staticmethod
    async def quick_search(query: str) -> List[Dict[str, Any]]:
        """
        Hızlı RAG araması (diğer ajanlar için utility).
        
        Returns:
            RAG sonuçları listesi
        """
        try:
            results = await MemoryCore.search(query, top_k=3)
            return results
        except Exception as e:
            logger.error(f"Quick search error: {e}")
            return []
