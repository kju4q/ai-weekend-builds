"""Ask questions about your documents.

    python ask.py "when does my passport expire?"
    python ask.py            # interactive loop

Retrieval (finding the relevant chunks) is 100% local. The final answer is
written by Claude IF you set ANTHROPIC_API_KEY; otherwise you get "local mode"
which prints the retrieved passages so the tool still works fully offline.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

from embeddings import embed, cosine

INDEX_PATH = pathlib.Path(__file__).parent / "index.json"
TOP_K = 4
MODEL = "claude-opus-4-8"


def load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        print("No index.json found. Run `python ingest.py` first.")
        sys.exit(1)
    return json.loads(INDEX_PATH.read_text())["records"]


def retrieve(question: str, records: list[dict]) -> list[dict]:
    qvec = embed([question])[0]
    scored = sorted(records, key=lambda r: cosine(qvec, r["vector"]), reverse=True)
    return scored[:TOP_K]


def answer_with_claude(question: str, hits: list[dict]) -> str:
    import anthropic

    context = "\n\n".join(f"[{h['source']} #{h['chunk']}]\n{h['text']}" for h in hits)
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=(
            "You answer questions about the user's personal documents using ONLY "
            "the provided context. Cite the source file in brackets. If the answer "
            "is not in the context, say so plainly. Be concise and specific."
        ),
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )
    return msg.content[0].text


def answer_locally(question: str, hits: list[dict]) -> str:
    out = ["(local mode — no ANTHROPIC_API_KEY set. Most relevant passages:)\n"]
    for h in hits:
        out.append(f"— from {h['source']}:\n  {h['text'][:280]}...\n")
    return "\n".join(out)


def respond(question: str, records: list[dict]) -> str:
    hits = retrieve(question, records)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return answer_with_claude(question, hits)
        except Exception as e:
            print(f"(Claude call failed: {e}; falling back to local mode)")
    return answer_locally(question, hits)


def main() -> None:
    records = load_index()
    if len(sys.argv) > 1:
        print(respond(" ".join(sys.argv[1:]), records))
        return
    print("Ask about your documents (Ctrl-C to quit).")
    try:
        while True:
            q = input("\n> ").strip()
            if q:
                print(respond(q, records))
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
