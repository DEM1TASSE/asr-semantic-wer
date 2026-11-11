"""Annotate error spans with an LLM (OpenAI-compatible API; DeepSeek by default).

Backends: --backend azure (Azure OpenAI; key AZURE_API_KEY from env or project .env, model = deployment
name) or --backend openai (any OpenAI-compatible endpoint, e.g. DeepSeek or a vLLM server on Delta).
Results are cached per error_id, so reruns resume.
Output: outputs/llm_annotations_<tag>.jsonl
"""
import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import AzureOpenAI, OpenAI
from tqdm import tqdm

from common import OUT, ROOT

CONTENT_TYPES = ["disfluency", "function_word", "content_word", "named_entity", "number", "negation", "other"]
ERROR_FORMS = ["morph_variant", "nonword", "real_word", "garbled", "other"]
FLAGS = ["ref_issue", "crosstalk", "uncertain", "multi_issue"]

SYSTEM = """You are an expert annotator of speech recognition (ASR) errors in meeting transcripts.
Follow the annotation guideline below exactly.

{rubric}

Respond with a JSON object only:
{{"severity": integer 1-5, "content_type": one of {ct},
 "error_form": null (pure deletion or insertion) or one of {ef},
 "flag": list of zero or more of {fl}, "rationale": one short sentence}}"""

USER = """Meeting context (speaker: utterance; [TARGET] is the reference sentence containing the error):
{context}

Reference (what was actually said) with the error marked as [[what was said → what ASR output]].
Left of the arrow = reference, right = ASR; ∅ = nothing on that side (∅ on the right = deletion,
∅ on the left = insertion):
{ref_marked}

Edit operation (from alignment): {op}

Full ASR output for this sentence:
{hyp}

Judge ONLY the marked span: assume every other recognition error in this sentence has been corrected.
Severity depends on how much meaning is changed or lost and how important that information is in this
conversation -- never on the content type alone, and never lowered because the correct information
appears elsewhere in the context."""


def build_messages(e, rubric):
    ctx = "\n".join(e["context_before"] + ["[TARGET] " + e["ref"]] + e["context_after"])
    return [
        {"role": "system", "content": SYSTEM.format(rubric=rubric, ct=CONTENT_TYPES, ef=ERROR_FORMS, fl=FLAGS)},
        {"role": "user", "content": USER.format(context=ctx, ref_marked=e["ref_marked"], op=e["op"], hyp=e["hyp"] or "∅")},
    ]


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    obj = json.loads(m.group(0))
    sev = int(obj["severity"])
    assert 1 <= sev <= 5
    ct = obj.get("content_type") if obj.get("content_type") in CONTENT_TYPES else "other"
    ef = obj.get("error_form") if obj.get("error_form") in ERROR_FORMS else None
    fl = obj.get("flag") or []
    fl = [f for f in ([fl] if isinstance(fl, str) else fl) if f in FLAGS]
    return {"severity": sev, "content_type": ct, "error_form": ef, "flag": fl,
            "rationale": obj.get("rationale", "")}


def load_dotenv():
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"\''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["azure", "openai"], default="azure")
    ap.add_argument("--azure_endpoint", default="https://demi-azure.openai.azure.com/")
    ap.add_argument("--api_version", default="2024-10-21")
    ap.add_argument("--ids", default=str(OUT / "llm_set_ids.txt"), help="file of error_ids, or 'all'")
    ap.add_argument("--model", default="gpt-4o", help="Azure deployment name or model id")
    ap.add_argument("--base_url", default="https://api.deepseek.com", help="openai backend only")
    ap.add_argument("--api_key_env", default=None, help="default: AZURE_API_KEY / DEEPSEEK_API_KEY")
    ap.add_argument("--tag", default=None, help="output tag; defaults to the model name")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    load_dotenv()
    args.tag = args.tag or args.model
    if args.backend == "azure":
        client = AzureOpenAI(api_key=os.environ[args.api_key_env or "AZURE_API_KEY"],
                             azure_endpoint=args.azure_endpoint, api_version=args.api_version)
    else:
        client = OpenAI(api_key=os.environ.get(args.api_key_env or "DEEPSEEK_API_KEY", "EMPTY"),
                        base_url=args.base_url)
    # GPT-5 / o-series reasoning models reject temperature and max_tokens.
    reasoning = re.match(r"(gpt-5|o\d)", args.model) is not None
    gen = ({"max_completion_tokens": 4000} if reasoning
           else {"max_tokens": 300, "temperature": args.temperature})
    rubric = (ROOT / "annotation" / "rubric.md").read_text()
    errors = {e["error_id"]: e for e in map(json.loads, open(OUT / "errors.jsonl"))}
    ids = list(errors) if args.ids == "all" else [l.strip() for l in open(args.ids) if l.strip()]
    ids = ids[:args.limit]

    out_path = OUT / f"llm_annotations_{args.tag}.jsonl"
    done = set()
    if out_path.exists():
        done = {json.loads(l)["error_id"] for l in open(out_path)}
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} requested, {len(done)} cached, {len(todo)} to annotate with {args.model}")

    def work(eid):
        msgs = build_messages(errors[eid], rubric)
        for attempt in range(3):
            try:
                r = client.chat.completions.create(model=args.model, messages=msgs, **gen,
                                                   response_format={"type": "json_object"})
                u = r.usage
                return {"error_id": eid, "model": args.model, **parse(r.choices[0].message.content),
                        "usage": {"prompt": u.prompt_tokens, "completion": u.completion_tokens}}
            except Exception as ex:  # malformed JSON or transient API error
                err = repr(ex)
        return {"error_id": eid, "model": args.model, "failed": err}

    n_fail = 0
    with open(out_path, "a") as f, ThreadPoolExecutor(args.workers) as pool:
        for fut in tqdm(as_completed([pool.submit(work, i) for i in todo]), total=len(todo)):
            res = fut.result()
            if "failed" in res:
                n_fail += 1
                continue  # not cached, so a rerun retries it
            f.write(json.dumps(res) + "\n")
            f.flush()
    print(f"done; {n_fail} failed")


if __name__ == "__main__":
    main()
