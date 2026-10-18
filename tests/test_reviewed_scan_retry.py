import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from run_reviewed_scan_retry import POLICY, metadata, payload


def setup():
    args = SimpleNamespace(model="Qwen/Qwen3.8-27B-FP8", revision="pinned", max_tokens=6000)
    manifest = {"prompt": "Read the source", "review": {"evidence": "Checked scan"},
                "pages": [{"id": "reviewed-region"}],
                "checkpoints": [{"model": args.model, "revision": args.revision}]}
    return args, manifest, {"model": args.model, "revision": args.revision}


def test_provider_policy_is_explicit_without_affecting_original_runner(tmp_path):
    args, _, _ = setup()
    image = tmp_path / "source.png"
    image.write_bytes(b"source pixels")
    result = payload(args, image, "Exact source prompt")
    assert {key: result[key] for key in ["temperature", "top_p", "top_k", "presence_penalty", "seed"]} == {
        "temperature": .7, "top_p": .8, "top_k": 20, "presence_penalty": 1.5, "seed": 20261018}
    assert result["chat_template_kwargs"] == {"enable_thinking": False}
    assert result["messages"][0]["content"][1]["text"] == "Exact source prompt"
    assert "source_urls" not in result


def test_metadata_binds_policy_runner_source_and_actual_runtime():
    args, manifest, runtime = setup()
    raw = json.dumps(manifest).encode()
    result = metadata(args, raw, manifest, runtime)
    assert result["generation_policy"] == POLICY
    assert result["temperature"] == .7
    assert result["runtime"] == runtime
    assert len(result["manifest_sha256"]) == len(result["runner_sha256"]) == 64
    changed = metadata(args, raw + b" ", manifest, runtime)
    assert changed["manifest_sha256"] != result["manifest_sha256"]


def test_wrong_checkpoint_and_unreviewed_requests_are_rejected():
    args, manifest, runtime = setup()
    with pytest.raises(ValueError, match="server belongs"):
        metadata(args, b"{}", manifest, {**runtime, "revision": "other"})
    with pytest.raises(ValueError, match="outside"):
        metadata(args, b"{}", {**manifest, "checkpoints": [{"model": args.model, "revision": "other"}]}, runtime)
    with pytest.raises(ValueError, match="source-reviewed"):
        metadata(args, b"{}", {**manifest, "review": {}}, runtime)
