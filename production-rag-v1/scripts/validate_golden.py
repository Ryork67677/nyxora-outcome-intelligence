#!/usr/bin/env python3
import sys
from pathlib import Path

from rag_v1.evals.validate import validate_golden

if __name__ == "__main__":
    path = Path(sys.argv[1])
    print(validate_golden(path))
