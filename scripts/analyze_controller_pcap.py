from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import string
import subprocess
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze a controller capture saved by tshark and extract useful TCP streams/payloads.",
    )
    parser.add_argument("--pcap", required=True, help="Path to the .pcapng capture file")
    parser.add_argument("--controller-ip", required=True, help="Controller IP used to filter the analysis")
    parser.add_argument("--port", dest="ports", action="append", type=int, default=[], help="Expected TCP port. Repeatable.")
    parser.add_argument("--tshark-path", default="", help="Optional explicit path to tshark.exe")
    parser.add_argument("--max-samples", type=int, default=20, help="Maximum payload packet samples to persist")
    return parser


def resolve_tshark(preferred: str = "") -> str:
    candidates = []
    if preferred:
        candidates.append(preferred)
    which_path = shutil.which("tshark")
    if which_path:
        candidates.append(which_path)
    candidates.extend(
        [
            r"C:\Program Files\Wireshark\tshark.exe",
            r"C:\Program Files (x86)\Wireshark\tshark.exe",
        ]
    )
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("tshark.exe was not found")


def run_tshark(tshark: str, args: list[str]) -> str:
    proc = subprocess.run(
        [tshark] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"tshark failed with exit code {proc.returncode}")
    return proc.stdout


def sanitize_payload(payload: str) -> str:
    return "".join(ch for ch in str(payload or "") if ch in string.hexdigits)


def u32_le(hex_payload: str, offset: int) -> int | None:
    data = bytes.fromhex(hex_payload)
    if len(data) < offset + 4:
        return None
    return int.from_bytes(data[offset : offset + 4], "little", signed=False)


def ascii_preview(hex_payload: str, limit: int = 24) -> str:
    data = bytes.fromhex(hex_payload)[:limit]
    chars = []
    for byte in data:
        if 32 <= byte <= 126:
            chars.append(chr(byte))
        else:
            chars.append(".")
    return "".join(chars)


def u8(hex_payload: str, offset: int) -> int | None:
    data = bytes.fromhex(hex_payload)
    if len(data) <= offset:
        return None
    return int(data[offset])


def hex_slice(hex_payload: str, offset: int, size: int) -> str:
    data = bytes.fromhex(hex_payload)
    if len(data) <= offset:
        return ""
    return data[offset : offset + size].hex().upper()


def bytes_preview(hex_payload: str, count: int = 16) -> list[int]:
    return list(bytes.fromhex(hex_payload)[:count])


def build_candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    payload_hex = str(row.get("payload_hex") or "")
    preview_bytes = bytes_preview(payload_hex, count=16)
    candidate = {
        "frame": row.get("frame"),
        "time": row.get("time"),
        "stream": row.get("stream"),
        "src": row.get("src"),
        "sport": row.get("sport"),
        "dst": row.get("dst"),
        "dport": row.get("dport"),
        "tcp_len": row.get("tcp_len"),
        "payload_len_bytes": len(payload_hex) // 2,
        "payload_prefix_hex": payload_hex[:128],
        "payload_ascii_preview": ascii_preview(payload_hex, limit=32),
        "hex_0_3": hex_slice(payload_hex, 0, 4),
        "hex_4_7": hex_slice(payload_hex, 4, 4),
        "hex_8_11": hex_slice(payload_hex, 8, 4),
        "hex_12_15": hex_slice(payload_hex, 12, 4),
        "u32_le_offset_0": u32_le(payload_hex, 0),
        "u32_le_offset_4": u32_le(payload_hex, 4),
        "u32_le_offset_8": u32_le(payload_hex, 8),
        "u32_le_offset_12": u32_le(payload_hex, 12),
        "u8_offset_4": u8(payload_hex, 4),
        "u8_offset_5": u8(payload_hex, 5),
        "u8_offset_6": u8(payload_hex, 6),
        "u8_offset_7": u8(payload_hex, 7),
    }
    for index in range(16):
        candidate[f"byte_{index:02d}"] = preview_bytes[index] if index < len(preview_bytes) else None
    return candidate


def packet_rows(tshark: str, pcap_path: str, controller_ip: str, ports: list[int]) -> list[dict[str, Any]]:
    display_filter = f"ip.addr == {controller_ip} and tcp"
    if ports:
        display_filter += " and tcp.port in {" + ", ".join(str(port) for port in ports) + "}"

    fields = [
        "frame.number",
        "frame.time",
        "ip.src",
        "tcp.srcport",
        "ip.dst",
        "tcp.dstport",
        "tcp.stream",
        "tcp.len",
        "tcp.payload",
    ]

    output = run_tshark(
        tshark,
        [
            "-r",
            pcap_path,
            "-Y",
            display_filter,
            "-T",
            "fields",
            "-E",
            "separator=\t",
            "-E",
            "quote=n",
            "-E",
            "occurrence=f",
            *sum([["-e", field] for field in fields], []),
        ],
    )

    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        while len(parts) < len(fields):
            parts.append("")
        payload = sanitize_payload(parts[8])
        rows.append(
            {
                "frame": int(parts[0]) if parts[0].isdigit() else 0,
                "time": parts[1],
                "src": parts[2],
                "sport": int(parts[3]) if parts[3].isdigit() else None,
                "dst": parts[4],
                "dport": int(parts[5]) if parts[5].isdigit() else None,
                "stream": int(parts[6]) if parts[6].isdigit() else -1,
                "tcp_len": int(parts[7]) if parts[7].isdigit() else 0,
                "payload_hex": payload,
            }
        )
    return rows


def export_stream_dump(tshark: str, pcap_path: str, stream_id: int, target_path: Path) -> None:
    try:
        output = run_tshark(tshark, ["-r", pcap_path, "-q", "-z", f"follow,tcp,hex,{stream_id}"])
    except Exception as exc:
        target_path.write_text(f"Could not export tcp.stream {stream_id}: {exc}\n", encoding="utf-8")
        return
    target_path.write_text(output, encoding="utf-8")


def build_summary(rows: list[dict[str, Any]], max_samples: int) -> dict[str, Any]:
    streams: dict[int, dict[str, Any]] = {}
    payload_samples: list[dict[str, Any]] = []
    candidate_payloads: list[dict[str, Any]] = []

    for row in rows:
        stream_id = int(row.get("stream", -1))
        stream = streams.setdefault(
            stream_id,
            {
                "stream": stream_id,
                "packet_count": 0,
                "payload_packet_count": 0,
                "endpoints": set(),
                "ports": set(),
                "first_frame": row.get("frame"),
                "last_frame": row.get("frame"),
            },
        )
        stream["packet_count"] += 1
        stream["last_frame"] = row.get("frame")
        stream["endpoints"].add((row.get("src"), row.get("dst")))
        if row.get("sport") is not None:
            stream["ports"].add(int(row["sport"]))
        if row.get("dport") is not None:
            stream["ports"].add(int(row["dport"]))

        payload_hex = str(row.get("payload_hex") or "")
        if payload_hex:
            stream["payload_packet_count"] += 1
            candidate_payloads.append(build_candidate_row(row))
            if len(payload_samples) < max_samples:
                payload_samples.append(
                    {
                        "frame": row.get("frame"),
                        "time": row.get("time"),
                        "stream": stream_id,
                        "src": row.get("src"),
                        "sport": row.get("sport"),
                        "dst": row.get("dst"),
                        "dport": row.get("dport"),
                        "tcp_len": row.get("tcp_len"),
                        "payload_prefix_hex": payload_hex[:64],
                        "payload_ascii_preview": ascii_preview(payload_hex),
                        "u32_le_offset_0": u32_le(payload_hex, 0),
                        "u32_le_offset_4": u32_le(payload_hex, 4),
                        "u32_le_offset_8": u32_le(payload_hex, 8),
                    }
                )

    stream_list = []
    for stream in streams.values():
        stream_list.append(
            {
                "stream": stream["stream"],
                "packet_count": stream["packet_count"],
                "payload_packet_count": stream["payload_packet_count"],
                "first_frame": stream["first_frame"],
                "last_frame": stream["last_frame"],
                "ports": sorted(stream["ports"]),
                "endpoint_pairs": [f"{src} -> {dst}" for src, dst in sorted(stream["endpoints"])],
                "display_filter": f"tcp.stream eq {stream['stream']}",
            }
        )
    stream_list.sort(key=lambda item: (item["payload_packet_count"], item["packet_count"]), reverse=True)

    return {
        "packet_count": len(rows),
        "payload_packet_count": sum(1 for row in rows if row.get("payload_hex")),
        "streams": stream_list,
        "payload_samples": payload_samples,
        "candidate_payloads": candidate_payloads,
    }


def write_text_report(summary: dict[str, Any], target_path: Path, pcap_path: str, controller_ip: str) -> None:
    lines = []
    lines.append(f"PCAP: {pcap_path}")
    lines.append(f"Controller IP: {controller_ip}")
    lines.append(f"Packets matched: {summary['packet_count']}")
    lines.append(f"Packets with payload: {summary['payload_packet_count']}")
    lines.append("")
    lines.append("Top TCP streams:")
    for stream in summary["streams"][:10]:
      lines.append(
          f"  stream={stream['stream']} packets={stream['packet_count']} payload_packets={stream['payload_packet_count']} ports={stream['ports']} filter={stream['display_filter']}"
      )
      for pair in stream["endpoint_pairs"][:4]:
          lines.append(f"    {pair}")
    lines.append("")
    lines.append("Payload samples:")
    for sample in summary["payload_samples"][:10]:
        lines.append(
            "  frame={frame} stream={stream} {src}:{sport} -> {dst}:{dport} len={tcp_len} "
            "u32[0]={u32_le_offset_0} u32[4]={u32_le_offset_4} u32[8]={u32_le_offset_8} hex={payload_prefix_hex}".format(**sample)
        )
    lines.append("")
    lines.append("Candidate payloads for CardNo/Event/Door comparison:")
    for candidate in summary["candidate_payloads"][:10]:
        lines.append(
            "  frame={frame} stream={stream} len={payload_len_bytes} bytes "
            "u32[0]={u32_le_offset_0} u8[4]={u8_offset_4} u8[5]={u8_offset_5} u8[6]={u8_offset_6} u8[7]={u8_offset_7} "
            "hex0-15={payload_prefix_hex}".format(**candidate)
        )
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_candidate_csv(candidates: list[dict[str, Any]], target_path: Path) -> None:
    fieldnames = [
        "frame",
        "time",
        "stream",
        "src",
        "sport",
        "dst",
        "dport",
        "tcp_len",
        "payload_len_bytes",
        "u32_le_offset_0",
        "u32_le_offset_4",
        "u32_le_offset_8",
        "u32_le_offset_12",
        "u8_offset_4",
        "u8_offset_5",
        "u8_offset_6",
        "u8_offset_7",
        "hex_0_3",
        "hex_4_7",
        "hex_8_11",
        "hex_12_15",
        "payload_ascii_preview",
        "payload_prefix_hex",
    ] + [f"byte_{index:02d}" for index in range(16)]

    with target_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow({name: candidate.get(name) for name in fieldnames})


def main() -> int:
    args = build_parser().parse_args()
    tshark = resolve_tshark(args.tshark_path)
    pcap_path = os.path.abspath(args.pcap)
    if not os.path.exists(pcap_path):
        raise FileNotFoundError(pcap_path)

    rows = packet_rows(tshark, pcap_path, args.controller_ip, args.ports)
    summary = build_summary(rows, max_samples=max(1, int(args.max_samples)))

    pcap = Path(pcap_path)
    report_json = pcap.with_suffix(pcap.suffix + ".summary.json")
    report_txt = pcap.with_suffix(pcap.suffix + ".summary.txt")
    candidates_json = pcap.with_suffix(pcap.suffix + ".candidates.json")
    candidates_csv = pcap.with_suffix(pcap.suffix + ".candidates.csv")
    stream_dir = pcap.parent / f"{pcap.stem}_streams"
    stream_dir.mkdir(parents=True, exist_ok=True)

    report_json.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    write_text_report(summary, report_txt, pcap_path, args.controller_ip)
    candidates_json.write_text(json.dumps(summary["candidate_payloads"], ensure_ascii=True, indent=2), encoding="utf-8")
    write_candidate_csv(summary["candidate_payloads"], candidates_csv)

    for stream in summary["streams"][:5]:
        if int(stream.get("payload_packet_count") or 0) <= 0:
            continue
        export_stream_dump(tshark, pcap_path, int(stream["stream"]), stream_dir / f"tcp_stream_{stream['stream']}.txt")

    print(f"Summary JSON: {report_json}")
    print(f"Summary TXT:  {report_txt}")
    print(f"Candidates JSON: {candidates_json}")
    print(f"Candidates CSV:  {candidates_csv}")
    if summary["streams"]:
        print("Suggested filters:")
        for stream in summary["streams"][:5]:
            print(f"  {stream['display_filter']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())