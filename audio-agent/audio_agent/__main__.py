"""``python -m audio_agent`` entry point."""

import os
import sys

if "--mock" in sys.argv:
    os.environ["AUDIO_AGENT_MOCK"] = "1"

from .main import main

if __name__ == "__main__":
    main()
