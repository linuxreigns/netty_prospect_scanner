from dataclasses import dataclass


@dataclass
class SectorTemplate:
    sector: str
    pitch: str
    email_subject: str
    email_body: str
    whatsapp_message: str
    follow_up_48h: str


TEMPLATES: dict[str, SectorTemplate] = {
    "restaurantes": SectorTemplate(
        sector="restaurantes",
        pitch="Automatiza reservas, preguntas frecuentes y captura de leads por WhatsApp.",
        email_subject="Auditoría automática de atención digital para tu restaurante",
        email_body="Hola, nuestro ecosistema IA analizó automáticamente tu sitio y detectó oportunidades para mejorar respuesta a clientes, reservas y seguimiento comercial.",
        whatsapp_message="Hola 👋 analizamos automáticamente su sitio y vimos oportunidades para responder clientes más rápido y captar más reservas con Netty.",
        follow_up_48h="Retomamos: ¿te compartimos una demo de 15 min con mejoras concretas para reservas/atención?",
    ),
    "clinicas": SectorTemplate(
        sector="clinicas",
        pitch="Centraliza consultas, triage inicial y agendamiento con respuesta inmediata.",
        email_subject="Auditoría IA de experiencia paciente y agendamiento",
        email_body="Hola, el motor comercial de Netty detectó oportunidades para mejorar tiempos de respuesta y agendamiento desde web/WhatsApp.",
        whatsapp_message="Hola 👋 revisamos su presencia digital y vimos oportunidades para automatizar agendamiento y dudas frecuentes con Netty.",
        follow_up_48h="¿Te mostramos cómo reducir tiempos de respuesta y mejorar la conversión de consultas?",
    ),
}


def get_template_for_sector(sector: str | None) -> SectorTemplate:
    key = (sector or "").strip().lower()
    return TEMPLATES.get(
        key,
        SectorTemplate(
            sector=key or "general",
            pitch="Automatiza atención, soporte y captura de leads con trazabilidad comercial.",
            email_subject="Auditoría automática de oportunidades comerciales",
            email_body="Hola, analizamos automáticamente tu sitio y detectamos oportunidades para mejorar atención y conversión.",
            whatsapp_message="Hola 👋 hicimos una auditoría automática de su sitio y detectamos oportunidades de automatización comercial con Netty.",
            follow_up_48h="¿Coordinamos una demo breve para mostrar oportunidades detectadas?",
        ),
    )
