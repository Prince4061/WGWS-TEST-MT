import csv
import io
import random
from app.models import db, Question

REQUIRED_COLUMNS = [
    "question_no",
    "question",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_option",
    "topic",
    "question_type",
    "difficulty"
]

OPTIONAL_COLUMNS = ["explanation"]

VALID_OPTIONS = {"A", "B", "C", "D"}
VALID_TYPES = {"conceptual", "numerical", "application", "recall"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}

def generate_csv_template():
    """Generates a downloadable CSV template with sample questions as specified in PRD Section 4.3"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "question_no", "question", "option_a", "option_b", "option_c", "option_d",
        "correct_option", "topic", "question_type", "difficulty", "explanation"
    ]
    writer.writerow(headers)
    
    sample_rows = [
        [
            1, "What is 3/4 + 1/4?", "1", "3/8", "1/2", "4/8",
            "A", "Fractions", "numerical", "easy", "Same denominator add numerators: 4/4 = 1"
        ],
        [
            2, "If 2x + 6 = 14, what is the value of x?", "2", "4", "6", "8",
            "B", "Algebra", "application", "medium", "2x = 14 - 6 = 8, so x = 4"
        ],
        [
            3, "Which of the following is a prime number?", "9", "15", "17", "21",
            "C", "Number Systems", "recall", "easy", "17 has only two factors: 1 and 17"
        ],
        [
            4, "The perimeter of a square is 36 cm. What is its area?", "36 cm²", "72 cm²", "81 cm²", "144 cm²",
            "C", "Geometry", "conceptual", "medium", "Side = 36/4 = 9 cm. Area = 9 * 9 = 81 cm²"
        ]
    ]
    for row in sample_rows:
        writer.writerow(row)
        
    return output.getvalue()

def validate_and_parse_csv(file_stream, test, selected_count=None):
    """
    Parses and validates CSV stream.
    Returns: (success: bool, errors: list, questions_imported: int)
    """
    errors = []
    
    try:
        # Detect encoding: read bytes and decode utf-8 or utf-8-sig (for Excel CSVs)
        content = file_stream.read()
        if isinstance(content, bytes):
            try:
                decoded = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                decoded = content.decode("latin-1")
        else:
            decoded = content
            
        csv_reader = csv.DictReader(io.StringIO(decoded))
    except Exception as e:
        return False, [f"Failed to read CSV file: {str(e)}"], 0

    if not csv_reader.fieldnames:
        return False, ["CSV file is empty or corrupted."], 0

    # Clean fieldnames (strip spaces, lowercase)
    field_map = {name.strip().lower(): name for name in csv_reader.fieldnames if name}
    
    missing_cols = []
    for req in REQUIRED_COLUMNS:
        if req not in field_map:
            missing_cols.append(req)
            
    if missing_cols:
        return False, [f"Missing required columns in CSV header: {', '.join(missing_cols)}"], 0

    parsed_rows = []
    seen_questions = set()
    row_num = 1  # 1 is header

    for row in csv_reader:
        row_num += 1
        # Extract fields using mapped keys
        def get_val(key, default=""):
            orig_col = field_map.get(key)
            return (row.get(orig_col) or "").strip() if orig_col else default

        q_text = get_val("question")
        opt_a = get_val("option_a")
        opt_b = get_val("option_b")
        opt_c = get_val("option_c")
        opt_d = get_val("option_d")
        correct_opt = get_val("correct_option").upper()
        topic = get_val("topic")
        q_type = get_val("question_type").lower()
        diff = get_val("difficulty").lower()
        explanation = get_val("explanation")

        # Row validations
        row_errs = []
        if not q_text:
            row_errs.append("Question text cannot be empty.")
        if not opt_a or not opt_b or not opt_c or not opt_d:
            row_errs.append("All options (A, B, C, D) must have text.")
        if correct_opt not in VALID_OPTIONS:
            row_errs.append(f"Correct option must be one of A, B, C, D (Found: '{correct_opt}').")
        if not topic:
            row_errs.append("Topic is required.")
        if q_type and q_type not in VALID_TYPES:
            q_type = "conceptual"
        if diff and diff not in VALID_DIFFICULTIES:
            diff = "medium"

        if q_text and q_text.lower() in seen_questions:
            row_errs.append("Duplicate question found in CSV.")
        elif q_text:
            seen_questions.add(q_text.lower())

        if row_errs:
            errors.append(f"Row {row_num}: " + "; ".join(row_errs))
        else:
            parsed_rows.append({
                "q_no": len(parsed_rows) + 1,
                "text": q_text,
                "opt_a": opt_a,
                "opt_b": opt_b,
                "opt_c": opt_c,
                "opt_d": opt_d,
                "correct_option": correct_opt,
                "topic": topic,
                "question_type": q_type or "conceptual",
                "difficulty": diff or "medium",
                "explanation": explanation
            })

    if errors:
        return False, errors, 0

    if not parsed_rows:
        return False, ["CSV contains no valid question rows."], 0

    # Clear existing questions for this test if replacing
    Question.query.filter_by(test_id=test.id).delete()

    # Determine subset if admin specified fewer or if total_questions < uploaded
    target_count = selected_count or test.total_questions or len(parsed_rows)
    if len(parsed_rows) > target_count:
        if test.shuffle:
            final_rows = random.sample(parsed_rows, target_count)
        else:
            final_rows = parsed_rows[:target_count]
    else:
        final_rows = parsed_rows

    # Re-index questions cleanly from 1..N
    for idx, q_data in enumerate(final_rows, start=1):
        question = Question(
            test_id=test.id,
            q_no=idx,
            text=q_data["text"],
            opt_a=q_data["opt_a"],
            opt_b=q_data["opt_b"],
            opt_c=q_data["opt_c"],
            opt_d=q_data["opt_d"],
            correct_option=q_data["correct_option"],
            topic=q_data["topic"],
            question_type=q_data["question_type"],
            difficulty=q_data["difficulty"],
            explanation=q_data["explanation"]
        )
        db.session.add(question)

    test.total_questions = len(final_rows)
    db.session.commit()

    return True, [], len(final_rows)
