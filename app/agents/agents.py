from app.ai.commercial_analysis import generate_outreach_with_ai, generate_proposal_with_ai
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
        a = ctx.analysis
        opps = []

        # Chatbot / atención
        if not a.get("has_chatbot"):
            opps.append("No tiene chatbot visible — atención 24/7 manual")
        if a.get("has_whatsapp"):
            opps.append("Depende de WhatsApp manual — sin automatización")

        # Formularios y CRM
        if a.get("has_contact_form") and not a.get("has_crm_form"):
            opps.append("Formulario sin CRM integrado — leads sin captura automática")
        elif a.get("has_contact_form") and a.get("has_crm_form"):
            opps.append(
                f"CRM parcial ({a.get('crm_form_vendor', 'detectado')}) — integración Netty amplía automatización"
            )

        # eCommerce
        if a.get("has_products_or_cart"):
            opps.append("Tiene eCommerce — oportunidad de asistente de ventas 24/7")

        # CTA
        if not a.get("has_clear_cta"):
            opps.append("CTA débil o no evidente — baja conversión")

        # SEO
        if not a.get("meta_description") or (a.get("meta_desc_length", 0) < 50):
            opps.append("Sin meta descripción SEO — visibilidad en Google subóptima")
        if not a.get("has_h1"):
            opps.append("Sin H1 — estructura de página débil para SEO")
        if not a.get("has_og_tags"):
            opps.append("Sin Open Graph — vistas en redes sociales sin optimizar")

        # Velocidad
        speed = a.get("load_speed_tier", "ok")
        if speed == "slow":
            opps.append("Carga lenta (2.5–5 s) — afecta conversión y SEO")
        elif speed == "very_slow":
            opps.append("Carga muy lenta (>5 s) — abandono alto de usuarios")

        # Redes sociales
        if a.get("social_count", 0) == 0:
            opps.append("Sin redes sociales detectadas — alcance orgánico limitado")

        ctx.analysis["audit_opportunities"] = opps
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary=f"Audit detectó {len(opps)} oportunidades (SEO, velocidad, CRM, redes).",
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
        cms = ctx.analysis.get("cms") or "no detectado"
        ecommerce = ctx.analysis.get("ecommerce_platform") or "ninguno"
        opps = ctx.analysis.get("audit_opportunities") or []
        plan = "Business" if ctx.score >= 80 else "Pro" if ctx.score >= 60 else "Starter"
        rubro_str = ctx.rubro or "su sector"

        ctx_dict = {
            "domain": ctx.domain,
            "rubro": ctx.rubro,
            "cms": cms,
            "ecommerce": ecommerce,
            "score": ctx.score,
            "classification": ctx.classification,
            "has_chatbot": ctx.analysis.get("has_chatbot", False),
            "has_whatsapp": ctx.analysis.get("has_whatsapp", False),
            "has_ecommerce": bool(ctx.analysis.get("has_products_or_cart")),
            "opportunities": opps,
            "recommendations": ctx.recommendations,
        }
        ai_result = generate_proposal_with_ai(ctx_dict)

        if ai_result:
            proposal = {
                "audit_summary": ai_result.get("audit_summary", ""),
                "value_proposition": ai_result.get("value_proposition", ""),
                "tech_detected": {"cms": cms, "ecommerce": ecommerce},
                "opportunities": opps,
                "value_points": ctx.recommendations,
                "plan_recommendation": ai_result.get("plan_recommendation", plan),
                "plan_justification": ai_result.get("plan_justification", ""),
                "pitch": ai_result.get("pitch", ""),
                "meta_note": ai_result.get("meta_note", ""),
                "ai_generated": True,
            }
        else:
            tech_line = f"Stack detectado: {cms}" + (f" + {ecommerce}" if ecommerce != "ninguno" else "")
            opps_text = "; ".join(opps) if opps else "múltiples oportunidades de automatización"
            audit_summary = (
                f"NETTY SALES ENGINE descubrió, visitó y auditó {ctx.domain} de forma completamente autónoma. "
                f"Clasificación: {ctx.classification} ({ctx.score}/100). "
                f"{tech_line}. "
                f"Oportunidades detectadas: {opps_text}."
            )
            pitch = (
                f"Netty puede transformar {rubro_str} como {ctx.domain}: "
                f"atención automática 24/7, captura de leads, seguimiento IA y ventas sin fricción. "
                f"Plan recomendado: {plan}."
            )
            proposal = {
                "audit_summary": audit_summary,
                "tech_detected": {"cms": cms, "ecommerce": ecommerce},
                "opportunities": opps,
                "value_points": ctx.recommendations,
                "plan_recommendation": plan,
                "pitch": pitch,
                "meta_note": "Esta propuesta fue generada automáticamente por el ecosistema Netty Sales Engine — el mismo sistema que Netty utiliza para sus clientes.",
                "ai_generated": False,
            }

        ctx.proposal = proposal
        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary=f"Propuesta generada para {ctx.domain} (plan {proposal['plan_recommendation']}, IA={'sí' if ai_result else 'no'}).",
                output=proposal,
            )
        )
        return ctx


class OutreachAgent(BaseAgent):
    name = "Outreach Agent"

    def run(self, ctx: ProspectContext) -> ProspectContext:
        opps = ctx.analysis.get("audit_opportunities") or []
        top_opp = opps[0] if opps else "oportunidades de automatización"
        cms = ctx.analysis.get("cms") or "su plataforma web"
        rubro_str = ctx.rubro or "su negocio"

        ctx_dict = {
            "domain": ctx.domain,
            "rubro": ctx.rubro,
            "cms": cms,
            "score": ctx.score,
            "classification": ctx.classification,
            "has_chatbot": ctx.analysis.get("has_chatbot", False),
            "opportunities": opps,
        }
        ai_result = generate_outreach_with_ai(ctx_dict)

        if ai_result:
            ctx.outreach = {
                "whatsapp_draft": ai_result.get("whatsapp_draft", ""),
                "email_subject": ai_result.get("email_subject", ""),
                "email_draft": ai_result.get("email_body", ""),
                "send_mode": "manual_approval_required",
                "personalization": {"domain": ctx.domain, "score": ctx.score, "top_opportunity": top_opp},
                "ai_generated": True,
            }
        else:
            first_msg = (
                f"Hola, te escribo desde Netty. "
                f"Nuestro ecosistema IA descubrió y analizó {ctx.domain} automáticamente. "
                f"Detectamos: {top_opp}. "
                f"¿Te comparto la auditoría completa? Es gratis y específica para {rubro_str}."
            )
            email = (
                f"Asunto: Auditoría automática de {ctx.domain} — {ctx.classification} ({ctx.score}/100)\n\n"
                f"Hola,\n\n"
                f"El ecosistema NETTY SALES ENGINE identificó, visitó y auditó {ctx.domain} de forma autónoma.\n\n"
                f"Hallazgos principales:\n"
                + "".join(f"  • {o}\n" for o in (opps or ["Oportunidades de automatización detectadas"]))
                + f"\nTecnología detectada: {cms}.\n"
                f"Score Netty Fit: {ctx.score}/100 — clasificado como {ctx.classification}.\n\n"
                f"Este análisis fue realizado automáticamente por el mismo motor IA que impulsa Netty.\n"
                f"¿Le mostramos cómo Netty puede cubrir estas brechas en {rubro_str}?"
            )
            ctx.outreach = {
                "whatsapp_draft": first_msg,
                "email_draft": email,
                "send_mode": "manual_approval_required",
                "personalization": {"domain": ctx.domain, "score": ctx.score, "top_opportunity": top_opp},
                "ai_generated": False,
            }

        ctx.add_trace(
            AgentTrace(
                agent_name=self.name,
                status="done",
                summary=f"Outreach generado para {ctx.domain} ({len(opps)} oportunidades, IA={'sí' if ai_result else 'no'}).",
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
