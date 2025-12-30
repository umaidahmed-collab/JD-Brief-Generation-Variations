#!/usr/bin/env python3
"""
JD to Brief Generator using Google Gemini 3.0

Generates comprehensive recruiter briefs from job descriptions using Gemini 3.0.
Processes all JDs with different temperatures (0.3, 0.5, 0.7) like GPT-4o pattern.

Usage:
    python generate_brief_gemini3.py              # Process all JDs at all temperatures
    python generate_brief_gemini3.py --temp 0.5   # Process all JDs at specific temperature
"""

import os
import sys
import argparse
import glob
import time
from pathlib import Path
from datetime import datetime

from google import genai

from prompts import BRIEF_GENERATION_PROMPT

# Gemini Configuration
GEMINI_API_KEY = "AIzaSyChWu2byrwLO13X9P1FrThcd1VgpFOgZIg"
MODEL = "gemini-3-flash-preview"  # Gemini 3.0
TEMPERATURES = [0.3, 0.5, 0.7]
# Different thinking budgets for generation variety
THINKING_BUDGETS = [1024, 4096, 8192]

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Rate limit handling
MAX_RETRIES = 5
RETRY_DELAY = 60  # seconds - longer delay for rate limits
DELAY_BETWEEN_JDS = 30  # seconds between JDs


def generate_brief_gemini3(job_description: str, temperature: float = 0.7, thinking_budget: int = 4096) -> str:
    """
    Generate a comprehensive recruiter brief from a job description using Gemini 3.0 with thinking.

    Args:
        job_description: The full job description text
        temperature: Controls randomness (0.0-1.0)
        thinking_budget: Token budget for model thinking/reasoning

    Returns:
        The generated brief as a string
    """
    prompt = f"""You are an expert recruitment consultant who creates detailed, easy-to-understand briefs for external recruiters.

{BRIEF_GENERATION_PROMPT.format(job_description=job_description)}"""

    print(f"  Generating brief using {MODEL} (temp={temperature}, thinking={thinking_budget})...")

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "thinking_config": {"thinking_budget": thinking_budget},
                    "max_output_tokens": 16000,
                }
            )
            # Extract text from response parts
            result_text = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    result_text += part.text
            return result_text if result_text else response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)  # Progressive backoff
                    print(f"    Rate limited. Waiting {wait_time}s before retry {attempt + 2}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Rate limit exceeded after {MAX_RETRIES} retries: {e}")
            else:
                raise e


def get_jd_files() -> list[tuple[int, str, str]]:
    """Get list of available JD files."""
    jds_dir = Path(__file__).parent / "jds"
    jd_files = sorted(glob.glob(str(jds_dir / "*.txt")))
    return [(i + 1, os.path.basename(f), f) for i, f in enumerate(jd_files)]


def process_single_jd(jd_path: str, output_dir: Path, temperature: float = 0.7, thinking_budget: int = 4096) -> str:
    """Process a single JD file and save the brief."""
    jd_name = Path(jd_path).stem

    # Read JD content
    with open(jd_path, "r") as f:
        jd_content = f.read()

    # Generate brief
    brief = generate_brief_gemini3(jd_content, temperature, thinking_budget)

    # Save brief (same format as GPT-4o outputs)
    output_file = output_dir / f"{jd_name}.md"
    with open(output_file, "w") as f:
        f.write(f"# Recruiter Brief: {jd_name}\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using {MODEL} (temp={temperature}, thinking={thinking_budget})*\n\n")
        f.write("---\n\n")
        f.write(brief)

    print(f"    ✓ Saved: {output_file}")
    return str(output_file)


def process_all_jds_at_temperature(temperature: float, thinking_budget: int = 4096, delay: int = 30) -> list[str]:
    """Process all JD files at a specific temperature and thinking budget."""
    jd_files = get_jd_files()

    # Create output directory with temp and thinking config
    output_dir = Path(__file__).parent / "outputs_gemini3" / f"temp_{temperature}_think_{thinking_budget}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Processing {len(jd_files)} JDs")
    print(f"Temperature: {temperature}, Thinking Budget: {thinking_budget}")
    print(f"Output directory: {output_dir}")
    print(f"Delay between JDs: {delay}s")
    print(f"{'='*60}")

    generated_files = []
    for idx, name, path in jd_files:
        try:
            print(f"\n[{idx}/{len(jd_files)}] {name}")
            output_file = process_single_jd(path, output_dir, temperature, thinking_budget)
            generated_files.append(output_file)

            # Add delay between JDs to avoid rate limits
            if idx < len(jd_files):
                print(f"    Waiting {delay}s before next JD...")
                time.sleep(delay)
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            # Still wait before continuing to next JD
            time.sleep(delay)
            continue

    return generated_files


def main():
    parser = argparse.ArgumentParser(description="Generate briefs using Gemini 3.0 with thinking")
    parser.add_argument("--temp", "-T", type=float, help="Specific temperature (default: all 0.3, 0.5, 0.7)")
    parser.add_argument("--thinking", "-t", type=int, help="Specific thinking budget (default: varies)")
    parser.add_argument("--delay", "-d", type=int, default=DELAY_BETWEEN_JDS, help=f"Delay between JDs in seconds (default: {DELAY_BETWEEN_JDS})")
    parser.add_argument("--list", "-l", action="store_true", help="List available JD files")
    args = parser.parse_args()

    if args.list:
        jds = get_jd_files()
        print("\nAvailable JD files:")
        for idx, name, _ in jds:
            print(f"  {idx:2}. {name}")
        return

    print("\n" + "=" * 60)
    print("GEMINI 3.0 BRIEF GENERATOR (with Thinking)")
    print(f"Model: {MODEL}")
    print(f"Temperatures: {TEMPERATURES}")
    print(f"Thinking Budgets: {THINKING_BUDGETS}")
    print("=" * 60)

    # Generate combinations of temperature and thinking budget
    temperatures = [args.temp] if args.temp else TEMPERATURES
    thinking_budgets = [args.thinking] if args.thinking else THINKING_BUDGETS

    all_generated = []

    # Process each combination
    for temp in temperatures:
        for thinking in thinking_budgets:
            generated = process_all_jds_at_temperature(temp, thinking, args.delay)
            all_generated.extend(generated)
            print(f"\n>>> Completed temp={temp}, thinking={thinking}: {len(generated)} briefs")

    print("\n" + "=" * 60)
    print(f"COMPLETED: Generated {len(all_generated)} briefs total")
    print("=" * 60)
    for f in all_generated:
        print(f"  ✓ {f}")


if __name__ == "__main__":
    main()

