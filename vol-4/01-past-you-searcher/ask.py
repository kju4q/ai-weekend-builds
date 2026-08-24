"""Ask your own archive a question.

    python3 ask.py "what did I keep saying about building products?"
    python3 ask.py                       # interactive loop

Retrieval is 100% local: the question is embedded on your machine and compared
against index.json. Nothing is sent anywhere in this default mode.

If OPENAI_API_KEY and OPENAI_MODEL are both set, the retrieved passages (and
only those) are sent to the OpenAI API to phrase a short answer with citations.
Without them you get the passages themselves, which is the point of the tool.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import textwrap

from embeddings import backend_name, cosine, embed

INDEX_PATH = pathlib.Path(__file__).parent / "index.json"

TOP_K = 5
# Below this cosine score the match is words-in-common noise rather than a real
# hit. Tuned by hand against the sample data, see prompts.md for how to change it.
WEAK_SCORE = 0.20
SNIPPET_CHARS = 400

SYSTEM_PROMPT = (
    "You answer questions about the user's own past writing using ONLY the "
    "passages provided. Every factual claim must end with a receipt in the form "
    "[filename #chunk]. Never invent a memory, a date, an opinion, or a change "
    "over time that is not present in the passages. If the passages do not "
    "support an answer, say exactly that and stop. Do not pad the answer. Two "
    "to five sentences unless the question needs a short list."
)


def load_index() -> dict:
    if not INDEX_PATH.exists():
        print("No index.json found, so there is nothing to search yet.")
        print("Build one:  python3 ingest.py sample-data")
        sys.exit(1)
    try:
        data = json.loads(INDEX_PATH.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"index.json could not be read ({e}).")
        print("Rebuild it:  python3 ingest.py sample-data")
        sys.exit(1)
    if not data.get("records"):
        print("index.json exists but has no passages in it.")
        print("Rebuild it:  python3 ingest.py sample-data")
        sys.exit(1)
    if data.get("backend") != backend_name():
        print(f"Index was built with the '{data.get('backend')}' backend but this "
              f"environment provides '{backend_name()}'.")
        print("Those vectors are not comparable. Rebuild:  python3 ingest.py sample-data")
        sys.exit(1)
    return data


def retrieve(question: str, records: list[dict]) -> list[tuple[float, dict]]:
    qvec = embed([question])[0]
    scored = [(cosine(qvec, r["vector"]), r) for r in records]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:TOP_K]


def receipt(rec: dict) -> str:
    return f"[{rec['source']} #{rec['chunk']}]"


def show_passages(hits: list[tuple[float, dict]]) -> str:
    out = []
    for score, rec in hits:
        date = rec.get("date", "unknown date")
        if rec.get("date_source") == "file mtime":
            date += " (from file mtime, no date in the writing itself)"
        out.append(
            f"{receipt(rec)}  {date}  score {score:.3f}\n"
            + textwrap.fill(rec["text"][:SNIPPET_CHARS].strip(), width=78,
                            initial_indent="    ", subsequent_indent="    ")
            + ("..." if len(rec["text"]) > SNIPPET_CHARS else "")
        )
    return "\n\n".join(out)


def answer_with_openai(question: str, hits: list[tuple[float, dict]], model: str) -> str:
    from openai import OpenAI

    context = "\n\n".join(f"{receipt(r)} (dated {r.get('date', 'unknown')})\n{r['text']}"
                          for _, r in hits)
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Passages:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content or "(the model returned an empty answer)"


def respond(question: str, records: list[dict]) -> str:
    hits = retrieve(question, records)
    if not hits:
        return "Nothing in the index to compare against."

    best = hits[0][0]
    parts = []
    if best < WEAK_SCORE:
        parts.append(
            f"Weak match: the closest passage scores {best:.3f}, below the {WEAK_SCORE} "
            "threshold. Your writing probably does not cover this. The nearest "
            "passages are below, but treat them as unrelated."
        )

    key, model = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL")
    if key and model:
        try:
            parts.append(answer_with_openai(question, hits, model))
            parts.append("Passages the answer was built from:\n" + show_passages(hits))
            return "\n\n".join(parts)
        except Exception as e:
            parts.append(f"The OpenAI call failed ({type(e).__name__}: {e}).\n"
                         "Falling back to local mode, which is the passages below. "
                         "Retrieval itself was unaffected.")
    elif key and not model:
        parts.append("OPENAI_API_KEY is set but OPENAI_MODEL is not, so no answer was "
                     "written. Set OPENAI_MODEL to a model your account can call, or "
                     "unset the key to use local mode deliberately.")

    parts.append(f"Local mode, {len(hits)} closest passages from your own writing:\n"
                 + show_passages(hits))
    return "\n\n".join(parts)


def main() -> None:
    data = load_index()
    records = data["records"]
    if len(sys.argv) > 1:
        print(respond(" ".join(sys.argv[1:]), records))
        return
    print(f"{len(records)} passages indexed, backend {backend_name()}. Ctrl-C to quit.")
    try:
        while True:
            q = input("\n> ").strip()
            if q:
                print()
                print(respond(q, records))
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
