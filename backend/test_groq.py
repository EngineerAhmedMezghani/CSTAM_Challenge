import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.llm_extractor import extract_tender


SAMPLE_RFP = """Request for Proposal RFP-2026-04: Cloud migration services
The Example Agency invites proposals for migration of its internal services to a public
cloud. The proposal deadline is 2026-10-15 at 17:00 CET. The platform must support SSO
and Kubernetes. Suppliers must submit a technical proposal. No budget is published.
"""


if __name__ == "__main__":
    result = extract_tender(SAMPLE_RFP, source_url="https://example.test/rfp-2026-04")
    print(json.dumps(result, indent=2, ensure_ascii=False))