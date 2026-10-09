#!/usr/bin/env python3
"""Update slide video frames or captions while preserving approved source media."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def run(command: list[str], log: Path | None = None) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if log:
        log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} failed: {result.stderr[-1800:]}")
    return result.stdout + result.stderr


def probe(path: Path) -> dict:
    result = subprocess.run([
        shutil.which("ffprobe"), "-v", "error", "-show_format", "-show_streams",
        "-show_chapters", "-of", "json", str(path),
    ], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    if result.stderr.strip():
        data["probe_warnings"] = result.stderr.strip()
    return data


def srt_time(value: float) -> str:
    ms = round(value * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def link_chapter_title_track(path: Path) -> dict:
    """Link the explicit timed chapter titles without moving media samples.

    The local FFmpeg build produced invalid automatic QT chapter references
    and timings. A separate mov_text track supplies verified title timestamps.
    Replace the automatic references with that track, and free only redundant
    generated chapter metadata. Video/audio/caption samples retain all offsets.
    """
    def boxes(data: bytes, start=0, end=None):
        end = len(data) if end is None else end
        pos = start
        while pos + 8 <= end:
            size = int.from_bytes(data[pos:pos+4], "big")
            header = 8
            if size == 1:
                size = int.from_bytes(data[pos+8:pos+16], "big")
                header = 16
            if size == 0:
                size = end-pos
            if size < header or pos+size > end:
                raise ValueError("Invalid MP4 box size")
            yield data[pos+4:pos+8], pos, pos+header, pos+size
            pos += size

    with path.open("r+b") as file:
        file_size = path.stat().st_size
        position = 0
        while position < file_size:
            file.seek(position)
            header = file.read(16)
            size = int.from_bytes(header[:4], "big")
            header_size = 8
            if size == 1:
                size = int.from_bytes(header[8:16], "big")
                header_size = 16
            if size == 0:
                size = file_size-position
            if size < header_size:
                raise ValueError("Invalid MP4 container")
            if header[4:8] == b"moov":
                moov_offset = position+header_size
                file.seek(moov_offset)
                moov = file.read(size-header_size)
                break
            position += size
        else:
            raise ValueError("No MP4 movie metadata")
        tracks = [b for b in boxes(moov) if b[0] == b"trak"]
        track_info = {}
        references = []
        for _, track_start, start, end in tracks:
            children = list(boxes(moov, start, end))
            tkhd = next(b for b in children if b[0] == b"tkhd")
            at = tkhd[2]
            id_offset = at + (20 if moov[at] == 1 else 12)
            track_id = int.from_bytes(moov[id_offset:id_offset+4], "big")
            mdia = next(b for b in children if b[0] == b"mdia")
            hdlr = next(b for b in boxes(moov, mdia[2], mdia[3]) if b[0] == b"hdlr")
            handler = moov[hdlr[2]+8:hdlr[2]+12]
            name = moov[hdlr[2]+24:hdlr[3]].rstrip(b"\0").decode("utf-8")
            track_info[track_id] = {"start": track_start, "handler": handler, "name": name}
            for kind, tref_start, tref_payload, tref_end in children:
                if kind == b"tref":
                    for child in boxes(moov, tref_payload, tref_end):
                        if child[0] == b"chap":
                            values = [int.from_bytes(moov[i:i+4], "big")
                                      for i in range(child[2], child[3], 4)]
                            references.append((track_id, tref_start, child[1], child[2], values,
                                               len(list(boxes(moov, tref_payload, tref_end)))))
        chapter_ids = [i for i, t in track_info.items() if t["name"] == "Chapter titles"]
        if len(chapter_ids) != 1:
            raise ValueError("Explicit chapter title track is missing or ambiguous")
        chapter_id = chapter_ids[0]
        generated_ids = {i for *_, values, count in references for i in values
                         if i and i != chapter_id}
        for generated_id in generated_ids:
            if generated_id not in track_info:
                continue
            track = track_info[generated_id]
            if track["handler"] not in {b"text", b"sbtl"}:
                raise ValueError("Refusing to discard a non-text media track")
            file.seek(moov_offset+track["start"]+4)
            file.write(b"free")
        linked = 0
        for owner, parent, child, payload, values, count in references:
            if owner in generated_ids:
                continue
            if owner == chapter_id:
                file.seek(moov_offset+(parent if count == 1 else child)+4)
                file.write(b"free")
                continue
            for i in range(len(values)):
                file.seek(moov_offset+payload+4*i)
                file.write(chapter_id.to_bytes(4, "big"))
            linked += 1
        return {"explicit_chapter_track_id": chapter_id, "linked_references": linked,
                "redundant_generated_tracks": sorted(generated_ids),
                "media_offsets_unchanged": True}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_state(path):
    return {"sha256": digest(path), "bytes": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns}


def packets(path, stream):
    result = subprocess.check_output([
        shutil.which("ffprobe"), "-v", "error", "-select_streams", stream,
        "-show_packets", "-show_data_hash", "sha256",
        "-show_entries", "packet=pts,dts,duration,flags,data_hash", "-of", "json", str(path),
    ], text=True)
    return json.loads(result)["packets"]


def verify_hard_cuts(ffmpeg, video, timeline, qa):
    """Confirm the first slide at frame zero, hard cuts, and the closing fade."""
    fps = timeline["fps"]
    total = round(timeline["duration"] * fps)
    fade_frames = round(timeline["ending_fade_seconds"] * fps)
    hold_frames = round(timeline["ending_black_hold_seconds"] * fps)
    opening_end = min(round(.5 * fps), timeline["pages"][0]["frames"] - 1)
    ending_start = total - hold_frames - fade_frames
    ranges = [(0,opening_end),(ending_start,total-1)]
    for page in timeline["pages"][1:]:
        boundary = round(page["start"] * fps)
        ranges.append((boundary-6,boundary+6))
    ranges.sort()
    indices = sorted({i for start,end in ranges for i in range(start,end+1)})
    expression = "+".join(f"between(n\\,{start}\\,{end})" for start,end in ranges)
    result = subprocess.run([
        ffmpeg,"-v","error","-i",str(video),"-map","0:v:0",
        "-vf",f"select={expression},scale=128:72,format=gray",
        "-fps_mode","vfr","-f","rawvideo","-",
    ],capture_output=True)
    (qa/"hard-cuts.ffmpeg.log").write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(result.stderr.decode()[-1000:])
    size=128*72
    assert len(result.stdout)==len(indices)*size
    frames={n:result.stdout[i*size:(i+1)*size] for i,n in enumerate(indices)}
    mean=lambda n:sum(frames[n])/size
    assert mean(0)>50 and mean(total-1)<2
    opening_errors=[]
    for index in range(opening_end+1):
        error=sum(abs(a-b) for a,b in zip(frames[index],frames[opening_end]))/size
        assert error<.5, ("opening",index,error)
        opening_errors.append(error)
    for step in range(fade_frames+1):
        closing_ratio=mean(ending_start+step)/mean(ending_start)
        assert abs(closing_ratio-(1-step/fade_frames))<.04
    cuts=[]
    for page in timeline["pages"][1:]:
        boundary=round(page["start"]*fps)
        errors=[]
        for shift in range(-5,6):
            reference=frames[boundary-6 if shift<0 else boundary+6]
            actual=frames[boundary+shift]
            error=sum(abs(a-b) for a,b in zip(actual,reference))/size
            assert error<.5, (page["page"],shift,error)
            errors.append(error)
        assert mean(boundary-1)>50 and mean(boundary)>50
        cuts.append({"to_page":page["page"],"mode":"cut",
                     "maximum_stability_error":round(max(errors),4)})
    report={"status":"pass","page_transitions":cuts,"opening":"first_slide",
            "opening_fade_seconds":0,"opening_black_hold_seconds":0,
            "opening_maximum_stability_error":round(max(opening_errors),4),
            "ending":"black","ending_fade_seconds":timeline["ending_fade_seconds"],
            "ending_black_hold_seconds":timeline["ending_black_hold_seconds"],
            "page_fades":False}
    write_json(qa/"hard-cuts-and-bookends.json",report)
    return report


def cues(text):
    result = []
    for block in re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n").lstrip("\ufeff").strip()):
        lines = block.splitlines()
        assert len(lines) >= 3 and "-->" in lines[1], block
        result.append({"time": lines[1].strip(), "text": "\n".join(lines[2:])})
    return result


def refresh():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--slides-dir", type=Path, required=True)
    parser.add_argument("--protected-srt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    assert not args.output.exists(), "Use a new output filename"
    args.stage.mkdir(parents=True, exist_ok=True)
    before = protected_state(args.protected_srt)
    source_sha = digest(args.source_video)
    original = probe(args.source_video)
    timeline = json.loads(args.timeline.read_text())
    fps = timeline["fps"]
    duration = timeline["duration"]
    assert timeline["transition_style"] == "cuts_with_closing_fade"
    assert timeline["opening_frame"] == "first_slide"
    assert float(original["format"]["duration"]) == duration
    ffmpeg = shutil.which("ffmpeg")
    embedded = run([ffmpeg, "-v", "error", "-nostdin", "-i", str(args.source_video),
                    "-map", "0:s:0", "-c:s", "srt", "-f", "srt", "-"])
    assert cues(embedded) == cues(args.protected_srt.read_text()), "Source video does not match selected subtitles; run the subtitles command first"
    pages = []
    for old in timeline["pages"]:
        number = old["page"]
        slide = args.slides_dir / f"{number:02}.png"
        assert slide.is_file(), slide
        page = {**old, "slide_path": str(slide.resolve()), "slide_sha256": digest(slide),
                "segment": str((args.stage / f"segment-{number:02}.mp4").resolve())}
        pages.append(page)
    updated_timeline = {**timeline, "pages": pages}
    write_json(args.stage / "timeline.json", updated_timeline)

    def render(page):
        filters = ["scale=out_color_matrix=bt709", "format=yuv420p"]
        fade = timeline["ending_fade_seconds"]
        hold = timeline["ending_black_hold_seconds"]
        if page["page"] == len(pages):
            filters.append(f"fade=t=out:st={page['duration']-fade-hold:.9f}:d={fade:.9f}:color=black")
        run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-loop", "1", "-framerate", str(fps), "-i", page["slide_path"],
            "-vf", ",".join(filters), "-frames:v", str(page["frames"]), "-an",
            "-c:v", "libx264", "-preset", "fast", "-tune", "stillimage",
            "-crf", "18", "-threads", "2", "-r", str(fps), "-g", str(fps*10),
            "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart",
            page["segment"],
        ], args.stage / f"render-{page['page']:02}.log")
        return page["page"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        for page in pool.map(render, pages):
            print(json.dumps({"page": page, "rendered": True}), flush=True)
    concat = args.stage / "segments.txt"
    assert all("'" not in p["segment"] for p in pages)
    concat.write_text("".join(f"file '{p['segment']}'\n" for p in pages))
    joined = args.stage / "joined-visuals.mp4"
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
         "-f", "concat", "-safe", "0", "-i", str(concat), "-c:v", "copy", str(joined)],
        args.stage / "concat.log")
    chapter_titles = args.stage / "chapter-titles.srt"
    chapter_titles.write_text("".join(
        f"{i}\n{srt_time(float(c['start_time']))} --> {srt_time(float(c['end_time']))}\n"
        f"{c['tags']['title']}\n\n"
        for i, c in enumerate(original["chapters"], 1)
    ))
    run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
        "-i", str(joined), "-i", str(args.source_video), "-i", str(chapter_titles),
        "-map", "0:v:0", "-map", "1:a:0", "-map", "1:s:0", "-map", "2:s:0",
        "-map_metadata", "1", "-map_chapters", "1", "-c", "copy",
        "-c:s:1", "mov_text", "-metadata:s:s:1", "handler_name=Chapter titles",
        "-disposition:s:1", "0", "-movflags", "+faststart", str(args.output),
    ], args.stage / "mux.log")
    write_json(args.stage / "container-repair.json", link_chapter_title_track(args.output))
    info = probe(args.output)
    assert not info.get("probe_warnings"), info.get("probe_warnings")
    assert original["chapters"] == info["chapters"]
    assert float(info["format"]["duration"]) == duration
    media_checks = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for stream, before_packets, after_packets in pool.map(
            lambda s: (s, packets(args.source_video, s), packets(args.output, s)),
            ["a:0", "s:0"],
        ):
            assert before_packets == after_packets, f"{stream} changed"
            media_checks.append({"stream": stream, "packet_count": len(after_packets),
                                 "samples_and_timestamps": "identical"})

    def frame_check(page):
        at = 0 if page["page"] == 1 else min(page["start"] + 5, page["end"] - .5)
        result = run([
            ffmpeg, "-hide_banner", "-nostdin", "-ss", str(at), "-i", str(args.output),
            "-i", page["slide_path"], "-filter_complex",
            "[0:v]format=yuv444p[a];[1:v]format=yuv444p[b];[a][b]ssim",
            "-frames:v", "1", "-an", "-f", "null", "-",
        ], args.stage / f"frame-{page['page']:02}.log")
        import re
        score = float(re.findall(r"All:([0-9.]+)", result)[-1])
        assert score >= .98, (page["page"], score)
        return {"page": page["page"], "ssim": score}
    with ThreadPoolExecutor(max_workers=2) as pool:
        frame_checks = list(pool.map(frame_check, pages))
    # Inspect actual output frames for the cover start, cuts, and closing fade.
    cuts = verify_hard_cuts(ffmpeg, args.output, updated_timeline, args.stage)
    run([ffmpeg, "-v", "error", "-nostdin", "-i", str(args.output),
         "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], args.stage / "decode.log")
    assert protected_state(args.protected_srt) == before, "Protected subtitles changed"
    assert digest(args.source_video) == source_sha, "Source video changed"
    report = {
        "status": "pass", "output": str(args.output), "sha256": digest(args.output),
        "bytes": args.output.stat().st_size, "duration_seconds": duration,
        "fps": fps, "playback_multiplier": timeline["playback_multiplier"],
        "copied_media": media_checks, "chapters_unchanged": True,
        "frame_checks": frame_checks, "transition_review": cuts,
        "protected_srt": {"path": str(args.protected_srt), **before, "unchanged": True},
        "source_video_sha256": source_sha, "source_video_unchanged": True,
        "complete_decode": "pass",
    }
    write_json(args.stage / "verification.json", report)
    print(json.dumps({"status": "pass", "output": str(args.output),
                      "duration_seconds": duration, "protected_srt_unchanged": True}), flush=True)


def subtitles():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", type=Path, required=True)
    parser.add_argument("--subtitles", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "Use a new output file"
    assert args.subtitles.resolve() != args.output.resolve()
    args.stage.mkdir(parents=True, exist_ok=True)
    protected = protected_state(args.subtitles)
    desired = cues(args.subtitles.read_text())
    original = probe(args.source_video)
    chapter_titles = args.stage / "chapter-titles.srt"
    assert chapter_titles.resolve() != args.subtitles.resolve()
    chapter_titles.write_text("".join(
        f"{i}\n{srt_time(float(c['start_time']))} --> {srt_time(float(c['end_time']))}\n"
        f"{c['tags']['title']}\n\n" for i, c in enumerate(original["chapters"], 1)
    ))
    ffmpeg = shutil.which("ffmpeg")
    run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
        "-i", str(args.source_video), "-i", str(args.subtitles), "-i", str(chapter_titles),
        "-map", "0:v:0", "-map", "0:a:0", "-map", "1:s:0", "-map", "2:s:0",
        "-map_metadata", "0", "-map_chapters", "0", "-c:v", "copy", "-c:a", "copy",
        "-c:s", "mov_text", "-metadata:s:s:0", "language=zho",
        "-metadata:s:s:0", "handler_name=中文字幕", "-disposition:s:0", "default",
        "-metadata:s:s:1", "handler_name=Chapter titles", "-disposition:s:1", "0",
        "-movflags", "+faststart", str(args.output),
    ], args.stage / "mux.log")
    write_json(args.stage / "container-repair.json", link_chapter_title_track(args.output))
    current = probe(args.output)
    assert not current.get("probe_warnings")
    assert current["chapters"] == original["chapters"]
    assert current["format"]["duration"] == original["format"]["duration"]
    copied = []
    for stream in ["v:0", "a:0"]:
        before, after = packets(args.source_video, stream), packets(args.output, stream)
        assert before == after, f"{stream} media packets or timestamps changed"
        copied.append({"stream": stream, "packet_count": len(after), "samples_and_timestamps": "identical"})
    exported = run([
        ffmpeg, "-v", "error", "-nostdin", "-i", str(args.output),
        "-map", "0:s:0", "-c:s", "srt", "-f", "srt", "-",
    ], args.stage / "embedded-captions.srt")
    assert cues(exported) == desired, "Embedded caption text or timing differs from selected SRT"
    assert protected_state(args.subtitles) == protected, "User-edited subtitle source changed"
    report = {
        "status": "pass", "video": str(args.output.resolve()),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "bytes": args.output.stat().st_size, "duration_seconds": float(current["format"]["duration"]),
        "copied_media": copied, "chapters_unchanged": True, "caption_count": len(desired),
        "caption_text_and_timing_match_source": True,
        "protected_srt": {"path": str(args.subtitles.resolve()), **protected, "unchanged": True},
    }
    write_json(args.stage / "verification.json", report)
    print(json.dumps(report, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("Usage: video.py {refresh|subtitles} [options]\nEach command accepts --help. Inputs are preserved; use a new output path.")
    else:
        command = sys.argv.pop(1)
        if command == "refresh":
            refresh()
        elif command == "subtitles":
            subtitles()
        else:
            raise SystemExit("Unknown command; choose refresh or subtitles")
