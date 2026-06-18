from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path

from .models import CommandUtterance
from .parser import parse_utterance
from .queue import CommandQueue


@dataclass(frozen=True)
class TranscriptIngestResult:
    transcript: str
    command_count: int
    queue_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "transcript": self.transcript,
            "command_count": self.command_count,
            "queue_path": self.queue_path,
        }


def ingest_transcript(text: str, queue_path: Path, source: str = "voice_transcript") -> TranscriptIngestResult:
    commands = parse_utterance(CommandUtterance(text=text, source=source))
    CommandQueue(queue_path).append(commands)
    return TranscriptIngestResult(transcript=text, command_count=len(commands), queue_path=str(queue_path))


def ingest_transcript_file(path: Path, queue_path: Path, source: str = "voice_transcript_file") -> TranscriptIngestResult:
    return ingest_transcript(path.read_text(encoding="utf-8").strip(), queue_path, source)


def render_commander_ui(queue_path: Path, examples: tuple[str, ...] | None = None) -> str:
    examples = examples or (
        "저그 드론 5개 더 찍고 2햇 뮤탈. 침략적으로 가되 정면 싸움은 피하고 일꾼만 흔들어.",
        "프로토스 2게이트 압박. 드라군 사업 먼저.",
        "테란 벌처 3기 생산하고 마인업. 정면 싸움은 피하고 견제해.",
    )
    escaped_examples = "\n".join(f"<button type=\"button\" data-example=\"{html.escape(item)}\">{html.escape(item)}</button>" for item in examples)
    escaped_queue = html.escape(str(queue_path))
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VOI Brood War Commander</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #10130f;
      --panel: #1d2518;
      --ink: #f3f1df;
      --muted: #b8bd9f;
      --accent: #d7ff64;
      --line: #465235;
    }}
    body {{
      margin: 0;
      font-family: Avenir Next, Optima, Trebuchet MS, sans-serif;
      background: radial-gradient(circle at top left, #384423, transparent 34rem), linear-gradient(135deg, #10130f, #222617);
      color: var(--ink);
    }}
    main {{
      max-width: 880px;
      margin: 0 auto;
      padding: 48px 20px;
    }}
    section {{
      background: color-mix(in srgb, var(--panel) 88%, black);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 20px 80px rgb(0 0 0 / 35%);
    }}
    h1 {{
      font-size: clamp(2.2rem, 6vw, 4.4rem);
      line-height: .92;
      margin: 0 0 18px;
      letter-spacing: -0.07em;
    }}
    textarea {{
      width: 100%;
      min-height: 128px;
      box-sizing: border-box;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: #0e120c;
      color: var(--ink);
      padding: 16px;
      font: inherit;
    }}
    button {{
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #28331b;
      color: var(--ink);
      padding: 10px 14px;
      margin: 6px 6px 0 0;
      cursor: pointer;
    }}
    button.primary {{
      background: var(--accent);
      color: #171a10;
      font-weight: 800;
    }}
    .muted {{
      color: var(--muted);
    }}
    pre {{
      overflow: auto;
      background: #0b0e09;
      border-radius: 16px;
      padding: 16px;
    }}
  </style>
</head>
<body>
  <main>
    <section>
      <p class="muted">Queue target: <code>{escaped_queue}</code></p>
      <h1>Intent Commander</h1>
      <p>실제 런타임에서는 CLI나 로컬 서버가 이 텍스트를 JSONL command queue에 append하고, 봇의 onFrame hook이 cursor 기반으로 poll합니다.</p>
      <textarea id="command">저그 드론 5개 더 찍고 2햇 뮤탈. 침략적으로 가되 정면 싸움은 피하고 일꾼만 흔들어.</textarea>
      <p>
        <button class="primary" id="download">JSONL로 내보내기</button>
      </p>
      <div>{escaped_examples}</div>
      <h2>운영 연결</h2>
      <pre>PYTHONPATH=src python3 -m voi_bw_commander.cli transcript "..." --queue {escaped_queue}</pre>
    </section>
  </main>
  <script>
    const text = document.querySelector("#command");
    document.querySelectorAll("[data-example]").forEach(button => {{
      button.addEventListener("click", () => text.value = button.dataset.example);
    }});
    document.querySelector("#download").addEventListener("click", () => {{
      const blob = new Blob([JSON.stringify({{source: "commander_ui", text: text.value}}) + "\\n"], {{type: "application/jsonl"}});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "commander-input.jsonl";
      link.click();
      URL.revokeObjectURL(link.href);
    }});
  </script>
</body>
</html>
"""


def write_commander_ui(output: Path, queue_path: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_commander_ui(queue_path), encoding="utf-8")
    return output
