import sys
from pathlib import Path

# Ensure this directory is in sys.path so generated pb2_grpc can import demo_pb2 directly
_proto_dir = str(Path(__file__).resolve().parent)
if _proto_dir not in sys.path:
    sys.path.insert(0, _proto_dir)

import demo_pb2
import demo_pb2_grpc

__all__ = ["demo_pb2", "demo_pb2_grpc"]


# the init.py file makes the folder importable as a Python package and handles the generated files’ import path.