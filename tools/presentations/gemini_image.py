#!/usr/bin/env python3
"""Generate one image via the official Gemini API using a local private key file."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--size", choices=["1K", "2K", "4K"], default="2K")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--reference-image", type=Path, help="Existing image to edit while preserving its composition")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9.-]+", args.model):
        parser.error("Invalid model identifier")
    if args.out.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        parser.error("Output must use an image extension")
    metadata_path = args.out.with_suffix(".json")
    if any(args.out.with_suffix(suffix).exists() for suffix in (".png", ".jpg", ".jpeg", ".webp", ".bin", ".json")):
        parser.error("Output or metadata already exists; use a new filename")
    prompt = args.prompt_file.read_text().strip()
    if not prompt:
        parser.error("Prompt is empty")
    parts = [{"text": prompt}]
    reference_meta = None
    if args.reference_image:
        mime_type = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(args.reference_image.suffix.lower())
        if not mime_type:
            parser.error("Reference image must be PNG, JPEG, or WebP")
        reference_bytes = args.reference_image.read_bytes()
        if len(reference_bytes) > 15_000_000:
            parser.error("Reference image is too large for this inline request")
        parts.append({"inlineData": {"mimeType": mime_type, "data": base64.b64encode(reference_bytes).decode("ascii")}})
        reference_meta = {"file": args.reference_image.name, "sha256": hashlib.sha256(reference_bytes).hexdigest(), "role": "edit_target"}
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": args.aspect_ratio, "imageSize": args.size},
        },
    }
    if args.dry_run:
        print(json.dumps({"model": args.model, "prompt_characters": len(prompt), "size": args.size, "aspect_ratio": args.aspect_ratio, "network_request": False}))
        return 0
    key = (Path.home() / ".config" / "gherkai-presentation" / "gemini-api-key").read_text().strip()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"provider": "Google Gemini API", "model": args.model, "created_at": datetime.now(timezone.utc).isoformat(), "prompt_file": args.prompt_file.name, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "image_size": args.size, "aspect_ratio": args.aspect_ratio, "attempts": 1, "reference_image": reference_meta}
    req = Request(f"https://generativelanguage.googleapis.com/v1beta/models/{args.model}:generateContent", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    start = time.monotonic()
    try:
        with build_opener(NoRedirect).open(req, timeout=180) as response:
            data = json.load(response)
    except HTTPError as error:
        message = error.read().decode("utf-8", "replace").replace(key, "[REDACTED]")
        message = re.sub(r"\b\d{12}\b", "[REDACTED_ID]", message)
        metadata.update(status="http_error", http_status=error.code, message=message[:1800], elapsed_seconds=round(time.monotonic()-start,3))
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
        print(json.dumps({"status": "http_error", "http_status": error.code, "message": message[:900]}, ensure_ascii=False))
        return 1
    except Exception as error:
        message = str(error).replace(key,"[REDACTED]")
        metadata.update(status="request_error", error_type=type(error).__name__, message=message[:400], elapsed_seconds=round(time.monotonic()-start,3))
        metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
        print(json.dumps({"status":"request_error","error_type":type(error).__name__,"message":message[:400]}))
        return 1
    images = []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if part.get("thought"):
                continue
            image = part.get("inlineData")
            if image and image.get("mimeType", "").startswith("image/"):
                images.append(image)
    metadata.update(elapsed_seconds=round(time.monotonic()-start,3), usage=data.get("usageMetadata",{}), finish_reasons=[c.get("finishReason") for c in data.get("candidates",[])], image_count=len(images))
    if not images:
        metadata.update(status="no_image", prompt_feedback=data.get("promptFeedback",{}))
        metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
        print(json.dumps({"status":"no_image","finish_reasons":metadata["finish_reasons"]}))
        return 1
    image = images[0]
    image_bytes = base64.b64decode(image["data"],validate=True)
    suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(image.get("mimeType"), ".bin")
    actual_output = args.out.with_suffix(suffix)
    with actual_output.open("xb") as stream:
        stream.write(image_bytes)
    metadata.update(status="success" if suffix != ".bin" else "saved_unknown_image_type", output=actual_output.name, mime_type=image["mimeType"],bytes=len(image_bytes),sha256=hashlib.sha256(image_bytes).hexdigest())
    metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print(json.dumps({"status":metadata["status"],"output":str(actual_output),"bytes":len(image_bytes),"elapsed_seconds":metadata["elapsed_seconds"]},ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
