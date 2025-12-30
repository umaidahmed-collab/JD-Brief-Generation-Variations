#!/usr/bin/env python3
"""
JD to Brief Generator using Google Gemini

Generates comprehensive recruiter briefs from job descriptions using Gemini models.
Supports both Google AI Studio (Flash) and Vertex AI (Pro).

Usage:
    python generate_brief_gemini.py                    # Process all JDs in jds/
    python generate_brief_gemini.py --jd 5             # Process specific JD
    python generate_brief_gemini.py --file path.txt   # Process single file
    python generate_brief_gemini.py --text "JD text"  # Process direct text
    python generate_brief_gemini.py --all-models      # Process with both Flash and Pro
"""

import os
import sys
import argparse
import glob
import time
from pathlib import Path
from datetime import datetime

from google import genai
from google.genai import types

from prompts import BRIEF_GENERATION_PROMPT

# Gemini Configuration - Google AI Studio (for Flash)
GEMINI_API_KEY = "AIzaSyChWu2byrwLO13X9P1FrThcd1VgpFOgZIg"

# Vertex AI Configuration (for Pro models) - requires gcloud auth
VERTEX_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "corelabsdocuments-dev")
VERTEX_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

DEFAULT_MODEL = "gemini-2.5-flash"
AVAILABLE_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]

# Models that require Vertex AI
VERTEX_MODELS = ["gemini-2.5-pro"]

# Initialize clients
ai_studio_client = genai.Client(api_key=GEMINI_API_KEY)
vertex_client = None  # Initialized lazily

def get_vertex_client():
    """Get or create Vertex AI client."""
    global vertex_client
    if vertex_client is None:
        vertex_client = genai.Client(
            vertexai=True,
            project=VERTEX_PROJECT_ID,
            location=VERTEX_LOCATION
        )
    return vertex_client

def get_client_for_model(model: str):
    """Get the appropriate client for the model."""
    if model in VERTEX_MODELS:
        return get_vertex_client()
    return ai_studio_client

# Rate limit handling
MAX_RETRIES = 3
RETRY_DELAY = 20  # seconds


def generate_brief_gemini(job_description: str, model: str = DEFAULT_MODEL, temperature: float = 0.7) -> str:
    """
    Generate a comprehensive recruiter brief from a job description using Gemini.

    Args:
        job_description: The full job description text
        model: Gemini model to use
        temperature: Controls randomness (0.0-1.0)

    Returns:
        The generated brief as a string
    """
    prompt = BRIEF_GENERATION_PROMPT.format(job_description=job_description)

    # Get the appropriate client for the model
    client = get_client_for_model(model)
    backend = "Vertex AI" if model in VERTEX_MODELS else "Google AI Studio"

    print(f"Generating brief using {model} via {backend} (temp={temperature})...")

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                    system_instruction="You are an expert recruitment consultant who creates detailed, easy-to-understand briefs for external recruiters."
                )
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < MAX_RETRIES - 1:
                    print(f"  Rate limited. Waiting {RETRY_DELAY}s before retry {attempt + 2}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise Exception(f"Rate limit exceeded after {MAX_RETRIES} retries: {e}")
            else:
                raise e


def get_jd_files() -> list[tuple[int, str, str]]:
    """Get list of available JD files."""
    jds_dir = Path(__file__).parent / "jds"
    jd_files = sorted(glob.glob(str(jds_dir / "*.txt")))
    return [(i + 1, os.path.basename(f), f) for i, f in enumerate(jd_files)]


def process_single_jd(jd_path: str, output_dir: Path, model: str = DEFAULT_MODEL, temperature: float = 0.7) -> str:
    """Process a single JD file and save the brief."""
    jd_name = Path(jd_path).stem
    print(f"\n{'='*60}")
    print(f"Processing: {jd_name}")
    print(f"{'='*60}")

    # Read JD content
    with open(jd_path, "r") as f:
        jd_content = f.read()

    # Generate brief
    brief = generate_brief_gemini(jd_content, model, temperature)

    # Save brief
    output_file = output_dir / f"{jd_name}_brief.md"
    with open(output_file, "w") as f:
        f.write(f"# Recruiter Brief: {jd_name}\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using {model}*\n\n")
        f.write("---\n\n")
        f.write(brief)

    print(f"Saved brief to: {output_file}")
    return str(output_file)


def process_all_jds(model: str = DEFAULT_MODEL, temperature: float = 0.7, delay: int = 5) -> list[str]:
    """Process all JD files in the jds directory."""
    jd_files = get_jd_files()
    # Create model-specific output directory
    model_suffix = model.replace("gemini-", "").replace(".", "_")
    output_dir = Path(__file__).parent / f"briefs_{model_suffix}"
    output_dir.mkdir(exist_ok=True)

    print(f"\nFound {len(jd_files)} JD files to process")
    print(f"Model: {model}")
    print(f"Output directory: {output_dir}")
    print(f"Delay between JDs: {delay}s (to avoid rate limits)\n")

    generated_files = []
    for idx, name, path in jd_files:
        try:
            output_file = process_single_jd(path, output_dir, model, temperature)
            generated_files.append(output_file)

            # Add delay between JDs to avoid rate limits
            if idx < len(jd_files):
                print(f"  Waiting {delay}s before next JD...")
                time.sleep(delay)
        except Exception as e:
            print(f"ERROR processing {name}: {e}")
            # Continue with next JD after error
            continue

    return generated_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate recruiter briefs from JDs using Gemini models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate_brief_gemini.py              # Process all JDs with default model
    python generate_brief_gemini.py --all-models # Process all JDs with ALL models
    python generate_brief_gemini.py --model gemini-2.5-pro  # Use specific model
    python generate_brief_gemini.py --jd 5       # Process JD #5 only
    python generate_brief_gemini.py --file jd.txt  # Process specific file
    python generate_brief_gemini.py --list       # List available JDs
        """
    )

    parser.add_argument(
        "--jd",
        type=int,
        help="Process specific JD by number (1-10)"
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to a specific JD file to process"
    )
    parser.add_argument(
        "--text", "-t",
        help="JD as direct text input"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (for --text or --file mode)"
    )
    parser.add_argument(
        "--temp", "-T",
        type=float,
        default=0.7,
        help="Temperature for generation (0.0-1.0, default: 0.7)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available JD files"
    )
    parser.add_argument(
        "--model", "-m",
        choices=AVAILABLE_MODELS,
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--all-models",
        action="store_true",
        help="Process with ALL available models (flash and pro)"
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        jds = get_jd_files()
        print("\nAvailable JD files:")
        print("-" * 50)
        for idx, name, _ in jds:
            print(f"  {idx:2}. {name}")
        print("-" * 50)
        return

    # Text mode
    if args.text:
        brief = generate_brief_gemini(args.text, args.model, args.temp)
        if args.output:
            Path(args.output).write_text(brief)
            print(f"Brief saved to: {args.output}")
        else:
            print("\n" + "=" * 60)
            print("RECRUITER BRIEF")
            print("=" * 60 + "\n")
            print(brief)
        return

    # Single file mode
    if args.file:
        if not Path(args.file).exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        model_suffix = args.model.replace("gemini-", "").replace(".", "_")
        output_dir = Path(args.output).parent if args.output else Path(__file__).parent / f"briefs_{model_suffix}"
        output_dir.mkdir(exist_ok=True)
        process_single_jd(args.file, output_dir, args.model, args.temp)
        return

    # Single JD by number
    if args.jd:
        jds = get_jd_files()
        if args.jd < 1 or args.jd > len(jds):
            print(f"Error: JD number must be between 1 and {len(jds)}", file=sys.stderr)
            sys.exit(1)
        _, name, path = jds[args.jd - 1]
        model_suffix = args.model.replace("gemini-", "").replace(".", "_")
        output_dir = Path(__file__).parent / f"briefs_{model_suffix}"
        output_dir.mkdir(exist_ok=True)
        process_single_jd(path, output_dir, args.model, args.temp)
        return

    # Determine which models to use
    models_to_run = AVAILABLE_MODELS if args.all_models else [args.model]

    # Process all JDs with selected model(s)
    all_generated = []
    for model in models_to_run:
        print("\n" + "=" * 60)
        print("GEMINI JD BRIEF GENERATOR")
        print(f"Model: {model}")
        print("=" * 60)

        generated = process_all_jds(model, args.temp)
        all_generated.extend(generated)

        print("\n" + "=" * 60)
        print(f"COMPLETED with {model}: Generated {len(generated)} briefs")
        print("=" * 60)
        for f in generated:
            print(f"  - {f}")

    if args.all_models:
        print("\n" + "=" * 60)
        print(f"ALL MODELS COMPLETED: Generated {len(all_generated)} total briefs")
        print("=" * 60)


if __name__ == "__main__":
    main()
