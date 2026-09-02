import os
from fpdf import FPDF
from datetime import datetime

def clean_pdf_text(text) -> str:
    if not text:
        return ""
    text_str = str(text)
    replacements = {
        "\u2011": "-", "\u2013": "-", "\u2014": "--",
        "\u2018": "'", "\u2019": "'", "\u201c": '"',
        "\u201d": '"', "\u2022": "*", "\u2026": "...",
        "\u2027": "-", "\u2010": "-", "•": "|",
    }
    for k, v in replacements.items():
        text_str = text_str.replace(k, v)
    return text_str.encode("latin-1", errors="replace").decode("latin-1")

class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(15, 23, 42)  # Solid Black
        self.cell(0, 7, "FREELANCEFLOW PROGRESS REPORT", border=0, align="L")
        self.ln(7)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(71, 85, 105)  # Slate
        self.cell(0, 5, "Verified Contract Progress & Delivery Summary", border=0, align="L")
        self.ln(6)
        y_line = self.get_y()
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.4)
        self.line(15, y_line, 195, y_line)
        self.ln(4)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, f"* Note: Compiled by FreelanceFlow AI | Verified by Freelancer (Page {self.page_no()})", border=0, align="C")

def generate():
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    # Metadata Info Card (Solid Black & Gray tones)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(32, 7, "Project Title:", border="LT", fill=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(148, 7, "Modern E-commerce Landing Page", border="TR", fill=True)
    pdf.ln(7)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(32, 6, "Client:", border="L", fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(58, 6, "Alex Morgan", border=0, fill=True)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(32, 6, "Freelancer:", border=0, fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(58, 6, "Sayandip Bar", border="R", fill=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(32, 6, "Hours Logged:", border="LB", fill=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(58, 6, "12.00 hrs", border="B", fill=True)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(32, 6, "Date Generated:", border="B", fill=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(58, 6, datetime.now().strftime("%B %d, %Y"), border="RB", fill=True)
    pdf.ln(6)

    pdf.ln(5)

    # 1. Executive Summary
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "1. Executive Summary", align="L")
    pdf.ln(6)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    y_s1 = pdf.get_y()
    pdf.line(15, y_s1, 195, y_s1)
    pdf.ln(3)

    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    summary_text = (
        "Completed the foundational layout and responsive architecture for the landing page. "
        "The header navigation, hero banner, category showcases, promotional blocks, and footer "
        "have been structured and verified across mobile and desktop viewports."
    )
    pdf.multi_cell(180, 5, summary_text)
    pdf.ln(4)

    # 2. Deliverables & Milestones Completed
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "2. Deliverables & Milestones Completed", align="L")
    pdf.ln(6)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    y_s2 = pdf.get_y()
    pdf.line(15, y_s2, 195, y_s2)
    pdf.ln(3)

    deliverables = [
        {
            "title": "Navigation & Responsive Header",
            "status": "COMPLETED",
            "desc": "Implemented fixed sticky navbar with desktop navigation links and responsive mobile drawer menu."
        },
        {
            "title": "Hero Section & Product Scaffolding",
            "status": "COMPLETED",
            "desc": "Built call-to-action hero banner, featured category cards, and responsive product grid scaffolding."
        }
    ]

    for d in deliverables:
        pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, f"* {d['title']}  [{d['status']}]")
        pdf.ln(5)

        pdf.set_x(20)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(170, 4.5, d["desc"])
        pdf.ln(2)

    pdf.ln(3)

    # 3. Next Steps & Upcoming Priorities
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, "3. Next Steps & Upcoming Priorities", align="L")
    pdf.ln(6)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    y_s3 = pdf.get_y()
    pdf.line(15, y_s3, 195, y_s3)
    pdf.ln(3)

    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    next_steps = (
        "1. Apply visual polish, typography tokens, and color styling for Milestone 2.\n"
        "2. Replace mock items with dynamic catalog data and category filtering.\n"
        "3. Review responsive breakpoints and submit for client deliverable approval."
    )
    pdf.multi_cell(180, 5, next_steps)

    out_path = os.path.abspath("frontend/public/demo_progress_report.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pdf.output(out_path)
    print(f"Generated demo PDF at: {out_path}")

if __name__ == "__main__":
    generate()
