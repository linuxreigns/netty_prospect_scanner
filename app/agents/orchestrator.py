from app.scanner.crawler import ScanInput, scan_batch

from .agents import (
    CommercialQualificationAgent,
    CRMIntelligenceAgent,
    FollowUpAgent,
    NettySolutionArchitectAgent,
    OutreachAgent,
    PanamaValidationAgent,
    ProposalGeneratorAgent,
    ProspectDiscoveryAgent,
    TechnologyFingerprintAgent,
    WebsiteAuditAgent,
)
from .schemas import ProspectContext


class NettySalesEngineOrchestrator:
    def __init__(self):
        self.agent_chain = [
            ProspectDiscoveryAgent(),
            PanamaValidationAgent(),
            TechnologyFingerprintAgent(),
            WebsiteAuditAgent(),
            CommercialQualificationAgent(),
            NettySolutionArchitectAgent(),
            ProposalGeneratorAgent(),
            OutreachAgent(),
            FollowUpAgent(),
            CRMIntelligenceAgent(),
        ]

    async def run_for_url(self, url: str, rubro: str | None = None, provincia: str | None = None) -> dict:
        # 1) scan técnico base (fuente real)
        scanned = await scan_batch([ScanInput(url=url, rubro=rubro, provincia=provincia)])
        if not scanned:
            return {
                "ok": False,
                "message": "No fue posible escanear el sitio",
                "url": url,
                "agent_traces": [],
            }

        base = scanned[0]
        ctx = ProspectContext(url=base["url"], domain=base["domain"], rubro=rubro, provincia=provincia, analysis=base)

        # 2) cadena de agentes comerciales
        for agent in self.agent_chain:
            ctx = agent.run(ctx)

        return {
            "ok": True,
            "url": ctx.url,
            "domain": ctx.domain,
            "rubro": ctx.rubro,
            "provincia": ctx.provincia,
            "score": ctx.score,
            "classification": ctx.classification,
            "analysis": ctx.analysis,
            "recommendations": ctx.recommendations,
            "proposal": ctx.proposal,
            "outreach": ctx.outreach,
            "follow_up": ctx.follow_up,
            "agent_traces": [
                {
                    "agent": t.agent_name,
                    "status": t.status,
                    "summary": t.summary,
                    "output": t.output,
                }
                for t in ctx.traces
            ],
        }
