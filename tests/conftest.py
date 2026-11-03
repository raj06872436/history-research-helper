import sys
from pathlib import Path

# Let tests import app.py and the research package from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
