import os
import json
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Set your Groq API key as an environment variable:
# PowerShell:
#   $env:GROQ_API_KEY="your_api_key"

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required.")

# Groq model
MODEL = "openai/gpt-oss-120b"

# Output format: "json" or "txt"
OUTPUT_FORMAT = "json"

# Output directory
OUTPUT_DIR = "output"


# ---------------------------------------------------------------------------
# Initialize Groq client
# ---------------------------------------------------------------------------

client = Groq(api_key=API_KEY)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# RFP Prompt
# ---------------------------------------------------------------------------

prompt = """
Create a comprehensive and realistic Request for Proposal (RFP)
for a Mobile Application Redesign project.

The RFP must contain the following sections:

1. Executive Summary
2. Project Objectives
3. Scope of Work
4. Functional Requirements
5. Technical Requirements
6. UI/UX and Design Requirements
7. Deliverables
8. Project Timeline
9. Submission Guidelines
10. Vendor Evaluation Criteria
11. Budget and Commercial Requirements
12. Terms and Conditions

Make the RFP realistic enough to resemble a real-world procurement
document that could be published by an organization looking for
technology vendors.

Include specific requirements, deliverables, deadlines, evaluation
criteria, and technical details.

Do not invent a real company name. Use a fictional organization.
"""


# ---------------------------------------------------------------------------
# Generate RFP
# ---------------------------------------------------------------------------

print(
    f"Generating RFP in '{OUTPUT_FORMAT.upper()}' format "
    f"using Groq ({MODEL})...\n"
)


if OUTPUT_FORMAT.lower() == "json":

    prompt += """
    
Return ONLY valid JSON.

Use exactly this structure:

{
    "title": "...",
    "issuing_organization": "...",
    "project_type": "...",
    "executive_summary": "...",
    "project_objectives": [],
    "scope_of_work": [],
    "functional_requirements": [],
    "technical_requirements": [],
    "design_requirements": [],
    "deliverables": [],
    "project_timeline": [],
    "submission_guidelines": [],
    "vendor_evaluation_criteria": [],
    "budget_requirements": [],
    "terms_and_conditions": []
}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert procurement specialist and "
                    "RFP writer. Generate realistic, detailed and "
                    "professionally structured RFP documents."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_object"
        },
        temperature=0.7
    )

else:

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert procurement specialist and "
                    "RFP writer. Generate realistic and detailed "
                    "RFP documents."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )


# ---------------------------------------------------------------------------
# Extract response
# ---------------------------------------------------------------------------

rfp_content = response.choices[0].message.content


# ---------------------------------------------------------------------------
# Validate and format JSON
# ---------------------------------------------------------------------------

if OUTPUT_FORMAT.lower() == "json":

    try:
        parsed_json = json.loads(rfp_content)

        rfp_content = json.dumps(
            parsed_json,
            indent=4,
            ensure_ascii=False
        )

    except json.JSONDecodeError as e:

        print("WARNING: Groq returned invalid JSON.")
        print(f"JSON error: {e}")


# ---------------------------------------------------------------------------
# Print output
# ---------------------------------------------------------------------------

print("=" * 70)
print(f"GENERATED REQUEST FOR PROPOSAL ({OUTPUT_FORMAT.upper()})")
print("=" * 70)

print(rfp_content)

print("=" * 70)


# ---------------------------------------------------------------------------
# Save output
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Save output
# ---------------------------------------------------------------------------

from datetime import datetime

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

file_name = (
    f"request_for_proposal_{timestamp}."
    f"{OUTPUT_FORMAT.lower()}"
)

file_path = os.path.join(
    OUTPUT_DIR,
    file_name
)

with open(
    file_path,
    "w",
    encoding="utf-8"
) as f:
    f.write(rfp_content)

print(
    f"\n[Saved] File successfully saved to:\n"
    f"{os.path.abspath(file_path)}"
)