"""
Post-processor and validator for quiz data.

Applies all quality fixes discovered in the v4/v5 analysis:
- Adds missing 'type' fields
- Removes true duplicates
- Validates schema per question type
- Checks slider ranges
- Verifies MCQ option counts
- Flags content accuracy issues
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ValidationReport:
    """Collects all validation findings."""
    file_path: str = ""
    total_questions: int = 0
    duplicates_removed: int = 0
    types_added: int = 0
    schema_errors: list[str] = field(default_factory=list)
    accuracy_warnings: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    type_distribution: dict[str, int] = field(default_factory=dict)

    def has_errors(self) -> bool:
        return len(self.schema_errors) > 0

    def summary(self) -> str:
        lines = [
            f"  File: {self.file_path}",
            f"  Questions: {self.total_questions}",
        ]
        if self.duplicates_removed:
            lines.append(f"  Duplicates removed: {self.duplicates_removed}")
        if self.types_added:
            lines.append(f"  Missing 'type' fields fixed: {self.types_added}")
        if self.fixes_applied:
            lines.append(f"  Other fixes: {len(self.fixes_applied)}")
            for fix in self.fixes_applied[:5]:
                lines.append(f"    - {fix}")
        if self.schema_errors:
            lines.append(f"  ❌ Schema errors: {len(self.schema_errors)}")
            for err in self.schema_errors[:10]:
                lines.append(f"    - {err}")
        if self.accuracy_warnings:
            lines.append(f"  ⚠️  Accuracy warnings: {len(self.accuracy_warnings)}")
            for warn in self.accuracy_warnings[:10]:
                lines.append(f"    - {warn}")
        if self.type_distribution:
            lines.append(f"  Type distribution:")
            for t, c in sorted(self.type_distribution.items()):
                lines.append(f"    {t}: {c}")
        return "\n".join(lines)


def load_json_file(filepath: str) -> list[dict]:
    """Load and parse a JSON file, handling common issues."""
    path = Path(filepath)
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []

    # Strip markdown code fences if present (common AI output artifact)
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        else:
            return [data]
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON parse error in {filepath}: {e}")
        return []


def add_missing_types(questions: list[dict], report: ValidationReport) -> list[dict]:
    """Add explicit 'type' field to questions that are missing it."""
    for q in questions:
        if "type" not in q:
            if "o" in q:
                q["type"] = "mcq"
                report.types_added += 1
            elif "correct" in q and q.get("correct") in ("True", "False"):
                q["type"] = "true_false"
                report.types_added += 1
    return questions


def remove_duplicates(questions: list[dict], report: ValidationReport) -> list[dict]:
    """Remove true duplicate questions (same question text + same options/answers)."""
    seen = set()
    unique = []

    for q in questions:
        # Build a fingerprint from the question
        fingerprint_parts = [q.get("q", "").strip().lower()]

        # Add options to fingerprint if present
        if "o" in q:
            fingerprint_parts.append(str(sorted(str(o).lower() for o in q["o"])))
        if "answers" in q:
            ans = q["answers"]
            if isinstance(ans, list):
                fingerprint_parts.append(str(sorted(str(a).lower() for a in ans)))
            else:
                fingerprint_parts.append(str(ans).lower())
        if "correct" in q:
            fingerprint_parts.append(str(q["correct"]).lower())

        fingerprint = "|||".join(fingerprint_parts)

        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(q)
        else:
            report.duplicates_removed += 1

    return unique


def validate_question(q: dict, index: int, report: ValidationReport) -> bool:
    """
    Validate a single question's schema. Returns True if valid.
    Adds errors to report for invalid questions.
    """
    qtype = q.get("type", "unknown")
    qtext = q.get("q", "")

    if not qtext.strip():
        report.schema_errors.append(f"Q#{index}: Empty question text")
        return False

    if qtype == "mcq":
        return _validate_mcq(q, index, report)
    elif qtype == "fill_blank":
        return _validate_fill_blank(q, index, report)
    elif qtype == "true_false":
        return _validate_true_false(q, index, report)
    elif qtype == "short_answer":
        return _validate_short_answer(q, index, report)
    elif qtype == "match":
        return _validate_match(q, index, report)
    elif qtype == "slider":
        return _validate_slider(q, index, report)
    elif qtype == "memory":
        return _validate_memory(q, index, report)
    elif qtype == "odd_one_out":
        return _validate_odd_one_out(q, index, report)
    elif qtype == "swipe_cards":
        return _validate_swipe_cards(q, index, report)
    elif qtype == "word_scramble":
        return _validate_word_scramble(q, index, report)
    elif qtype == "inline_dropdown":
        return _validate_inline_dropdown(q, index, report)
    else:
        report.schema_errors.append(f"Q#{index}: Unknown type '{qtype}'")
        return False


def _validate_mcq(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    if "o" not in q:
        report.schema_errors.append(f"Q#{index} (mcq): Missing 'o' field")
        return False

    opts = q["o"]
    if len(opts) != 4:
        report.schema_errors.append(
            f"Q#{index} (mcq): Has {len(opts)} options, expected 4"
        )
        valid = False

    # Check for empty options
    for i, opt in enumerate(opts):
        if not str(opt).strip():
            report.schema_errors.append(
                f"Q#{index} (mcq): Option {i} is empty/blank"
            )
            valid = False

    # Check for option length imbalance (giveaway correct answer)
    if len(opts) == 4 and all(isinstance(opt, str) for opt in opts):
        len0 = len(opts[0])
        distractor_lens = [len(opt) for opt in opts[1:]]
        avg_distractor_len = sum(distractor_lens) / max(len(distractor_lens), 1)
        if len0 > 40 and len0 > 2.2 * avg_distractor_len:
            report.accuracy_warnings.append(
                f"Q#{index} (mcq): Option 0 (answer) is significantly longer ({len0} chars) than distractors (avg {avg_distractor_len:.0f} chars)"
            )

    return valid


def _validate_fill_blank(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    if "answers" not in q:
        report.schema_errors.append(f"Q#{index} (fill_blank): Missing 'answers'")
        valid = False
    if "other_options" not in q:
        report.schema_errors.append(f"Q#{index} (fill_blank): Missing 'other_options'")
        valid = False

    # Check blank placeholder exists
    qtext = q.get("q", "")
    if "______" not in qtext and "____" not in qtext:
        report.accuracy_warnings.append(
            f"Q#{index} (fill_blank): No blank placeholder (______) in question text"
        )

    return valid


def _validate_true_false(q: dict, index: int, report: ValidationReport) -> bool:
    if "correct" not in q:
        report.schema_errors.append(f"Q#{index} (true_false): Missing 'correct'")
        return False
    if q["correct"] not in ("True", "False"):
        report.schema_errors.append(
            f"Q#{index} (true_false): 'correct' must be 'True' or 'False', got '{q['correct']}'"
        )
        return False
    return True


def _validate_short_answer(q: dict, index: int, report: ValidationReport) -> bool:
    if "answers" not in q:
        report.schema_errors.append(f"Q#{index} (short_answer): Missing 'answers'")
        return False
    answers = q["answers"]
    if isinstance(answers, list) and len(answers) == 0:
        report.schema_errors.append(f"Q#{index} (short_answer): Empty answers list")
        return False
    return True


def _validate_match(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    if "left" not in q:
        report.schema_errors.append(f"Q#{index} (match): Missing 'left'")
        valid = False
    if "right" not in q:
        report.schema_errors.append(f"Q#{index} (match): Missing 'right'")
        valid = False

    if valid:
        if len(q["left"]) != len(q["right"]):
            report.schema_errors.append(
                f"Q#{index} (match): left ({len(q['left'])}) and right ({len(q['right'])}) count mismatch"
            )
            valid = False

    return valid


def _validate_slider(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    for field_name in ("min", "max", "correct"):
        if field_name not in q:
            report.schema_errors.append(f"Q#{index} (slider): Missing '{field_name}'")
            valid = False

    if valid:
        mn, mx, correct = q["min"], q["max"], q["correct"]
        if not (mn <= correct <= mx):
            report.schema_errors.append(
                f"Q#{index} (slider): correct={correct} outside range [{mn}, {mx}] — AUTO-FIXING"
            )
            # Auto-fix: clamp correct to range, or adjust range
            if correct < mn:
                q["min"] = correct
                report.fixes_applied.append(f"Q#{index}: Slider min adjusted to {correct}")
            elif correct > mx:
                q["max"] = correct
                report.fixes_applied.append(f"Q#{index}: Slider max adjusted to {correct}")

    return valid


def _validate_memory(q: dict, index: int, report: ValidationReport) -> bool:
    if "pairs" not in q:
        report.schema_errors.append(f"Q#{index} (memory): Missing 'pairs'")
        return False
    if not isinstance(q["pairs"], dict) or len(q["pairs"]) < 2:
        report.schema_errors.append(f"Q#{index} (memory): 'pairs' must be object with 2+ entries")
        return False
    return True


def _validate_odd_one_out(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    if "options" not in q:
        report.schema_errors.append(f"Q#{index} (odd_one_out): Missing 'options'")
        return False
    if "correct" not in q:
        report.schema_errors.append(f"Q#{index} (odd_one_out): Missing 'correct'")
        return False

    if q["correct"] not in q["options"]:
        report.schema_errors.append(
            f"Q#{index} (odd_one_out): correct '{q['correct']}' not found in options"
        )
        valid = False

    return valid


def _validate_swipe_cards(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    for field_name in ("cards", "left_label", "right_label"):
        if field_name not in q:
            report.schema_errors.append(f"Q#{index} (swipe_cards): Missing '{field_name}'")
            valid = False

    if "cards" in q:
        for key, val in q["cards"].items():
            if val not in ("left", "right"):
                report.schema_errors.append(
                    f"Q#{index} (swipe_cards): Card '{key}' has value '{val}', must be 'left' or 'right'"
                )
                valid = False

    return valid


def _validate_word_scramble(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    if "answer" not in q:
        report.schema_errors.append(f"Q#{index} (word_scramble): Missing 'answer'")
        valid = False
    if "decoys" not in q:
        report.schema_errors.append(f"Q#{index} (word_scramble): Missing 'decoys'")
        valid = False
    return valid


def _validate_inline_dropdown(q: dict, index: int, report: ValidationReport) -> bool:
    valid = True
    if "text" not in q:
        report.schema_errors.append(f"Q#{index} (inline_dropdown): Missing 'text'")
        valid = False
    if "dropdowns" not in q:
        report.schema_errors.append(f"Q#{index} (inline_dropdown): Missing 'dropdowns'")
        valid = False
    else:
        for i, dd in enumerate(q["dropdowns"]):
            if "correct" not in dd:
                report.schema_errors.append(
                    f"Q#{index} (inline_dropdown): Dropdown {i} missing 'correct'"
                )
                valid = False
            if "options" not in dd:
                report.schema_errors.append(
                    f"Q#{index} (inline_dropdown): Dropdown {i} missing 'options'"
                )
                valid = False
            elif "correct" in dd and dd["correct"] not in dd["options"]:
                report.schema_errors.append(
                    f"Q#{index} (inline_dropdown): Dropdown {i} correct '{dd['correct']}' not in options"
                )
                valid = False

    return valid





def process_questions(
    questions: list[dict],
    filepath: str = "",
) -> tuple[list[dict], ValidationReport]:
    """
    Full processing pipeline for a list of questions:
    1. Add missing type fields
    2. Remove duplicates
    3. Validate schema
    4. Check code accuracy
    5. Generate report

    Returns (processed_questions, report)
    """
    report = ValidationReport(file_path=filepath)

    # Step 1: Add missing types
    questions = add_missing_types(questions, report)

    # Step 2: Remove duplicates
    questions = remove_duplicates(questions, report)

    # Step 3: Validate each question
    valid_questions = []
    for i, q in enumerate(questions):
        if validate_question(q, i, report):
            valid_questions.append(q)
        else:
            # Keep the question but mark it had issues
            valid_questions.append(q)

    # Step 4: Compute type distribution
    report.total_questions = len(valid_questions)
    report.type_distribution = dict(Counter(q.get("type", "unknown") for q in valid_questions))

    return valid_questions, report


def process_file(filepath: str) -> tuple[list[dict], ValidationReport]:
    """Load, process, and validate a single JSON file."""
    questions = load_json_file(filepath)
    if not questions:
        report = ValidationReport(file_path=filepath, total_questions=0)
        report.schema_errors.append("File is empty or contains no questions")
        return [], report

    return process_questions(questions, filepath)
