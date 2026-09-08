"""
Parse Constants.dart to extract all categories, topics, and their metadata.
"""
from __future__ import annotations
import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class TopicInfo:
    id: str
    title: str
    tier: str
    topics: list[str]
    category: str = ""
    output_dir: str = ""  # e.g., "Python"

    @property
    def output_path(self) -> str:
        """Return the relative output path for this topic's JSON file."""
        return f"{self.output_dir}/{self.id}.json"


@dataclass
class CategoryInfo:
    name: str
    topics: list[TopicInfo] = field(default_factory=list)

    @property
    def output_dir(self) -> str:
        """Return directory name used in v4/v5 structure (matches Constants.dart category name)."""
        return self.name


def parse_constants_dart(filepath: str) -> list[CategoryInfo]:
    """
    Parse Constants.dart and extract all categories with their topics.

    The Dart file has a specific structure:
    - Map<String, List<Map<String, dynamic>>> allTypes = { ... }
    - Each key is a category name
    - Each value is a list of topic maps with id, title, tier, topics
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Constants.dart not found at: {filepath}")

    content = path.read_text(encoding="utf-8")

    categories = []

    # Extract the allTypes map content between the opening { and closing };
    all_types_match = re.search(
        r"static\s+const\s+Map.*?allTypes\s*=\s*\{(.+?)\n\s*\};",
        content,
        re.DOTALL,
    )
    if not all_types_match:
        raise ValueError("Could not find allTypes map in Constants.dart")

    all_types_content = all_types_match.group(1)

    # Split by category: find each "CategoryName": [ ... ]
    # Pattern: "Category Name": [ ... ],  (where the list may span many lines)
    category_pattern = re.compile(
        r'"([^"]+)"\s*:\s*\[',
        re.DOTALL,
    )

    # Find all category starts
    category_starts = list(category_pattern.finditer(all_types_content))

    for i, match in enumerate(category_starts):
        cat_name = match.group(1)
        start_pos = match.end()

        # Find the end of this category's list (matching bracket)
        # We need to find the matching ] that closes this [
        bracket_depth = 1
        pos = start_pos
        while pos < len(all_types_content) and bracket_depth > 0:
            if all_types_content[pos] == "[":
                bracket_depth += 1
            elif all_types_content[pos] == "]":
                bracket_depth -= 1
            pos += 1

        cat_content = all_types_content[start_pos:pos - 1]
        category = CategoryInfo(name=cat_name)

        # Extract individual topic blocks within this category
        # Each topic is a { ... } block
        topic_blocks = _extract_topic_blocks(cat_content)

        for block in topic_blocks:
            topic = _parse_topic_block(block, cat_name, category.output_dir)
            if topic:
                category.topics.append(topic)

        categories.append(category)

    return categories


def _extract_topic_blocks(content: str) -> list[str]:
    """Extract individual { ... } blocks from category content."""
    blocks = []
    i = 0
    while i < len(content):
        if content[i] == "{":
            depth = 1
            start = i
            i += 1
            while i < len(content) and depth > 0:
                if content[i] == "{":
                    depth += 1
                elif content[i] == "}":
                    depth -= 1
                i += 1
            blocks.append(content[start:i])
        else:
            i += 1
    return blocks


def _parse_topic_block(block: str, category_name: str, output_dir: str) -> Optional[TopicInfo]:
    """Parse a single topic { ... } block into TopicInfo."""
    # Extract 'id'
    id_match = re.search(r"'id'\s*:\s*'([^']+)'", block)
    if not id_match:
        return None

    # Extract 'title'
    title_match = re.search(r"'title'\s*:\s*'([^']+)'", block)

    # Extract 'tier'
    tier_match = re.search(r"'tier'\s*:\s*'([^']+)'", block)

    # Extract 'topics' list
    topics_match = re.search(r"'topics'\s*:\s*\[(.*?)\]", block, re.DOTALL)

    topics_list = []
    if topics_match:
        topics_str = topics_match.group(1)
        # Match both single and double quoted strings, and backtick-quoted
        topic_items = re.findall(r'["\']([^"\']+)["\']|`([^`]+)`', topics_str)
        for groups in topic_items:
            # Each match returns a tuple of groups, pick the non-empty one
            topic = groups[0] if groups[0] else groups[1]
            topics_list.append(topic)

    return TopicInfo(
        id=id_match.group(1),
        title=title_match.group(1) if title_match else id_match.group(1),
        tier=tier_match.group(1) if tier_match else "free",
        topics=topics_list,
        category=category_name,
        output_dir=output_dir,
    )


def get_all_topics(filepath: str) -> dict[str, list[TopicInfo]]:
    """
    Convenience function: returns {category_name: [TopicInfo, ...]}
    """
    categories = parse_constants_dart(filepath)
    return {cat.name: cat.topics for cat in categories}


def get_topic_count(filepath: str) -> int:
    """Return total number of topics across all categories."""
    categories = parse_constants_dart(filepath)
    return sum(len(cat.topics) for cat in categories)


if __name__ == "__main__":
    import sys

    dart_file = sys.argv[1] if len(sys.argv) > 1 else "Constants.dart"
    categories = parse_constants_dart(dart_file)

    print(f"Found {len(categories)} categories:\n")
    total = 0
    for cat in categories:
        print(f"  {cat.name} ({cat.output_dir}/) — {len(cat.topics)} topics")
        for topic in cat.topics:
            print(f"    ├─ {topic.id}: {topic.title} [{topic.tier}]")
            print(f"    │  Topics: {', '.join(topic.topics[:5])}{'...' if len(topic.topics) > 5 else ''}")
            total += 1
        print()

    print(f"Total: {total} topics across {len(categories)} categories")
