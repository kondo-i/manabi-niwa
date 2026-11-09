"""Rebuild the complete authored batch in a fixed order; no tracked verifier output by default."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
for name in ['build_expansion_v1.py','add_language_social_expansion.py','add_science_concepts.py','finalize_expansion_v1.py']:
 subprocess.run([sys.executable,str(R/name)],check=True)
