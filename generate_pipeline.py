#!/usr/bin/env python3
"""
Quiz Generation Pipeline — Main CLI

Usage:
    # Generate prompts for all topics in a category
    python3 generate_pipeline.py prompts "NEET Preparation"
    python3 generate_pipeline.py prompts --all

    # Generate prompts for a single topic
    python3 generate_pipeline.py prompts "NEET Preparation" --topic biology

    # Process staged AI outputs → validate + merge + output
    python3 generate_pipeline.py process "NEET Preparation"
    python3 generate_pipeline.py process "NEET Preparation" --topic biology
    python3 generate_pipeline.py process --all

    # Validate an existing JSON file
    python3 generate_pipeline.py validate v5/NEET Preparation/biology.json

    # Show status of all topics
    python3 generate_pipeline.py status
    python3 generate_pipeline.py status "NEET Preparation"
"""
import argparse
import json
import sys
from pathlib import Path

from pipeline.parse_constants import parse_constants_dart, CategoryInfo
from pipeline.prompt_generator import (
    generate_prompts_for_category,
    generate_master_instructions,
)
from pipeline.post_processor import process_file, ValidationReport
from pipeline.merger import merge_topic


# Configuration
CONSTANTS_FILE = "Constants.dart"
STAGING_DIR = "staging"
DEFAULT_VERSION = "v5"


def cmd_prompts(args):
    """Generate prompt files for AI agent to read."""
    categories = parse_constants_dart(CONSTANTS_FILE)

    if args.all:
        target_categories = categories
    else:
        target_categories = [c for c in categories if c.name == args.category]
        if not target_categories:
            print(f"❌ Category '{args.category}' not found.")
            print(f"Available: {', '.join(c.name for c in categories)}")
            sys.exit(1)

    total_prompts = 0
    for cat in target_categories:
        print(f"\n📝 Generating prompts for: {cat.name}")
        count = generate_prompts_for_category(
            category=cat,
            staging_dir=STAGING_DIR,
            topic_id=args.topic,
        )
        total_prompts += count

    # Generate master instructions file
    instructions_path = generate_master_instructions(
        staging_dir=STAGING_DIR,
        categories=target_categories,
        target_category=args.category if not args.all else None,
        target_topic=args.topic,
    )

    print(f"\n{'='*60}")
    print(f"✅ Generated {total_prompts} prompt files")
    print(f"📋 Master instructions: {instructions_path}")
    print(f"\n📌 Next step: Tell your AI agent to read {instructions_path}")
    print(f"   and follow the instructions to generate quiz data.")
    print(f"{'='*60}")


def cmd_process(args):
    """Process staged AI outputs: validate, deduplicate, merge, output."""
    categories = parse_constants_dart(CONSTANTS_FILE)

    if args.all:
        target_categories = categories
    else:
        target_categories = [c for c in categories if c.name == args.category]
        if not target_categories:
            print(f"❌ Category '{args.category}' not found.")
            sys.exit(1)

    version = args.version or DEFAULT_VERSION
    reports = []

    for cat in target_categories:
        for topic in cat.topics:
            if args.topic and topic.id != args.topic:
                continue

            report = merge_topic(
                staging_dir=STAGING_DIR,
                category_name=cat.name,
                topic_id=topic.id,
                output_dir=cat.output_dir,
                version=version,
            )
            reports.append((f"{cat.name}/{topic.id}", report))

    # Print summary
    print(f"\n{'='*60}")
    print(f"PROCESSING SUMMARY")
    print(f"{'='*60}")
    total_questions = 0
    total_dupes = 0
    total_errors = 0
    for name, report in reports:
        status = "✅" if not report.has_errors() else "⚠️"
        print(f"  {status} {name}: {report.total_questions} questions")
        total_questions += report.total_questions
        total_dupes += report.duplicates_removed
        total_errors += len(report.schema_errors)

    print(f"\nTotal: {total_questions} questions, {total_dupes} duplicates removed, {total_errors} errors")


def cmd_validate(args):
    """Validate an existing JSON file."""
    filepath = args.file
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    print(f"🔍 Validating: {filepath}")
    questions, report = process_file(filepath)

    print(f"\n{report.summary()}")

    if report.has_errors():
        print(f"\n❌ Validation failed with {len(report.schema_errors)} errors")
        sys.exit(1)
    else:
        print(f"\n✅ Validation passed!")

    # Optionally save the fixed version
    if args.fix:
        output = args.output or filepath
        with open(output, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=4, ensure_ascii=False)
        print(f"💾 Fixed version saved to: {output}")


def cmd_status(args):
    """Show status of all topics: which have prompts, raw data, and final output."""
    categories = parse_constants_dart(CONSTANTS_FILE)
    staging = Path(STAGING_DIR)
    version = args.version or DEFAULT_VERSION

    if args.category:
        categories = [c for c in categories if c.name == args.category]

    for cat in categories:
        print(f"\n📦 {cat.name} ({cat.output_dir}/)")
        print(f"  {'Topic':<25} {'Prompts':>8} {'Raw':>8} {'Output':>8} {'Status'}")
        print(f"  {'─'*70}")

        for topic in cat.topics:
            topic_dir = staging / cat.name / topic.id

            # Check prompts
            prompts_dir = topic_dir / "prompts"
            prompt_count = len(list(prompts_dir.glob("*.txt"))) if prompts_dir.exists() else 0

            # Check raw outputs
            raw_dir = topic_dir / "raw"
            raw_count = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0

            # Check final output
            output_path = Path(version) / cat.output_dir / f"{topic.id}.json"
            has_output = output_path.exists()
            output_size = ""
            if has_output:
                try:
                    with open(output_path) as f:
                        data = json.load(f)
                    output_size = f"{len(data)}q"
                except Exception:
                    output_size = "err"

            # Determine status
            if has_output:
                status = f"✅ Done ({output_size})"
            elif raw_count > 0:
                status = "🔄 Ready to process"
            elif prompt_count > 0:
                status = "📝 Prompts ready"
            else:
                status = "⬜ Not started"

            print(f"  {topic.title:<25} {prompt_count:>8} {raw_count:>8} {'Yes' if has_output else 'No':>8} {status}")


def main():
    parser = argparse.ArgumentParser(
        description="Quiz Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate_pipeline.py prompts "NEET Preparation"
  python3 generate_pipeline.py prompts "NEET Preparation" --topic biology
  python3 generate_pipeline.py prompts --all
  python3 generate_pipeline.py process "NEET Preparation" --topic biology
  python3 generate_pipeline.py validate v5/NEET Preparation/biology.json
  python3 generate_pipeline.py status
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # prompts command
    prompts_parser = subparsers.add_parser("prompts", help="Generate AI prompt files")
    prompts_parser.add_argument("category", nargs="?", help="Category name (e.g., 'NEET Preparation')")
    prompts_parser.add_argument("--all", action="store_true", help="Generate for all categories")
    prompts_parser.add_argument("--topic", help="Single topic ID (e.g., 'basic')")

    # process command
    process_parser = subparsers.add_parser("process", help="Process staged AI outputs")
    process_parser.add_argument("category", nargs="?", help="Category name")
    process_parser.add_argument("--all", action="store_true", help="Process all categories")
    process_parser.add_argument("--topic", help="Single topic ID")
    process_parser.add_argument("--version", help=f"Output version dir (default: {DEFAULT_VERSION})")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an existing JSON file")
    validate_parser.add_argument("file", help="Path to JSON file to validate")
    validate_parser.add_argument("--fix", action="store_true", help="Save fixed version")
    validate_parser.add_argument("--output", help="Output path for fixed file")

    # status command
    status_parser = subparsers.add_parser("status", help="Show topic status")
    status_parser.add_argument("category", nargs="?", help="Category name (optional)")
    status_parser.add_argument("--version", help=f"Version dir to check (default: {DEFAULT_VERSION})")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "prompts":
        if not args.category and not args.all:
            print("❌ Specify a category name or use --all")
            sys.exit(1)
        cmd_prompts(args)
    elif args.command == "process":
        if not args.category and not args.all:
            print("❌ Specify a category name or use --all")
            sys.exit(1)
        cmd_process(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
