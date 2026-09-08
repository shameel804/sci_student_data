"""
Enhanced merger that combines MCQ and other-type batches into a single
quiz file with proper interleaving and progressive difficulty.

Replaces the original merge_quizzes.py with smarter logic.
"""
from __future__ import annotations
import json
import random
from pathlib import Path
from .post_processor import load_json_file, process_questions, ValidationReport


def merge_batches(
    mcq_files: list[str],
    other_files: list[str],
    output_path: str,
    interleave_ratio: float = 0.90,
) -> ValidationReport:
    """
    Merge multiple MCQ and other-type batch files into a single quiz file.

    1. Loads and concatenates all MCQ batches (preserving batch order = difficulty)
    2. Loads and concatenates all other-type batches
    3. Post-processes both (dedup, validate, fix)
    4. Interleaves other types into the first `interleave_ratio` of MCQ questions
    5. Writes the final merged file

    Args:
        mcq_files: List of MCQ batch JSON file paths (ordered by difficulty)
        other_files: List of other-type batch JSON file paths
        output_path: Where to write the final merged JSON
        interleave_ratio: Fraction of MCQ section to interleave others into (default 90%)

    Returns:
        ValidationReport for the final merged output
    """
    # Step 1: Load all MCQ batches
    all_mcq = []
    for f in mcq_files:
        questions = load_json_file(f)
        if questions:
            print(f"  Loaded {len(questions)} MCQs from {Path(f).name}")
            all_mcq.extend(questions)

    # Step 2: Load all other-type batches
    all_other = []
    for f in other_files:
        questions = load_json_file(f)
        if questions:
            print(f"  Loaded {len(questions)} other-types from {Path(f).name}")
            all_other.extend(questions)

    if not all_mcq and not all_other:
        report = ValidationReport(file_path=output_path)
        report.schema_errors.append("No questions found in any batch file")
        return report

    # Step 3: Post-process MCQ questions
    print(f"\n  Processing {len(all_mcq)} MCQ questions...")
    all_mcq, mcq_report = process_questions(all_mcq, "mcq_batches")
    print(mcq_report.summary())

    # Step 4: Post-process other questions
    print(f"\n  Processing {len(all_other)} other-type questions...")
    all_other, other_report = process_questions(all_other, "other_batches")
    print(other_report.summary())

    # Step 5: Interleave
    merged = _interleave(all_mcq, all_other, interleave_ratio)

    # Step 6: Final validation pass on merged result
    print(f"\n  Final validation on {len(merged)} merged questions...")
    merged, final_report = process_questions(merged, output_path)

    # Step 7: Write output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=4, ensure_ascii=False)

    print(f"\n  ✅ Written {len(merged)} questions to {output_path}")
    print(final_report.summary())

    return final_report


def _interleave(
    mcq: list[dict],
    other: list[dict],
    ratio: float = 0.90,
) -> list[dict]:
    """
    Insert other-type questions throughout the first `ratio` portion of the
    MCQ list, keeping difficulty progression intact.

    The MCQ list is assumed to be ordered by difficulty (batch 1 first, batch 6 last).
    Other types are distributed evenly within the first 90%.
    """
    if not other:
        return mcq

    if not mcq:
        return other

    # Calculate insertion boundary
    boundary = int(len(mcq) * ratio)

    # Generate evenly-spaced insertion positions
    start_index = min(5, boundary)  # Skip the first few MCQs
    num_inserts = len(other)

    if boundary <= start_index:
        # Not enough MCQs, just append
        return mcq + other

    # Generate sorted random positions within the boundary
    positions = sorted(
        random.randint(start_index, boundary) for _ in range(num_inserts)
    )

    # Insert other questions (account for array shifting)
    merged = list(mcq)
    for i, item in enumerate(other):
        merged.insert(positions[i] + i, item)

    return merged


def merge_topic(
    staging_dir: str,
    category_name: str,
    topic_id: str,
    output_dir: str,
    version: str = "v5",
) -> ValidationReport:
    """
    Merge all batches for a single topic from staging into the final output.

    Looks for files in: staging/{category_name}/{topic_id}/raw/
    Outputs to: {version}/{output_dir}/{topic_id}.json
    """
    raw_dir = Path(staging_dir) / category_name / topic_id / "raw"

    if not raw_dir.exists():
        report = ValidationReport(file_path=str(raw_dir))
        report.schema_errors.append(f"Raw directory not found: {raw_dir}")
        return report

    # Collect MCQ batch files (ordered)
    mcq_files = sorted(
        str(f) for f in raw_dir.glob("mcq_batch*.json")
    )

    # Collect other-type batch files (ordered)
    other_files = sorted(
        str(f) for f in raw_dir.glob("other_batch*.json")
    )

    if not mcq_files and not other_files:
        report = ValidationReport(file_path=str(raw_dir))
        report.schema_errors.append(f"No batch files found in {raw_dir}")
        return report

    # Determine output path
    output_path = str(Path(version) / output_dir / f"{topic_id}.json")

    print(f"\n{'='*60}")
    print(f"Merging: {category_name} / {topic_id}")
    print(f"  MCQ batches: {len(mcq_files)}")
    print(f"  Other batches: {len(other_files)}")
    print(f"  Output: {output_path}")
    print(f"{'='*60}")

    return merge_batches(mcq_files, other_files, output_path)
