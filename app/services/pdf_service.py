import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from app.models import db, Attempt, Test, Student, Question, Answer, Feedback, Report, SchoolSettings

class NumberedCanvas(canvas.Canvas):
    """Adds page numbers and footer dynamically to every page"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Top header line on subsequent pages
        if self._pageNumber > 1:
            self.drawString(54, 750, "Student Assessment Diagnostic Report")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}  •  Student Assessment Tracker"
        self.drawRightString(558, 30, footer_text)
        gen_text = f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        self.drawString(54, 30, gen_text)
        self.restoreState()

def generate_pdf_report(attempt_id: int, reports_dir: str = "reports") -> str:
    """
    Builds a beautifully styled school-branded assessment report PDF.
    Returns: absolute file path to the generated PDF.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt {attempt_id} not found.")

    test = Test.query.get(attempt.test_id)
    student = Student.query.get(attempt.student_id)
    feedback = Feedback.query.filter_by(attempt_id=attempt_id).first()
    school_settings = SchoolSettings.query.first()

    questions = Question.query.filter_by(test_id=test.id).order_by(Question.q_no).all()
    answers = Answer.query.filter_by(attempt_id=attempt_id).all()
    ans_map = {a.question_id: a for a in answers}

    os.makedirs(reports_dir, exist_ok=True)
    filename = f"report_attempt_{attempt.id}_{student.name.replace(' ', '_')}.pdf"
    file_path = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1e3a8a")  # Deep school navy
    accent_color = colors.HexColor("#2563eb")   # Royal blue
    text_dark = colors.HexColor("#0f172a")
    text_muted = colors.HexColor("#475569")
    bg_light = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#e2e8f0")
    success_color = colors.HexColor("#16a34a")
    danger_color = colors.HexColor("#dc2626")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=accent_color
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=text_dark
    )

    body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    story = []

    # 1. School Header Block
    header_data = []
    logo_cell = ""
    school_name_text = school_settings.school_name if school_settings else "Delhi Public Model School"

    if school_settings and school_settings.logo_path and os.path.exists(school_settings.logo_path):
        try:
            img = Image(school_settings.logo_path, width=1.1*inch, height=1.1*inch)
            img.hAlign = 'LEFT'
            logo_cell = img
        except Exception:
            logo_cell = ""

    school_header_para = Paragraph(f"<b>{school_name_text.upper()}</b>", title_style)
    sub_title_para = Paragraph("STUDENT ASSESSMENT & DIAGNOSTIC REPORT", subtitle_style)

    if logo_cell:
        header_table = Table([[logo_cell, [school_header_para, Spacer(1, 4), sub_title_para]]], colWidths=[1.3*inch, 5.7*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (1, 0), (1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
    else:
        story.append(school_header_para)
        story.append(Spacer(1, 2))
        story.append(sub_title_para)

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=4, spaceAfter=10))

    # 2. Metadata Grid (Student Info & Test Info)
    date_str = attempt.submitted_at.strftime("%d %B %Y, %I:%M %p") if attempt.submitted_at else datetime.now().strftime("%d %B %Y")
    info_table_data = [
        [
            Paragraph(f"<b>Student Name:</b> {student.name}", body_style),
            Paragraph(f"<b>Assessment:</b> {test.name}", body_style)
        ],
        [
            Paragraph(f"<b>Class / Section:</b> {student.class_name}", body_style),
            Paragraph(f"<b>Subject:</b> {test.subject}", body_style)
        ],
        [
            Paragraph(f"<b>Attempt ID:</b> #{attempt.id}", body_style),
            Paragraph(f"<b>Date:</b> {date_str}", body_style)
        ]
    ]
    info_table = Table(info_table_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # 3. Score Summary Metric Cards
    pct = round((attempt.score / attempt.max_score * 100), 1) if attempt.max_score > 0 else 0
    time_min = attempt.total_time_sec // 60
    time_sec = attempt.total_time_sec % 60
    time_display = f"{time_min}m {time_sec}s"

    card_data = [
        [
            Paragraph(f"<font size=18 color='#1e3a8a'><b>{attempt.score}</b></font><font size=10 color='#64748b'> / {attempt.max_score}</font><br/><font size=8 color='#64748b'>FINAL SCORE</font>", body_style),
            Paragraph(f"<font size=18 color='#2563eb'><b>{pct}%</b></font><br/><font size=8 color='#64748b'>PERCENTAGE</font>", body_style),
            Paragraph(f"<font size=18 color='#16a34a'><b>{attempt.correct}</b></font><br/><font size=8 color='#64748b'>CORRECT</font>", body_style),
            Paragraph(f"<font size=18 color='#dc2626'><b>{attempt.wrong}</b></font><br/><font size=8 color='#64748b'>INCORRECT</font>", body_style),
            Paragraph(f"<font size=18 color='#d97706'><b>{attempt.skipped}</b></font><br/><font size=8 color='#64748b'>SKIPPED</font>", body_style),
            Paragraph(f"<font size=15 color='#0f172a'><b>{time_display}</b></font><br/><font size=8 color='#64748b'>TIME TAKEN</font>", body_style)
        ]
    ]
    cards_table = Table(card_data, colWidths=[1.16*inch]*6)
    cards_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(cards_table)
    story.append(Spacer(1, 12))

    # 4. Deep AI Diagnostic Analysis Section
    payload = feedback.json_payload if (feedback and feedback.json_payload) else {}
    if payload:
        story.append(Paragraph("AI Diagnostic Insights & Personalized Feedback", section_heading))
        
        # Summary
        if payload.get("summary"):
            summary_p = Paragraph(f"<b>Executive Summary:</b> {payload['summary']}", body_style)
            summary_box = Table([[summary_p]], colWidths=[7.0*inch])
            summary_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bfdbfe")),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(summary_box)
            story.append(Spacer(1, 8))

        # Strengths & Weak Areas Side-by-Side
        col_left = [Paragraph("<b>Key Strengths</b>", body_bold)]
        for s in payload.get("strengths", []):
            col_left.append(Paragraph(f"• <b>{s.get('topic')}:</b> {s.get('evidence')}", body_style))
            col_left.append(Spacer(1, 2))

        col_right = [Paragraph("<b>Areas for Improvement</b>", body_bold)]
        for w in payload.get("weak_areas", []):
            pri_tag = f"[{w.get('priority', 'med').upper()}]"
            col_right.append(Paragraph(f"• <b>{w.get('topic')}</b> <font color='#dc2626'>{pri_tag}</font>: {w.get('evidence')}", body_style))
            col_right.append(Spacer(1, 2))

        sw_table = Table([[col_left, col_right]], colWidths=[3.45*inch, 3.45*inch])
        sw_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#f0fdf4")),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#fef2f2")),
            ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor("#bbf7d0")),
            ('BOX', (1, 0), (1, 0), 0.5, colors.HexColor("#fecaca")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(sw_table)
        story.append(Spacer(1, 8))

        # Action Plan Steps
        if payload.get("action_plan"):
            plan_rows = [[
                Paragraph("<b>#</b>", body_bold),
                Paragraph("<b>Actionable Study Step</b>", body_bold),
                Paragraph("<b>Est. Time</b>", body_bold),
                Paragraph("<b>Target Resource / Reference</b>", body_bold)
            ]]
            for idx, step in enumerate(payload["action_plan"], start=1):
                plan_rows.append([
                    Paragraph(str(idx), body_style),
                    Paragraph(step.get("step", ""), body_style),
                    Paragraph(step.get("estimated_time", ""), body_style),
                    Paragraph(step.get("resource_hint", ""), body_style)
                ])
            plan_table = Table(plan_rows, colWidths=[0.3*inch, 3.8*inch, 1.0*inch, 1.9*inch])
            plan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(Paragraph("<b>Personalized Study & Practice Plan:</b>", body_bold))
            story.append(Spacer(1, 4))
            story.append(plan_table)
            story.append(Spacer(1, 8))

        # Encouragement
        if payload.get("encouragement"):
            enc_para = Paragraph(f"<i>Coach Note: {payload['encouragement']}</i>", ParagraphStyle("Enc", parent=body_style, textColor=colors.HexColor("#047857")))
            story.append(enc_para)
            story.append(Spacer(1, 12))

    # 5. Topic-Wise Performance Table
    story.append(Paragraph("Topic-Wise Accuracy Breakdown", section_heading))
    topic_tally = {}
    for q in questions:
        top = q.topic or "General"
        if top not in topic_tally:
            topic_tally[top] = {"total": 0, "correct": 0, "wrong": 0}
        topic_tally[top]["total"] += 1
        ans = ans_map.get(q.id)
        if ans and ans.selected_option and ans.is_correct:
            topic_tally[top]["correct"] += 1
        elif ans and ans.selected_option:
            topic_tally[top]["wrong"] += 1

    topic_rows = [[
        Paragraph("<b>Topic</b>", body_bold),
        Paragraph("<b>Total Questions</b>", body_bold),
        Paragraph("<b>Correct</b>", body_bold),
        Paragraph("<b>Incorrect / Skipped</b>", body_bold),
        Paragraph("<b>Accuracy (%)</b>", body_bold)
    ]]
    for t_name, stats in topic_tally.items():
        t_pct = round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        color_hex = "#16a34a" if t_pct >= 70 else ("#d97706" if t_pct >= 40 else "#dc2626")
        topic_rows.append([
            Paragraph(t_name, body_style),
            Paragraph(str(stats["total"]), body_style),
            Paragraph(str(stats["correct"]), body_style),
            Paragraph(str(stats["total"] - stats["correct"]), body_style),
            Paragraph(f"<font color='{color_hex}'><b>{t_pct}%</b></font>", body_style)
        ])
    topic_table = Table(topic_rows, colWidths=[2.6*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
    topic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(topic_table)
    story.append(Spacer(1, 12))

    # 6. Itemized Mistakes Review (Only incorrect questions)
    wrong_answers = []
    for q in questions:
        ans = ans_map.get(q.id)
        if ans and ans.selected_option and not ans.is_correct:
            wrong_answers.append((q, ans))

    if wrong_answers:
        story.append(Paragraph(f"Mistakes Review & Explanations ({len(wrong_answers)} Missed Questions)", section_heading))
        for q, ans in wrong_answers:
            chosen = ans.selected_option
            correct = q.correct_option
            spent = ans.time_spent_sec
            explanation = q.explanation or "No explanation provided for this question."

            q_text_p = Paragraph(f"<b>Q{q.q_no}. {q.text}</b> (Topic: <i>{q.topic}</i> | Spent: {spent}s)", body_style)
            ans_p = Paragraph(f"Your Answer: <font color='#dc2626'><b>Option {chosen}</b></font> &nbsp;&nbsp;|&nbsp;&nbsp; Correct Answer: <font color='#16a34a'><b>Option {correct}</b></font>", body_bold)
            exp_p = Paragraph(f"<b>Explanation:</b> {explanation}", body_style)

            m_box = Table([[q_text_p], [ans_p], [exp_p]], colWidths=[7.0*inch])
            m_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#fecdd3")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(KeepTogether([m_box, Spacer(1, 6)]))

    # Build PDF with custom numbered canvas
    doc.build(story, canvasmaker=NumberedCanvas)

    # Persist or update Report record in DB
    report = Report.query.filter_by(attempt_id=attempt.id).first()
    if not report:
        report = Report(
            attempt_id=attempt.id,
            pdf_path=file_path,
            generated_at=datetime.utcnow()
        )
        db.session.add(report)
    else:
        report.pdf_path = file_path
        report.generated_at = datetime.utcnow()
    db.session.commit()

    return file_path
