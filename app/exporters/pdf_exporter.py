from fpdf import FPDF


def export_summary_pdf(summary: dict, output_path: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Netty Prospect Scanner - Resumen", ln=True)
    pdf.ln(4)
    for k, v in summary.items():
        pdf.multi_cell(0, 8, f"{k}: {v}")
    pdf.output(output_path)
    return output_path
