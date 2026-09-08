"""
Auto-generate self-contained AI-agent-ready prompt files for each topic.

These prompts are designed to be read directly from disk by an AI agent
(like Antigravity/Claude) that has file read/write access. The agent reads
the prompt, generates the quiz JSON, and writes it to the corresponding
output file path specified in the prompt.

All quality rules from the v4/v5 analysis are baked into each prompt.
"""
from __future__ import annotations
import os
from pathlib import Path
from .parse_constants import TopicInfo, CategoryInfo


# MCQ batch definitions: (batch_number, difficulty_label)
MCQ_BATCHES = [
    (1, "Beginner"),
    (2, "Beginner-Intermediate"),
    (3, "Intermediate"),
    (4, "Intermediate-Advanced"),
    (5, "Advanced-Expert"),
    (6, "Expert"),
]

# Other types batch definitions
OTHER_BATCHES = [
    (1, "Beginner-Intermediate"),
    (2, "Intermediate-Advanced"),
]


QUALITY_RULES = """
## QUALITY RULES (MANDATORY — from production data analysis)

### Anti-Duplication Rules
1. **ZERO DUPLICATE QUESTIONS**: Every single question must be unique. Do NOT repeat the same question text even with different options.
2. **Distinct Learning Objectives**: Each question must test a DIFFERENT concept or sub-topic. If you've asked about "valid variable names", don't ask about it again with different examples.
3. **Vary Question Stems**: Do NOT overuse generic stems like "What is the output of this code?" — use a maximum of 20% of questions with this stem. Use varied phrasings like:
   - "What value does X hold after this code runs?"
   - "Which statement about X is correct?"
   - "What error occurs when..."
   - "How does Python handle..."

### Schema Rules
4. **EVERY question MUST have an explicit `"type"` field**. Never omit it. Valid types for MCQ: `"mcq"`.
5. **MCQ must have EXACTLY 4 options** in the `"o"` array. No more, no less.
6. **First option in `"o"` MUST be the correct answer**. Always.
7. **No option may contain `\\n` or `\\t`**. Keep options on one line.
8. **BALANCED OPTION LENGTH (CRITICAL — ZERO GIVEAWAY ANSWERS)**:
   - All 4 options in `"o"` MUST be **almost the same length** and detail level.
   - **NEVER** make the first option (the correct answer) noticeably longer, more elaborate, or more detailed than the distractors (wrong options).
   - If the correct answer is an explanatory sentence or clause (e.g., 12–15 words), all 3 distractors MUST also be explanatory clauses of similar length and structure.
   - If distractors are short (e.g., 2–4 words), the correct answer MUST also be short.
   - A noticeably longer correct answer makes the question trivially easy to predict. Ensure all distractors are equally plausible, detailed, and length-matched.

### Content Accuracy Rules
9. **Verify all factual claims**: Ensure that the correct answer is universally accepted as true in the scientific community.
10. **Avoid ambiguous questions**: Do not ask questions where multiple options could be considered correct under different interpretations.

### Encoding Rules
12. **NEVER use LaTeX, MathJax, or backslashes**: no \\alpha, no \\mu, no \\bar{x}, no \\( \\), no $$ etc.
13. **NEVER use Unicode math symbols**: no α, β, μ, σ, x̄, ±, ≤, ≥, ≠, √ etc.
14. Use ONLY plain ASCII + simple Markdown (**bold**, *italic*, `code`).

### Topic Adherence
15. **STRICT TOPIC ADHERENCE**: You MUST ONLY generate questions for the specific topics listed. DO NOT generate questions for any unrequested topics.
16. **Cover ALL listed topics**: Every topic in the list must have at least 2-3 questions. Don't skip any.
17. **NO GENERATION SCRIPTS**: You MUST use your AI knowledge to manually generate every single question. DO NOT write a Python script (or any other code) to programmatically generate the datasets. Script-generated questions are low quality and strictly forbidden. Pacing across turns is permitted to avoid token limits.
"""




def _build_mcq_prompt(
    category_name: str,
    topic: TopicInfo,
    batch_num: int,
    difficulty: str,
    output_path: str,
) -> str:
    """Build a complete, self-contained MCQ prompt for an AI agent."""

    topics_formatted = "\n".join(f"  - {t}" for t in topic.topics)

    return f"""# QUIZ GENERATION TASK

## Instructions
You are generating quiz questions for a production quiz app. Read this prompt carefully and write the output JSON to the file path specified below.

**Category**: {category_name}
**Title**: {topic.title}
**Batch**: {batch_num} of {len(MCQ_BATCHES)}
**Difficulty**: {difficulty}
**Output File**: `{output_path}`

## Topics to Cover
{topics_formatted}

## Output Format
Write a valid JSON array to the output file. Each element is a question object. Example:

```json
[
    {{
        "q": "Which of the following represents Newton's second law of motion?",
        "type": "mcq",
        "o": [
            "F = ma",
            "E = mc^2",
            "v = u + at",
            "F = G(m1m2)/r^2"
        ]
    }},
    {{
        "q": "What is the powerhouse of the cell?",
        "type": "mcq",
        "o": [
            "Mitochondria",
            "Nucleus",
            "Ribosome",
            "Endoplasmic reticulum"
        ]
    }}
]
```

## Question Type: MCQ Only
- `"type"`: MUST always be `"mcq"` (NEVER omit this field)
- `"o"`: Array of exactly 4 options. First option = correct answer.
- `"q"`: The question text.
- **CRITICAL OPTION LENGTH REQUIREMENT**: All 4 options in `"o"` MUST be almost the same length. Do NOT make the correct answer (first option) significantly longer or more detailed than the distractors. Distractors must match the correct answer in length, detail, and tone so learners cannot predict the answer based on length.

## Mix Requirements
- Generate **100+ questions** at `{difficulty}` difficulty level.
- Gradually increase difficulty within the batch.
{QUALITY_RULES}

## FINAL REMINDER
- Output MUST be a valid JSON array.
- Write the output to: `{output_path}`
- Generate 100+ questions. All must be `"mcq"` type with the `"type"` field explicitly set.
- First option in `"o"` is ALWAYS the correct answer.
- **ALL 4 OPTIONS MUST BE ALMOST EQUAL IN LENGTH**. Never create a conspicuously long correct answer with short distractors.
- EVERY question must cover a DISTINCT learning objective from the topics listed above.
"""


def _build_other_prompt(
    category_name: str,
    topic: TopicInfo,
    batch_num: int,
    difficulty: str,
    output_path: str,
) -> str:
    """Build a complete, self-contained other-types prompt for an AI agent."""

    topics_formatted = "\n".join(f"  - {t}" for t in topic.topics)

    return f"""# QUIZ GENERATION TASK (Interactive Question Types)

## Instructions
You are generating interactive quiz questions for a production quiz app. Read this prompt carefully and write the output JSON to the file path specified below.

**Category**: {category_name}
**Title**: {topic.title}
**Batch**: {batch_num} of {len(OTHER_BATCHES)}
**Difficulty**: {difficulty}
**Output File**: `{output_path}`

## Topics to Cover
{topics_formatted}

## Output Format
Write a valid JSON array to the output file. Each element is a question object with a specific `"type"` field.

### All 10 Question Types with Examples:

```json
[
    {{
        "q": "What is the chemical symbol for Gold?",
        "type": "short_answer",
        "answers": ["Au"],
        "isCaseSensitive": true
    }},
    {{
        "q": "The ______ organelle is known as the powerhouse of the cell.",
        "type": "fill_blank",
        "answers": ["mitochondria"],
        "other_options": ["nucleus", "ribosome", "vacuole"]
    }},
    {{
        "q": "Match the planets with their descriptions:",
        "type": "match",
        "left": ["Mars", "Jupiter", "Earth", "Venus"],
        "right": ["Red planet", "Largest planet", "Has life", "Hottest planet"]
    }},
    {{
        "q": "Electrons have a positive charge.",
        "type": "true_false",
        "correct": "False"
    }},
    {{
        "q": "How many bones are in the adult human body?",
        "type": "slider",
        "min": 100,
        "max": 300,
        "correct": 206
    }},
    {{
        "q": "Match the organelle with its function by flipping pairs.",
        "type": "memory",
        "pairs": {{
            "Mitochondria": "Energy production",
            "Nucleus": "Control center",
            "Ribosome": "Protein synthesis"
        }}
    }},
    {{
        "q": "Which of these is NOT a noble gas?",
        "type": "odd_one_out",
        "options": ["Helium", "Neon", "Argon", "Oxygen"],
        "correct": "Oxygen"
    }},
    {{
        "q": "Swipe RIGHT for mammals, LEFT for reptiles",
        "type": "swipe_cards",
        "left_label": "Reptile",
        "right_label": "Mammal",
        "cards": {{
            "Human": "right",
            "Snake": "left",
            "Whale": "right",
            "Lizard": "left"
        }}
    }},
    {{
        "q": "What is the force that pulls objects toward Earth?",
        "type": "word_scramble",
        "answer": "GRAVITY",
        "decoys": "XZ"
    }},
    {{
        "q": "Complete the sentence:",
        "type": "inline_dropdown",
        "text": "The [0] is the center of our solar system, and the [1] orbits the Earth.",
        "dropdowns": [
            {{"correct": "Sun", "options": ["Moon", "Sun", "Mars"]}},
            {{"correct": "Moon", "options": ["Sun", "Moon", "Venus"]}}
        ]
    }}
]
```

## Type-Specific Rules

### 1. Short Answer (`"short_answer"`)
- ONLY for questions with a specific, factual answer (e.g., keywords, function names, symbols).
- `"answers"`: List ALL acceptable answers (synonyms, spellings).
- `"isCaseSensitive"`: `true` if capitalization matters, `false` otherwise.
- Do NOT use for open-ended questions with many possible answers.

### 2. Fill-in-the-Blank (`"fill_blank"`)
- Question text MUST contain `______` (6 underscores) as blank placeholder.
- `"answers"`: List with exactly one item per blank, in order.
- `"other_options"`: 3-4 plausible wrong alternatives.

### 3. Match (`"match"`)
- `"left"` and `"right"` must have the SAME number of items (4-6 recommended).
- Correct matches are aligned by index (left[0] matches right[0]).

### 4. True/False (`"true_false"`)
- `"correct"`: Must be exactly `"True"` or `"False"` (capitalized string).
- Statements must be clear and unambiguous.

### 5. Slider (`"slider"`)
- `"min"`, `"max"`: Integer bounds.
- `"correct"`: The exact correct number. **MUST satisfy: min <= correct <= max**.
- CRITICAL: Never set correct outside the min/max range.

### 6. Memory Grid (`"memory"`)
- `"pairs"`: Object with 3-6 key-value pairs.
- Keys = concepts/terms, Values = definitions/descriptions.

### 7. Odd One Out (`"odd_one_out"`)
- `"options"`: List of 4-9 items where all but one share a trait.
- `"correct"`: The odd one out. MUST exactly match one item in `"options"`.

### 8. Swipe Cards (`"swipe_cards"`)
- `"left_label"`, `"right_label"`: Category labels.
- `"cards"`: Object with 3-6 entries. Values MUST be `"left"` or `"right"`.

### 9. Word Scramble (`"word_scramble"`)
- `"answer"`: One-word answer in ALL CAPS.
- `"decoys"`: 2-4 random uppercase letters for scrambling.

### 10. Inline Dropdown (`"inline_dropdown"`)
- `"text"`: Sentence with `[0]`, `[1]`, etc. as placeholders.
- `"dropdowns"`: Array of objects, each with `"correct"` and `"options"` (list of 3 including correct).

## Distribution (100 questions per batch)
Generate EXACTLY this mix, evenly distributed (DO NOT group same types together):
- Short answer: 10 questions
- Fill-in-the-blank: 10 questions
- True/False: 10 questions
- Match: 10 questions
- Slider: 10 questions
- Memory: 10 questions
- Odd One Out: 10 questions
- Swipe Cards: 10 questions
- Word Scramble: 10 questions
- Inline Dropdown: 10 questions
{QUALITY_RULES}

## FINAL REMINDER
- Output MUST be a valid JSON array.
- Write the output to: `{output_path}`
- Generate 100 questions with the exact type distribution above.
- EVERY question MUST have an explicit `"type"` field.
- Gradually increase difficulty within the batch.
- EVERY question must cover a DISTINCT learning objective from the topics listed above.
"""


def generate_master_instructions(
    staging_dir: str,
    categories: list[CategoryInfo],
    target_category: str | None = None,
    target_topic: str | None = None,
) -> str:
    """
    Generate a master INSTRUCTIONS.md file that tells the AI agent
    exactly what to do: read each prompt, generate content, write output.
    """
    staging = Path(staging_dir)

    # Collect all prompt/output pairs
    tasks = []
    for cat in categories:
        if target_category and cat.name != target_category:
            continue
        for topic in cat.topics:
            if target_topic and topic.id != target_topic:
                continue

            topic_dir = staging / cat.name / topic.id

            # MCQ batches
            for batch_num, difficulty in MCQ_BATCHES:
                prompt_file = topic_dir / "prompts" / f"mcq_batch{batch_num}_prompt.txt"
                output_file = topic_dir / "raw" / f"mcq_batch{batch_num}.json"
                tasks.append({
                    "category": cat.name,
                    "topic": topic.title,
                    "topic_id": topic.id,
                    "batch": f"MCQ Batch {batch_num} ({difficulty})",
                    "prompt": str(prompt_file),
                    "output": str(output_file),
                })

            # Other batches
            for batch_num, difficulty in OTHER_BATCHES:
                prompt_file = topic_dir / "prompts" / f"other_batch{batch_num}_prompt.txt"
                output_file = topic_dir / "raw" / f"other_batch{batch_num}.json"
                tasks.append({
                    "category": cat.name,
                    "topic": topic.title,
                    "topic_id": topic.id,
                    "batch": f"Other Types Batch {batch_num} ({difficulty})",
                    "prompt": str(prompt_file),
                    "output": str(output_file),
                })

    # Build the instructions document
    instructions = f"""# Quiz Generation — AI Agent Instructions

## Overview
You are generating quiz data for a production Science quiz app. This file contains
the complete list of tasks. For each task, read the prompt file, generate the quiz
JSON following ALL rules in the prompt, and write the output to the specified output file.

## Total Tasks: {len(tasks)}

## Workflow
For EACH task below:
1. **Read** the prompt file (contains all rules, examples, and quality requirements)
2. **Generate** the quiz JSON directly using your LLM knowledge (NO scripts!)
3. **Write** the valid JSON array to the output file path specified in the prompt
4. **Update `task.md`**: Mark the completed task in `task.md` to track your progress
5. **Move to the next task in the group**
6. **Pause when group completes**: When a full group of batches for a topic (6 MCQ batches + 2 other type batches) is completed, pause and ask the user to type `"continue"` to proceed to the next topic.

**CRITICAL EXECUTION RULE (Sequential Across Multiple Turns):**
- **Process sequentially across multiple turns**: Work through the tasks topic-by-topic. You can and should pause when a full group of batches is completed (i.e., 6 MCQ batches and 2 other type batches for a topic, totaling 8 files). Once a group is completed, stop your turn and prompt the user to type `"continue"` to generate the next topic.
- **Strictly sequential within each group**: You MUST generate the batches **SEQUENTIALLY** (one by one, not simultaneously). This is critical so you maintain context of what was generated in earlier batches, preventing duplicate questions across the topic when merged.
- **ABSOLUTELY NO PYTHON GENERATION SCRIPTS**: Do NOT attempt to create Python scripts, programs, or templates to generate the quiz content. Script-generated questions lack depth and quality, and are strictly forbidden. You must write the questions directly using your own LLM intelligence.

## Critical Rules
- Output MUST be a valid JSON array (no markdown, no ```json``` wrappers)
- Follow ALL quality rules in each prompt (anti-duplication, schema, accuracy)
- **BALANCED OPTION LENGTH**: All 4 options in every MCQ must be almost equal in length and detail. Never make the correct answer (first option) conspicuously longer than the distractors.
- Do NOT skip any tasks
- Each output file should contain 100+ questions
- NO GENERATION SCRIPTS: You MUST generate the questions using your LLM knowledge. DO NOT write a Python script (or any other code) to programmatically generate the questions.
- Update `task.md` properly as you progress.

## Task List

"""
    for i, task in enumerate(tasks, 1):
        instructions += f"""### Task {i}/{len(tasks)}
- **Category**: {task['category']}
- **Topic**: {task['topic']}
- **Batch**: {task['batch']}
- **Read prompt from**: `{task['prompt']}`
- **Write output to**: `{task['output']}`

"""

    instructions += """## After Completion
Once all tasks are done, run the post-processing pipeline:
```bash
python3 generate_pipeline.py process --all
```
This will validate, deduplicate, merge, and output the final quiz files.
"""

    instructions_path = staging / "INSTRUCTIONS.md"
    instructions_path.write_text(instructions, encoding="utf-8")

    return str(instructions_path)


def generate_prompts_for_topic(
    topic: TopicInfo,
    category_name: str,
    staging_dir: str,
) -> dict[str, str]:
    """
    Generate all prompt files for a single topic and save to staging directory.
    Returns dict of {prompt_filename: output_filepath}
    """
    topic_dir = Path(staging_dir) / category_name / topic.id
    prompts_dir = topic_dir / "prompts"
    raw_dir = topic_dir / "raw"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    generated = {}

    # Generate MCQ batch prompts
    for batch_num, difficulty in MCQ_BATCHES:
        output_path = str(raw_dir / f"mcq_batch{batch_num}.json")
        prompt = _build_mcq_prompt(
            category_name, topic, batch_num, difficulty, output_path
        )
        filename = f"mcq_batch{batch_num}_prompt.txt"
        filepath = prompts_dir / filename
        filepath.write_text(prompt, encoding="utf-8")
        generated[filename] = output_path

    # Generate other-types batch prompts
    for batch_num, difficulty in OTHER_BATCHES:
        output_path = str(raw_dir / f"other_batch{batch_num}.json")
        prompt = _build_other_prompt(
            category_name, topic, batch_num, difficulty, output_path
        )
        filename = f"other_batch{batch_num}_prompt.txt"
        filepath = prompts_dir / filename
        filepath.write_text(prompt, encoding="utf-8")
        generated[filename] = output_path

    return generated


def generate_prompts_for_category(
    category: CategoryInfo,
    staging_dir: str,
    topic_id: str | None = None,
) -> int:
    """
    Generate prompts for all topics in a category (or a single topic).
    Returns the number of prompt files generated.
    """
    count = 0
    for topic in category.topics:
        if topic_id and topic.id != topic_id:
            continue

        generated = generate_prompts_for_topic(
            topic=topic,
            category_name=category.name,
            staging_dir=staging_dir,
        )
        count += len(generated)
        print(f"  ✓ {topic.title} ({topic.id}) — {len(generated)} prompts generated")

    return count
