"""Local one-card-at-a-time review app for silver label drafts.

Each card is one criterion of one report: a plain-English question, the draft answer, the quote,
and the cited PDF page rendered as an image. Answers are saved to data/silver/review/answers.json.

Run (base environment, which has fastapi, uvicorn and pypdfium2):
    apctt-env/base/bin/python dev/review_app.py USGS-SDG-030 USGS-SDG-096 USGS-SDG-007 USGS-SDG-077 USGS-SDG-089
then open http://127.0.0.1:8765
"""

from __future__ import annotations

import io
import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, Response  # noqa: E402
from pydantic import BaseModel  # noqa: E402

SILVER = harness.ROOT / "data" / "silver"
ANSWERS = SILVER / "review" / "answers.json"
LOCK = threading.Lock()

QUESTIONS = {
    1: "Does the report explain the science or method this technology is based on (theory, equations, or earlier studies it builds on)?",
    2: "Does the report say what this technology is for and how it is meant to be used?",
    3: "Does the report show results (calculations or simulations) proving the technology's main function works?",
    4: "Does the report say the technology was tested in a laboratory or other controlled setting, and give the results? (Field work does not count.)",
    5: "Does the report say the technology was checked against real field measurements (for example calibrated or validated against observed data), with results?",
    6: "Does the report say a working version was actually applied or demonstrated in the real study area to produce results?",
    7: "Does the report say it is in real use by its users (real-time operation, public website, agencies relying on it)?",
    8: "Does the report say the FINAL version was completed and formally approved, certified, or tested against its stated requirements?",
    9: "Does the report say the final system has been used successfully in real operations over a stated time period (for example 'since 2005')?",
    10: "Does the report compare measured performance with a STATED target or requirement, and say whether it was met?",
    11: "Does the report describe the test conditions and the setup or version of what was tested?",
    12: "Is the evidence about this exact technology, not a different tool or only the overall project?",
}


def criterion_number(cid: str) -> int:
    digits = "".join(ch for ch in cid if ch.isdigit())
    return int(digits[-2:]) if digits else 0


def build_items(case_ids: list[str]) -> list[dict]:
    items = []
    for case_id in case_ids:
        label = json.loads((SILVER / f"{case_id}.json").read_text())
        meta = harness.manifest_case(case_id)
        for cid, entry in label["criteria"].items():
            pages = [g["page"] for g in entry.get("gold_pages", [])]
            items.append({
                "key": f"{case_id}|{cid}",
                "case_id": case_id,
                "title": meta["title"],
                "target": meta["assessment_target"]["description"],
                "page_count": meta["page_count"],
                "criterion_id": cid,
                "question": QUESTIONS.get(criterion_number(cid), cid),
                "draft": entry["status"],
                "pages": pages,
                "quote": entry.get("quote", ""),
                "note": entry.get("note", ""),
            })
    return items


def load_answers() -> dict:
    if ANSWERS.exists():
        return json.loads(ANSWERS.read_text())
    return {}


class Answer(BaseModel):
    key: str
    verdict: str  # agree | disagree | unsure
    label: str | None = None
    page: int | None = None
    comment: str | None = None


def create_app(case_ids: list[str]) -> FastAPI:
    app = FastAPI()
    items = build_items(case_ids)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return PAGE

    @app.get("/api/items")
    def get_items() -> dict:
        return {"items": items, "answers": load_answers()}

    @app.post("/api/answer")
    def post_answer(answer: Answer) -> dict:
        with LOCK:
            answers = load_answers()
            answers[answer.key] = answer.model_dump()
            ANSWERS.parent.mkdir(parents=True, exist_ok=True)
            ANSWERS.write_text(json.dumps(answers, indent=2) + "\n")
        return {"saved": len(answers)}

    @app.get("/page/{case_id}/{page}.png")
    def page_image(case_id: str, page: int) -> Response:
        if case_id not in case_ids:
            raise HTTPException(404)
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(harness.PDF_DIR / f"{case_id}.pdf"))
        try:
            if not 1 <= page <= len(pdf):
                raise HTTPException(404)
            image = pdf[page - 1].render(scale=1.6).to_pil()
        finally:
            pdf.close()
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return Response(buffer.getvalue(), media_type="image/png")

    @app.get("/pdf/{case_id}.pdf")
    def pdf_file(case_id: str) -> FileResponse:
        if case_id not in case_ids:
            raise HTTPException(404)
        return FileResponse(harness.PDF_DIR / f"{case_id}.pdf", media_type="application/pdf")

    return app


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Label review</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#1d1d1f;--muted:#6b6b70;--line:#e3e1dc;--accent:#2f5d50;--agree:#2f7d4f;--dis:#b3452f;--unsure:#8a6d1f}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--card:#1f1f1f;--ink:#ececec;--muted:#a0a0a5;--line:#333;--accent:#7fb3a3}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center;z-index:2}
.bar{flex:1;height:8px;background:var(--line);border-radius:4px;overflow:hidden}.bar>div{height:100%;background:var(--accent)}
main{display:grid;grid-template-columns:minmax(320px,440px) 1fr;gap:16px;padding:16px;max-width:1500px;margin:auto}
@media (max-width:900px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
h1{font-size:13px;color:var(--muted);margin:0 0 4px;font-weight:600}h2{font-size:18px;margin:0 0 12px;line-height:1.35}
.pill{display:inline-block;padding:2px 10px;border-radius:99px;background:var(--line);font-weight:600;font-size:13px}
.quote{border-left:3px solid var(--accent);padding:6px 10px;margin:10px 0;background:color-mix(in srgb,var(--accent) 8%,transparent)}
.muted{color:var(--muted);font-size:13px}
button{font:inherit;padding:9px 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
button.agree{background:var(--agree);color:#fff;border:0}button.dis{background:var(--dis);color:#fff;border:0}button.unsure{background:var(--unsure);color:#fff;border:0}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
select,input,textarea{font:inherit;padding:7px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--ink);width:100%}
.pages button{padding:4px 10px}.pages button.on{background:var(--accent);color:#fff;border:0}
img{max-width:100%;border:1px solid var(--line);border-radius:6px;background:#fff}
.steps{margin:0;padding-left:18px}.done{color:var(--agree);font-weight:600}
</style></head><body>
<header><strong>Label review</strong><div class="bar"><div id="prog"></div></div><span id="count" class="muted"></span></header>
<main><section class="card" id="left"></section><section class="card" id="right"></section></main>
<script>
let items=[],answers={},i=0,page=null;
const $=s=>document.querySelector(s);
async function load(){const r=await fetch('/api/items');const d=await r.json();items=d.items;answers=d.answers;
 i=items.findIndex(it=>!answers[it.key]);if(i<0)i=items.length;render();}
function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function render(){const n=Object.keys(answers).length;$('#prog').style.width=(100*n/items.length)+'%';$('#count').textContent=n+' / '+items.length+' answered';
 if(i>=items.length){$('#left').innerHTML='<h2 class="done">All done. Thank you!</h2><p>Your answers are saved in data/silver/review/answers.json. Tell Claude you are finished.</p><div class="row"><button onclick="i=0;render()">Go back to the first card</button></div>';$('#right').innerHTML='';return;}
 const it=items[i];page=it.pages[0]||null;const a=answers[it.key];
 const met=it.draft==='met';
 $('#left').innerHTML=`<h1>${esc(it.case_id)} · ${esc(it.criterion_id)} · card ${i+1} of ${items.length}</h1>
 <h2>${esc(it.question)}</h2>
 <p class="muted">Technology: ${esc(it.target)}</p>
 <p>Draft answer: <span class="pill">${esc(it.draft)}</span></p>
 ${met?`<p class="muted">The draft says the proof is on page(s) ${it.pages.join(', ')}. Look for this sentence on the page image:</p><div class="quote">${esc(it.quote)}</div>`:`<p class="muted">The draft found no page that shows this. If you know a page that does, choose Disagree and enter it.</p>`}
 <p class="muted">Why: ${esc(it.note)}</p>
 <ol class="steps muted"><li>Read the question.</li><li>${met?'Check the page on the right: is the quote there, and does it really answer yes?':'Skim the full PDF if you like (link on the right).'}</li><li>Click one button.</li></ol>
 <div class="row"><button class="agree" onclick="save('agree')">Agree</button><button class="dis" onclick="toggleDis()">Disagree</button><button class="unsure" onclick="save('unsure')">Not sure</button></div>
 <div id="dis" style="display:none;margin-top:12px">
  <label class="muted">Your answer</label><select id="lab"><option>met</option><option>not met</option><option>insufficient evidence</option></select>
  <label class="muted">Page that proves it (PDF page number, if met)</label><input id="pg" type="number" min="1" max="${it.page_count}">
  <label class="muted">Short reason (optional)</label><textarea id="cm" rows="2"></textarea>
  <div class="row"><button class="dis" onclick="saveDis()">Save disagreement</button></div></div>
 ${a?`<p class="muted">Already answered: <b>${esc(a.verdict)}</b>${a.label?' → '+esc(a.label):''}${a.page?' (p'+a.page+')':''}</p>`:''}
 <div class="row"><button onclick="move(-1)">← Back</button><button onclick="move(1)">Skip →</button></div>`;
 renderRight(it);}
function renderRight(it){const btns=it.pages.map(p=>`<button class="${p===page?'on':''}" onclick="page=${p};renderRight(items[i])">p${p}</button>`).join(' ');
 $('#right').innerHTML=`<div class="row pages" style="margin-top:0;align-items:center">${btns}<a class="muted" href="/pdf/${it.case_id}.pdf${page?'#page='+page:''}" target="_blank">Open the full PDF${page?' at page '+page:''} ↗</a></div>
 ${page?`<p class="muted">Page ${page} of ${it.page_count}</p><img src="/page/${it.case_id}/${page}.png" alt="PDF page ${page}">`:'<p class="muted">No page cited for this draft.</p>'}`;}
function toggleDis(){const d=$('#dis');d.style.display=d.style.display==='none'?'block':'none';}
async function send(body){const r=await fetch('/api/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(r.ok){answers[body.key]=body;move(1);}else alert('Could not save, please try again.');}
function save(v){send({key:items[i].key,verdict:v});}
function saveDis(){const pg=parseInt($('#pg').value);send({key:items[i].key,verdict:'disagree',label:$('#lab').value,page:isNaN(pg)?null:pg,comment:$('#cm').value||null});}
function move(d){i=Math.max(0,Math.min(items.length,i+d));render();window.scrollTo(0,0);}
load();
</script></body></html>"""


if __name__ == "__main__":
    import uvicorn

    cases = [harness.select_cases([c])[0] for c in sys.argv[1:]] or [
        "USGS-SDG-030", "USGS-SDG-096", "USGS-SDG-007", "USGS-SDG-077", "USGS-SDG-089"]
    uvicorn.run(create_app(cases), host="127.0.0.1", port=8765, log_level="warning")
