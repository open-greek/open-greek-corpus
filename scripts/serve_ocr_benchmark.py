#!/usr/bin/env python3
"""Serve an immutable OCR checkpoint and record its inference environment."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    from huggingface_hub import snapshot_download
    import torch
    path = snapshot_download(args.model, revision=args.revision)
    command = [sys.executable, "-m", "vllm.entrypoints.openai.api_server",
               "--model", path, "--served-model-name", args.model,
               "--host", "127.0.0.1", "--port", str(args.port),
               "--max-model-len", "16384", "--max-num-seqs", "8",
               "--gpu-memory-utilization", "0.90", "--reasoning-parser", "qwen3",
               "--limit-mm-per-prompt", '{"image":1}']
    # Store portable settings, not local checkpoint or executable paths.
    runtime = {"model": args.model, "revision": args.revision,
               "versions": {name: importlib.metadata.version(name)
                            for name in ("vllm", "torch", "transformers", "huggingface-hub")},
               "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(),
               "settings": {"max_model_len": 16384, "max_num_seqs": 8,
                            "gpu_memory_utilization": 0.90, "reasoning_parser": "qwen3",
                            "images_per_prompt": 1}}
    args.runtime_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.runtime_manifest.write_text(json.dumps(runtime, indent=2) + "\n")
    os.execv(command[0], command)


if __name__ == "__main__":
    main()
