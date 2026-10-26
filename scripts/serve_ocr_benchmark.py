#!/usr/bin/env python3
"""Serve an immutable OCR checkpoint and record its inference environment."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-num-seqs", type=int, default=8,
                        help="maximum concurrent sequences (default: 8)")
    args = parser.parse_args()
    if args.max_num_seqs < 1:
        parser.error("--max-num-seqs must be positive")
    from huggingface_hub import snapshot_download
    import torch
    path = snapshot_download(args.model, revision=args.revision)
    command = [sys.executable, "-m", "vllm.entrypoints.openai.api_server",
               "--model", path, "--served-model-name", args.model,
               "--host", "127.0.0.1", "--port", str(args.port),
               "--max-model-len", "16384", "--max-num-seqs", str(args.max_num_seqs),
               "--gpu-memory-utilization", "0.90", "--reasoning-parser", "qwen3",
               "--limit-mm-per-prompt", '{"image":1}']
    # Store portable settings, not local checkpoint or executable paths.
    runtime = {"model": args.model, "revision": args.revision,
               "versions": {name: importlib.metadata.version(name)
                            for name in ("vllm", "torch", "transformers", "huggingface-hub")},
               "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(),
               "settings": {"max_model_len": 16384, "max_num_seqs": args.max_num_seqs,
                            "gpu_memory_utilization": 0.90, "reasoning_parser": "qwen3",
                            "images_per_prompt": 1}}
    compiler = subprocess.run(["nvcc", "--version"], capture_output=True, text=True, check=True)
    match = re.search(r"release ([0-9.]+), V([0-9.]+)", compiler.stdout)
    runtime["cuda_compiler"] = {"release": match[1], "version": match[2]} if match else {
        "version_output": compiler.stdout.strip()}
    runtime["server_recipe_sha256"] = __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest()
    args.runtime_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.runtime_manifest.write_text(json.dumps(runtime, indent=2) + "\n")
    os.execv(command[0], command)


if __name__ == "__main__":
    main()
