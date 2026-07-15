from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Russell_York_Recent_AI_Engineering_Project_Record.pdf"

NAVY = colors.HexColor("#0B172A")
NAVY_2 = colors.HexColor("#13233A")
BLUE = colors.HexColor("#2563EB")
TEAL = colors.HexColor("#0F9F8F")
AMBER = colors.HexColor("#D97706")
GREEN = colors.HexColor("#15803D")
INK = colors.HexColor("#172033")
SLATE = colors.HexColor("#475569")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#CBD5E1")
LIGHT = colors.HexColor("#F1F5F9")
PALE_BLUE = colors.HexColor("#EFF6FF")
PALE_TEAL = colors.HexColor("#ECFDF5")
WHITE = colors.white


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#7DD3FC"),
            tracking=1.4,
            spaceAfter=16,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=31,
            leading=35,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=18,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=13,
            leading=19,
            textColor=colors.HexColor("#D7E4F4"),
            spaceAfter=22,
        ),
        "cover_name": ParagraphStyle(
            "cover_name",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            textColor=WHITE,
            spaceAfter=4,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#AFC2D9"),
        ),
        "kicker": ParagraphStyle(
            "kicker",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=BLUE,
            tracking=1.1,
            spaceAfter=5,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=NAVY,
            spaceBefore=0,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=13.2,
            textColor=INK,
            spaceAfter=7,
        ),
        "body_small": ParagraphStyle(
            "body_small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.7,
            leading=10.5,
            textColor=SLATE,
            spaceAfter=4,
        ),
        "callout": ParagraphStyle(
            "callout",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=14,
            textColor=NAVY,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=NAVY,
            spaceAfter=4,
        ),
        "card_body": ParagraphStyle(
            "card_body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10.7,
            textColor=SLATE,
        ),
        "metric": ParagraphStyle(
            "metric",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=17,
            textColor=BLUE,
            alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "metric_label",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=SLATE,
            alignment=TA_CENTER,
        ),
        "link": ParagraphStyle(
            "link",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=BLUE,
        ),
        "source": ParagraphStyle(
            "source",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=9,
            textColor=MUTED,
            spaceAfter=3,
        ),
    }


STYLES = build_styles()


class AccentRule(Flowable):
    def __init__(self, width: float = 72, color: colors.Color = TEAL, thickness: float = 4):
        super().__init__()
        self.width = width
        self.height = thickness
        self.color = color
        self.thickness = thickness

    def draw(self) -> None:
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.thickness, self.thickness / 2, fill=1, stroke=0)


class PipelineFlow(Flowable):
    def __init__(self, labels: list[str], width: float = 510, height: float = 82):
        super().__init__()
        self.labels = labels
        self.width = width
        self.height = height

    def draw(self) -> None:
        count = len(self.labels)
        gap = 17
        box_width = (self.width - gap * (count - 1)) / count
        y = 22
        box_height = 44
        for index, label in enumerate(self.labels):
            x = index * (box_width + gap)
            self.canv.setFillColor(PALE_BLUE if index % 2 == 0 else PALE_TEAL)
            self.canv.setStrokeColor(colors.HexColor("#B7C8DE"))
            self.canv.roundRect(x, y, box_width, box_height, 7, fill=1, stroke=1)
            self.canv.setFillColor(NAVY)
            self.canv.setFont("Helvetica-Bold", 7.5)
            words = label.split()
            lines: list[str] = []
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if stringWidth(candidate, "Helvetica-Bold", 7.5) > box_width - 12 and current:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
            line_y = y + box_height / 2 + (len(lines) - 1) * 4.5
            for line in lines[:3]:
                self.canv.drawCentredString(x + box_width / 2, line_y, line)
                line_y -= 9
            if index < count - 1:
                arrow_start = x + box_width + 3
                arrow_end = x + box_width + gap - 3
                arrow_y = y + box_height / 2
                self.canv.setStrokeColor(TEAL)
                self.canv.setFillColor(TEAL)
                self.canv.setLineWidth(1.4)
                self.canv.line(arrow_start, arrow_y, arrow_end, arrow_y)
                self.canv.line(arrow_end - 4, arrow_y + 3, arrow_end, arrow_y)
                self.canv.line(arrow_end - 4, arrow_y - 3, arrow_end, arrow_y)


class ComparisonBars(Flowable):
    def __init__(self, groups: list[tuple[str, float, float]], width: float = 500, height: float = 130):
        super().__init__()
        self.groups = groups
        self.width = width
        self.height = height

    def draw(self) -> None:
        left = 105
        usable = self.width - left - 44
        self.canv.setFont("Helvetica", 7)
        self.canv.setFillColor(MUTED)
        for tick in range(0, 11, 2):
            x = left + usable * tick / 10
            self.canv.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.canv.line(x, 18, x, self.height - 12)
            self.canv.drawCentredString(x, 7, f"{tick / 10:.1f}")
        row_y = self.height - 32
        for label, model, baseline in self.groups:
            self.canv.setFillColor(NAVY)
            self.canv.setFont("Helvetica-Bold", 8)
            self.canv.drawRightString(left - 10, row_y + 6, label)
            self.canv.setFillColor(BLUE)
            self.canv.roundRect(left, row_y + 5, usable * model, 10, 3, fill=1, stroke=0)
            self.canv.setFillColor(AMBER)
            self.canv.roundRect(left, row_y - 9, usable * baseline, 10, 3, fill=1, stroke=0)
            self.canv.setFillColor(INK)
            self.canv.setFont("Helvetica", 7)
            self.canv.drawString(left + usable * model + 5, row_y + 7, f"{model:.3f}")
            self.canv.drawString(left + usable * baseline + 5, row_y - 7, f"{baseline:.3f}")
            row_y -= 48
        self.canv.setFont("Helvetica-Bold", 7)
        self.canv.setFillColor(BLUE)
        self.canv.drawString(left, self.height - 5, "Selected model")
        self.canv.setFillColor(AMBER)
        self.canv.drawString(left + 86, self.height - 5, "Naive baseline")


def page_chrome(canvas, doc) -> None:
    page = doc.page
    width, height = letter
    canvas.saveState()
    if page == 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#1C3858"))
        canvas.setLineWidth(1)
        for offset in range(-160, 420, 58):
            canvas.line(offset, 0, offset + 260, height)
        canvas.setFillColor(TEAL)
        canvas.rect(0, height - 9, width, 9, fill=1, stroke=0)
        canvas.setFillColor(BLUE)
        canvas.rect(width - 120, 0, 120, 8, fill=1, stroke=0)
    else:
        canvas.setFillColor(WHITE)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(42, height - 34, width - 42, height - 34)
        canvas.line(42, 30, width - 42, 30)
        canvas.setFont("Helvetica-Bold", 7.2)
        canvas.setFillColor(NAVY)
        canvas.drawString(42, height - 25, "RUSSELL YORK  |  RECENT AI ENGINEERING PROJECT RECORD")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(42, 18, "Portfolio evidence - July 2026")
        canvas.drawRightString(width - 42, 18, f"Page {page}")
    canvas.restoreState()


def section_heading(kicker: str, title: str, subtitle: str | None = None) -> list:
    items = [Paragraph(kicker.upper(), STYLES["kicker"]), Paragraph(title, STYLES["h1"])]
    if subtitle:
        items.append(Paragraph(subtitle, STYLES["body_small"]))
    items.append(AccentRule())
    items.append(Spacer(1, 9))
    return items


def card_grid(cards: list[tuple[str, str]], columns: int = 2) -> Table:
    rows = []
    for start in range(0, len(cards), columns):
        row = []
        for title, body in cards[start : start + columns]:
            row.append([Paragraph(title, STYLES["card_title"]), Paragraph(body, STYLES["card_body"])])
        while len(row) < columns:
            row.append("")
        rows.append(row)
    width = 510 / columns
    table = Table(rows, colWidths=[width] * columns, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, WHITE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def metric_strip(metrics: list[tuple[str, str]], accent: colors.Color = BLUE) -> Table:
    cells = []
    for value, label in metrics:
        value_style = ParagraphStyle("metric_dynamic", parent=STYLES["metric"], textColor=accent)
        cells.append([Paragraph(value, value_style), Paragraph(label, STYLES["metric_label"])])
    table = Table([cells], colWidths=[510 / len(cells)] * len(cells), hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, WHITE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def project_banner(number: str, title: str, tag: str, color: colors.Color) -> Table:
    number_style = ParagraphStyle(
        "project_number",
        parent=STYLES["metric"],
        fontSize=18,
        textColor=WHITE,
        alignment=TA_CENTER,
    )
    title_style = ParagraphStyle(
        "project_title",
        parent=STYLES["h1"],
        fontSize=19,
        leading=22,
        textColor=NAVY,
        spaceAfter=2,
    )
    tag_style = ParagraphStyle(
        "project_tag",
        parent=STYLES["body_small"],
        fontName="Helvetica-Bold",
        fontSize=7,
        textColor=color,
    )
    table = Table(
        [
            [Paragraph(number, number_style), [Paragraph(title, title_style), Paragraph(tag.upper(), tag_style)]]
        ],
        colWidths=[48, 462],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), color),
                ("BACKGROUND", (1, 0), (1, 0), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 4),
                ("RIGHTPADDING", (0, 0), (0, 0), 4),
                ("LEFTPADDING", (1, 0), (1, 0), 14),
                ("RIGHTPADDING", (1, 0), (1, 0), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def bullet_table(items: list[str], color: colors.Color = TEAL) -> Table:
    rows = [[Paragraph("-", ParagraphStyle("dash", parent=STYLES["body"], textColor=color)), Paragraph(item, STYLES["body"])] for item in items]
    table = Table(rows, colWidths=[13, 497], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def evidence_matrix() -> Table:
    header_style = ParagraphStyle("matrix_header", parent=STYLES["card_title"], textColor=WHITE, fontSize=7.2, leading=9)
    cell_style = ParagraphStyle("matrix_cell", parent=STYLES["body_small"], fontSize=6.7, leading=8.7, textColor=INK)
    label_style = ParagraphStyle("matrix_label", parent=cell_style, fontName="Helvetica-Bold", textColor=NAVY)
    data = [
        [
            Paragraph("Engineering evidence", header_style),
            Paragraph("Lead Concierge", header_style),
            Paragraph("Business Ops", header_style),
            Paragraph("Outcome Intelligence", header_style),
        ],
        [Paragraph("Primary problem", label_style), Paragraph("Safe, grounded lead conversation", cell_style), Paragraph("Private lead operations and follow-up", cell_style), Paragraph("Lead analytics and booking propensity", cell_style)],
        [Paragraph("Backend", label_style), Paragraph("FastAPI structured chat API", cell_style), Paragraph("Next.js API routes and D1", cell_style), Paragraph("FastAPI scoring and metrics API", cell_style)],
        [Paragraph("Data", label_style), Paragraph("Consent-gated SQLite metadata", cell_style), Paragraph("Drizzle schema, D1, notes, pipeline stages", cell_style), Paragraph("Event grain CSV, DuckDB facts and marts", cell_style)],
        [Paragraph("AI / ML", label_style), Paragraph("Local Qwen3 via Ollama behind policy", cell_style), Paragraph("Workflow system; AI intentionally outside core data path", cell_style), Paragraph("Logistic and gradient boosting comparison", cell_style)],
        [Paragraph("Evaluation", label_style), Paragraph("Behavior cases, safety recall, coverage", cell_style), Paragraph("Rendered HTML and build checks", cell_style), Paragraph("Chronological validation, holdout, baselines", cell_style)],
        [Paragraph("Safety", label_style), Paragraph("Urgent, clinical, injection, and handoff rules", cell_style), Paragraph("Auth boundary, rate limits, honeypot, hashed client ID", cell_style), Paragraph("Consent boundary, no automated outreach, synthetic data", cell_style)],
        [Paragraph("Monitoring", label_style), Paragraph("Evaluation regression gates", cell_style), Paragraph("Pipeline queues and aggregate metrics", cell_style), Paragraph("Calibration, PSI drift, channel slices", cell_style)],
        [Paragraph("Delivery", label_style), Paragraph("Docker, GitHub Actions, public demo", cell_style), Paragraph("Cloudflare Sites, Worker, D1", cell_style), Paragraph("Docker, CI, portable dashboard, API", cell_style)],
    ]
    table = Table(data, colWidths=[105, 125, 132, 148], repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for row in range(1, len(data)):
        if row % 2 == 0:
            style.append(("BACKGROUND", (0, row), (-1, row), LIGHT))
    table.setStyle(TableStyle(style))
    return table


def source_link(label: str, url: str) -> Paragraph:
    return Paragraph(f'<link href="{url}" color="#2563EB"><u>{label}</u></link>', STYLES["link"])


def load_outcome_metrics() -> dict:
    return json.loads((ROOT / "artifacts" / "model_metrics.json").read_text(encoding="utf-8"))


def build_pdf(output: Path = OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    metrics = load_outcome_metrics()
    selected = metrics["selected_test_metrics"]
    naive = metrics["naive_test_metrics"]

    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.71 * inch,
        rightMargin=0.71 * inch,
        topMargin=0.57 * inch,
        bottomMargin=0.52 * inch,
        title="Russell York - Recent AI Engineering Project Record",
        author="Russell York",
        subject="Shareable portfolio record for recent Nyxora AI engineering projects",
        creator="Russell York with AI-assisted implementation",
    )
    story = []

    # Cover
    story.extend(
        [
            Spacer(1, 0.88 * inch),
            Paragraph("SHAREABLE PORTFOLIO BRIEF  |  JULY 2026", STYLES["cover_kicker"]),
            Paragraph("Recent AI Engineering<br/>Project Record", STYLES["cover_title"]),
            AccentRule(width=108, color=TEAL, thickness=5),
            Spacer(1, 22),
            Paragraph(
                "Three connected systems demonstrating applied AI, full-stack operations, "
                "structured machine learning, evaluation, safety, and deployment.",
                STYLES["cover_subtitle"],
            ),
            Spacer(1, 38),
            Paragraph("Russell York", STYLES["cover_name"]),
            Paragraph(
                "Career-transition portfolio  |  Target path: AI / LLM engineering with strong software and cloud foundations",
                STYLES["cover_meta"],
            ),
            Spacer(1, 108),
            Table(
                [
                    [
                        Paragraph("01", STYLES["cover_name"]),
                        Paragraph("Safe AI application", STYLES["cover_meta"]),
                        Paragraph("02", STYLES["cover_name"]),
                        Paragraph("Operational product", STYLES["cover_meta"]),
                        Paragraph("03", STYLES["cover_name"]),
                        Paragraph("Data and ML system", STYLES["cover_meta"]),
                    ]
                ],
                colWidths=[24, 112, 24, 112, 24, 112],
                hAlign="LEFT",
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                ),
            ),
            PageBreak(),
        ]
    )

    # Executive summary
    story.extend(section_heading("Portfolio narrative", "Executive summary", "A coherent progression, not three copies of the same project."))
    story.append(
        Paragraph(
            "The recent work shows a deliberate movement from an AI-enabled user experience, to the "
            "business system that receives and manages its outputs, to the analytical and machine-learning "
            "layer that measures outcomes. The Nyxora domain stays consistent, but each repository solves a "
            "different engineering problem with a different architecture.",
            STYLES["body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(PipelineFlow(["Lead Concierge", "Business Ops", "Outcome Intelligence"]))
    story.append(Paragraph("Why this supports an AI engineering path", STYLES["h2"]))
    story.append(
        card_grid(
            [
                ("End-to-end systems", "Requirements, APIs, data models, user workflows, deployment, and operational boundaries are treated as one system."),
                ("Model discipline", "The work includes grounded retrieval, behavior evaluations, chronological ML splits, baselines, calibration, and drift."),
                ("Responsible automation", "Human handoffs, consent gates, privacy minimization, no automatic outreach, and explicit limitations are built into the designs."),
                ("Technical ownership", "The projects are runnable, tested, documented, containerized, and tied to measurable business outcomes rather than isolated prompts."),
            ]
        )
    )
    story.append(Spacer(1, 10))
    authorship = Table(
        [[Paragraph("AUTHORSHIP NOTE", STYLES["card_title"]), Paragraph("Russell directed the problem framing, requirements, architecture decisions, validation goals, and portfolio narrative. AI tools assisted implementation, debugging, research, and documentation. The record does not claim prior professional ML engineering experience or production validation.", STYLES["card_body"]) ]],
        colWidths=[95, 415],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#9ED8CE")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        ),
    )
    story.append(authorship)
    story.append(PageBreak())

    # Lead Concierge
    story.append(project_banner("01", "Nyxora Lead Concierge", "Applied LLM engineering and safety", BLUE))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "A privacy-conscious lead qualification and human-handoff API for a synthetic aesthetics-clinic use case. "
            "It demonstrates that model output is only one layer of a dependable AI product: deterministic safety "
            "policy runs first, retrieved facts constrain responses, and the model cannot override routing decisions.",
            STYLES["body"],
        )
    )
    story.append(PipelineFlow(["Validated API", "Safety policy", "Lead scoring", "Grounded retrieval", "Local Ollama", "Structured action"]))
    story.append(metric_strip([("24", "automated tests"), ("94%", "code coverage"), ("12/12", "behavior cases"), ("100%", "safety recall")]))
    story.append(Paragraph("Engineering evidence", STYLES["h2"]))
    story.append(
        bullet_table(
            [
                "FastAPI request and response contracts with explicit answer, booking, handoff, and emergency actions.",
                "Grounded retrieval from a versioned synthetic knowledge base with visible source names.",
                "Provider-neutral generation interface with local Qwen3 14B through Ollama and deterministic fallback.",
                "Prompt-injection, urgent-language, clinical-review, consent, privacy, and human-handoff controls.",
                "GitHub Actions, Docker, architecture decisions, tests, and behavior-evaluation gates.",
            ]
        )
    )
    story.append(Paragraph("Public evidence", STYLES["h2"]))
    links = Table(
        [
            [Paragraph("Repository", STYLES["card_title"]), source_link("github.com/Ryork67677/nyxora-lead-concierge", "https://github.com/Ryork67677/nyxora-lead-concierge")],
            [Paragraph("Recorded demo", STYLES["card_title"]), source_link("ryork67677.github.io/nyxora-lead-concierge", "https://ryork67677.github.io/nyxora-lead-concierge/")],
            [Paragraph("Latest verified CI", STYLES["card_title"]), source_link("GitHub Actions run 29351547468 - success", "https://github.com/Ryork67677/nyxora-lead-concierge/actions/runs/29351547468")],
        ],
        colWidths=[90, 420],
        style=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )
    story.append(links)
    story.append(PageBreak())

    # Business Ops
    story.append(project_banner("02", "Nyxora Business Ops", "Full-stack operations and secure intake", TEAL))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "A hosted operating dashboard that receives free audit requests from the Nyxora website and turns them "
            "into an actionable lead pipeline. This project moves beyond an AI demo into the internal product and data "
            "boundary required to operate a real workflow.",
            STYLES["body"],
        )
    )
    story.append(PipelineFlow(["Website audit form", "Origin and abuse checks", "Structured intake API", "Cloudflare D1", "Authenticated dashboard"]))
    story.append(
        metric_strip(
            [("v3", "deployed Sites version"), ("D1", "durable data store"), ("6", "pipeline end states"), ("0", "visitor IPs stored")],
            accent=TEAL,
        )
    )
    story.append(Paragraph("Product and security capabilities", STYLES["h2"]))
    story.append(
        card_grid(
            [
                ("Pipeline control", "Lead stages from new request through audit, proposal, won, nurture, or lost; plus priority, follow-up date, value, and notes."),
                ("Direct intake", "The website sends structured JSON to a server route, eliminating a paid form service and keeping database credentials out of the browser."),
                ("Abuse resistance", "Origin verification, a hidden honeypot, deduplication, rate limiting, and a hashed client identifier protect the public route."),
                ("Operator boundary", "Dashboard data routes require authenticated operator context. Aggregate metrics are separated from raw customer details."),
            ]
        )
    )
    story.append(Spacer(1, 9))
    story.append(
        Table(
            [[Paragraph("LIVE APPLICATION", STYLES["card_title"]), source_link("nyxora-business-ops.yorkrussell282.chatgpt.site", "https://nyxora-business-ops.yorkrussell282.chatgpt.site")]],
            colWidths=[105, 405],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#9ED8CE")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        )
    )
    story.append(Spacer(1, 5))
    story.append(Paragraph("The hosted shell is reachable at the link above. Operational data remains subject to the application's sign-in checks. The source repository is private because this is an internal business tool.", STYLES["source"]))
    story.append(PageBreak())

    # Outcome Intelligence
    story.append(project_banner("03", "Nyxora Outcome Intelligence", "Data engineering, classical ML, and monitoring", AMBER))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "A reproducible analytics and machine-learning system that asks which leads may deserve human attention "
            "after a fixed 24-hour observation window. It intentionally does not use an LLM: structured probability "
            "estimation, SQL transformations, and transparent evaluation are the right tools for this problem.",
            STYLES["body"],
        )
    )
    story.append(PipelineFlow(["10k synthetic leads", "DuckDB facts and marts", "Chronological splits", "Model comparison", "Drift and calibration", "FastAPI scoring"]))
    story.append(metric_strip([("10,000", "synthetic leads"), ("36,173", "lifecycle events"), ("9/9", "data contracts"), ("96%", "core coverage")], accent=AMBER))
    story.append(Paragraph("Verified holdout performance", STYLES["h2"]))
    story.append(
        ComparisonBars(
            [
                ("ROC AUC", selected["roc_auc"], naive["roc_auc"]),
                ("Average precision", selected["average_precision"], naive["average_precision"]),
            ]
        )
    )
    story.append(
        Table(
            [
                [Paragraph("Probability quality", STYLES["card_title"]), Paragraph("Selected model", STYLES["card_title"]), Paragraph("Naive baseline", STYLES["card_title"]), Paragraph("Direction", STYLES["card_title"])],
                [Paragraph("Brier score", STYLES["body_small"]), Paragraph(f"{selected['brier_score']:.3f}", STYLES["body_small"]), Paragraph(f"{naive['brier_score']:.3f}", STYLES["body_small"]), Paragraph("Lower is better", STYLES["body_small"])],
            ],
            colWidths=[170, 110, 110, 120],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                    ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        )
    )
    story.append(Spacer(1, 7))
    story.append(
        card_grid(
            [
                ("Temporal discipline", "Only matured labels train the model; the newest 15% remains an untouched chronological holdout."),
                ("Operational safety", "Consent controls the recommended action, no outreach is sent, and scores remain human decision support."),
                ("Model observability", "Calibration deciles, channel slices, permutation importance, and Population Stability Index are generated every build."),
                ("Reproducible delivery", "One command rebuilds data, warehouse, models, monitoring, candidate scores, and the portable dashboard."),
            ]
        )
    )
    story.append(Spacer(1, 8))
    story.append(source_link("Repository: github.com/Ryork67677/nyxora-outcome-intelligence", "https://github.com/Ryork67677/nyxora-outcome-intelligence"))
    story.append(source_link("Recorded dashboard: ryork67677.github.io/nyxora-outcome-intelligence", "https://ryork67677.github.io/nyxora-outcome-intelligence/"))
    story.append(PageBreak())

    # Matrix
    story.extend(section_heading("Cross-project evidence", "What the portfolio now proves", "Each project fills a different part of the applied AI engineering stack."))
    story.append(evidence_matrix())
    story.append(Spacer(1, 12))
    story.append(
        Table(
            [[Paragraph("THE THROUGH-LINE", STYLES["card_title"]), Paragraph("Find a real workflow, define deterministic boundaries, introduce AI only where it adds value, make behavior measurable, and keep a human responsible for sensitive actions.", STYLES["callout"]) ]],
            colWidths=[100, 410],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#B7CDF8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        )
    )
    story.append(PageBreak())

    # Career alignment
    story.extend(section_heading("Career direction", "Why AI engineering is a credible next path", "The evidence is practical and promising, while the remaining gaps are stated plainly."))
    story.append(
        Paragraph(
            "Russell's operations, training, and customer-facing background maps naturally to applied AI engineering: "
            "he focuses on handoffs, edge cases, adoption, accountability, and business outcomes. The recent systems add "
            "the technical layer - code, data, models, tests, deployment, and monitoring - needed to turn that systems "
            "mindset into an engineering career.",
            STYLES["body"],
        )
    )
    story.append(Paragraph("Evidence already demonstrated", STYLES["h2"]))
    story.append(
        card_grid(
            [
                ("Applied AI systems", "Local model integration, grounded context, tool boundaries, deterministic policy, and human handoffs."),
                ("Software foundations", "Python, TypeScript, FastAPI, Next.js, SQL, schemas, API validation, Git, CI, Docker, and cloud deployment."),
                ("Evaluation mindset", "Behavior suites, coverage gates, chronological holdouts, probability baselines, calibration, drift, and data reconciliation."),
                ("Product ownership", "Problem framing, architecture choices, user workflows, security trade-offs, documentation, and measurable definitions of done."),
            ]
        )
    )
    story.append(Paragraph("Important next foundations", STYLES["h2"]))
    story.append(
        bullet_table(
            [
                "Deepen independent Python and SQL fluency until implementation choices can be explained without tool assistance.",
                "Continue computer science, data structures, algorithms, mathematics, statistics, and formal ML coursework.",
                "Replace synthetic assumptions with governed, consented, representative data before making real performance claims.",
                "Add production authentication, secrets management, infrastructure observability, alert ownership, and prospective validation.",
                "Practice concise technical walkthroughs that connect architecture decisions to user and business outcomes.",
            ],
            color=AMBER,
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        Table(
            [[Paragraph("HONEST LEVEL", STYLES["card_title"]), Paragraph("Early-career AI engineering candidate with unusually strong applied workflow and product context - not yet a professional ML engineer. The portfolio shows direction, discipline, and the ability to learn by building.", STYLES["callout"]) ]],
            colWidths=[88, 422],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7ED")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#F4C78F")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        )
    )
    story.append(PageBreak())

    # Sources and close
    story.extend(section_heading("Evidence and disclosure", "Shareable source record", "Links and claims below were checked against the repositories, live deployment metadata, and generated validation artifacts."))
    source_rows = [
        [Paragraph("1", STYLES["card_title"]), [Paragraph("Nyxora Lead Concierge", STYLES["card_title"]), source_link("Public GitHub repository", "https://github.com/Ryork67677/nyxora-lead-concierge"), Paragraph("README metrics: 24 tests, 94% coverage, 12/12 behavior cases, 100% safety recall. Latest checked CI run concluded successfully.", STYLES["source"]) ]],
        [Paragraph("2", STYLES["card_title"]), [Paragraph("Lead Concierge recorded demo", STYLES["card_title"]), source_link("GitHub Pages demonstration", "https://ryork67677.github.io/nyxora-lead-concierge/"), Paragraph("Recorded behavior artifact; it does not connect to real customer data.", STYLES["source"]) ]],
        [Paragraph("3", STYLES["card_title"]), [Paragraph("Nyxora Business Ops", STYLES["card_title"]), source_link("Hosted application", "https://nyxora-business-ops.yorkrussell282.chatgpt.site"), Paragraph("Sites project metadata: active, version 3. Application-level checks protect operational data routes.", STYLES["source"]) ]],
        [Paragraph("4", STYLES["card_title"]), [Paragraph("Nyxora Outcome Intelligence", STYLES["card_title"]), source_link("Public GitHub repository", "https://github.com/Ryork67677/nyxora-outcome-intelligence"), source_link("Recorded dashboard demonstration", "https://ryork67677.github.io/nyxora-outcome-intelligence/"), Paragraph("Default-build validation: 10,000 synthetic leads, 36,173 events, 9/9 contracts, 13 tests, 96% core coverage, Docker and live API smoke checks.", STYLES["source"]) ]],
    ]
    sources_table = Table(source_rows, colWidths=[32, 478], hAlign="LEFT")
    sources_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), NAVY),
                ("TEXTCOLOR", (0, 0), (0, -1), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(sources_table)
    story.append(Paragraph("Limitations that must travel with this document", STYLES["h2"]))
    story.append(
        bullet_table(
            [
                "Outcome Intelligence uses synthetic data; its metrics demonstrate methodology, not real clinic performance.",
                "Lead Concierge is educational software and has not received clinical validation or a production red-team review.",
                "Business Ops is an internal operating tool; public reachability does not imply public access to operator data.",
                "AI assistance accelerated implementation. Russell remains responsible for scope, decisions, testing, explanations, and every claim in this record.",
            ],
            color=BLUE,
        )
    )
    story.append(Spacer(1, 9))
    story.append(
        Table(
            [[Paragraph("PORTFOLIO CONCLUSION", STYLES["card_title"]), Paragraph("The strongest signal is not one model or framework. It is the ability to connect business workflows, software systems, data quality, model behavior, safety boundaries, and measurable outcomes into a coherent engineering product.", STYLES["callout"]) ]],
            colWidths=[112, 398],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#B7CDF8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            ),
        )
    )
    story.append(Spacer(1, 10))
    story.append(Paragraph("GitHub: <link href='https://github.com/Ryork67677' color='#2563EB'><u>github.com/Ryork67677</u></link>", STYLES["link"]))

    doc.build(story, onFirstPage=page_chrome, onLaterPages=page_chrome)
    return output


if __name__ == "__main__":
    print(build_pdf())
