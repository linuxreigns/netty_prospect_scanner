from app.scoring.score_engine import compute_score

from .base import BaseAgent
from .schemas import AgentTrace, ProspectContext


class ProspectDiscoveryAgent(BaseAgent):
    name = "Prospect Discovery Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary="Prospecto recibido desde pipeline/discovery para análisis.",
                output={"url": ctx.url, "domain": ctx.domain},
            )
        )
        return ctx


class PanamaValidationAgent(BaseAgent):
    name = "Panama Validation Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        text_blob = " ".join(
            [
                str(ctx.analysis.get("title") or ""),
                str(ctx.analysis.get("meta_description") or ""),
                str(ctx.analysis.get("score_reasons") or ""),
            ]
        ).lower()

        signals = {
            "tld_pa": ctx.domain.endswith(".pa"),
            "phone_507": bool(ctx.analysis.get("has_phone")),
            "mentions_panama": any(k in text_blob for k in ["panamá", "panama", "+507", "yappy", "banco general"]),
            "provincia_hint": bool(ctx.provincia),
        }
        panama_score = sum(
            [
                30 if signals["tld_pa"] else 0,
                25 if signals["phone_507"] else 0,
                30 if signals["mentions_panama"] else 0,
                15 if signals["provincia_hint"] else 0,
            ]
        )
        ctx.analysis["panama_validation"] = {"score": panama_score, "signals": signals, "is_panama": panama_score >= 40}

        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary=f"Validación Panamá calculada: {panama_score}/100.",
                output=ctx.analysis["panama_validation"],
            )
        )
        return ctx


class TechnologyFingerprintAgent(BaseAgent):
    name = "Technology Fingerprint Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        tech = {
            "cms": ctx.analysis.get("cms"),
            "ecommerce_platform": ctx.analysis.get("ecommerce_platform"),
            "frontend_stack": ctx.analysis.get("frontend_stack"),
        }
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary="Fingerprint tecnológico consolidado.",
                output=tech,
            )
        )
        return ctx


class WebsiteAuditAgent(BaseAgent):
    name = "Website Audit Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        opps = []
        if not ctx.analysis.get("has_chatbot"):
            opps.append("No tiene chatbot visible")
        if ctx.analysis.get("has_whatsapp"):
            opps.append("Depende de WhatsApp manual")
        if ctx.analysis.get("has_contact_form"):
            opps.append("Tiene formulario: oportunidad de captura automática")
        if ctx.analysis.get("has_products_or_cart"):
            opps.append("Tiene eCommerce: oportunidad de ventas 24/7")
        if not ctx.analysis.get("has_clear_cta"):
            opps.append("CTA débil o no evidente")

        ctx.analysis["audit_opportunities"] = opps
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary=f"Audit detectó {len(opps)} oportunidades.",
                output={"opportunities": opps},
            )
        )
        return ctx


class CommercialQualificationAgent(BaseAgent):
    name = "Commercial Qualification Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        score, classification_es, reasons = compute_score(ctx.analysis)
        map_cls = {"Caliente": "HOT", "Bueno": "GOOD", "Medio": "MEDIUM", "Bajo": "LOW"}
        ctx.score = score
        ctx.classification = map_cls.get(classification_es, "LOW")
        ctx.analysis["score_reasons"] = " | ".join(reasons)
        ctx.analysis["fit_classification"] = classification_es
        ctx.analysis["netty_fit_score"] = score

        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary=f"Score comercial calculado: {score} ({ctx.classification}).",
                output={"score": score, "classification": ctx.classification, "reasons": reasons},
            )
        )
        return ctx


class NettySolutionArchitectAgent(BaseAgent):
    name = "Netty Solution Architect Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        rubro = (ctx.rubro or "negocio").lower()
        recs = [
            f"Automatizar atención inicial para {rubro} con respuestas instantáneas.",
            "Capturar leads desde web/WhatsApp en un flujo unificado.",
            "Activar seguimiento comercial automático con recordatorios y CRM.",
        ]
        if ctx.analysis.get("has_products_or_cart"):
            recs.append("Asistente de ventas para recuperación de carritos y preguntas de compra.")
        if not ctx.analysis.get("has_chatbot"):
            recs.append("Implementar chatbot de ventas y soporte 24/7 como canal principal.")

        ctx.recommendations = recs
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary="Arquitectura de solución Netty generada por rubro y señales.",
                output={"recommendations": recs},
            )
        )
        return ctx


class ProposalGeneratorAgent(BaseAgent):
    name = "Proposal Generator Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        proposal = {
            "audit_summary": f"El ecosistema NETTY SALES ENGINE auditó automáticamente {ctx.domain} y detectó oportunidades comerciales.",
            "value_points": ctx.recommendations,
            "plan_recommendation": "Business" if ctx.score >= 80 else "Pro" if ctx.score >= 60 else "Starter",
            "pitch": f"Netty puede transformar la atención y conversión de {ctx.domain} con operación asistida por IA 24/7.",
        }
        ctx.proposal = proposal
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary="Propuesta comercial inicial generada.",
                output=proposal,
            )
        )
        return ctx


class OutreachAgent(BaseAgent):
    name = "Outreach Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        first_msg = (
            f"Hola, te escribo desde Netty. Nuestro ecosistema IA analizó automáticamente {ctx.domain} "
            "y encontramos oportunidades claras para mejorar captación y atención. "
            "¿Te comparto una auditoría breve personalizada?"
        )
        email = (
            f"Asunto: Auditoría automática de oportunidades para {ctx.domain}\n\n"
            f"Hola,\n\n"
            f"El ecosistema NETTY SALES ENGINE analizó su sitio de forma automatizada y detectó oportunidades para "
            f"mejorar ventas, soporte y captura de leads.\n\n"
            f"Clasificación actual: {ctx.classification} (score {ctx.score}/100).\n"
            f"¿Le compartimos una propuesta breve con acciones concretas?"
        )
        ctx.outreach = {"whatsapp_draft": first_msg, "email_draft": email, "send_mode": "manual_approval_required"}
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary="Mensajes de outreach preparados (sin envío automático).",
                output=ctx.outreach,
            )
        )
        return ctx


class FollowUpAgent(BaseAgent):
    name = "Follow-Up Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        ctx.follow_up = {
            "next_steps": [
                "Día 2: reenviar resumen de auditoría con caso de uso por rubro",
                "Día 5: enviar propuesta de plan y ROI esperado",
                "Día 10: cierre suave con invitación a demo",
            ],
            "status": "pending_first_contact",
        }
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary="Secuencia de seguimiento creada.",
                output=ctx.follow_up,
            )
        )
        return ctx


class CRMIntelligenceAgent(BaseAgent):
    name = "CRM Intelligence Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        crm_view = {
            "stage": "qualified" if ctx.score >= 60 else "nurturing",
            "priority": "high" if ctx.classification == "HOT" else "normal",
            "tags": [
                ctx.classification,
                "sin_chatbot" if not ctx.analysis.get("has_chatbot") else "con_chatbot",
                "con_whatsapp" if ctx.analysis.get("has_whatsapp") else "sin_whatsapp",
            ],
        }
        ctx.analysis["crm"] = crm_view
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary="Clasificación CRM operacional calculada.",
                output=crm_view,
            )
        )
        return ctx
