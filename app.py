import os, time
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from hindsight_client import Hindsight
from data import INCIDENTS, as_text

load_dotenv()
BANK = "oncall-agent"
hs = Hindsight(base_url=os.getenv("HINDSIGHT_URL", "https://api.hindsight.vectorize.io"),
               api_key=os.getenv("HINDSIGHT_API_KEY"))
llm = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
MODELS = [os.getenv("LLM_MODEL", "openai/gpt-oss-120b"), os.getenv("LLM_FALLBACK", "qwen/qwen3-32b")]

SYSTEM = ("You are an on-call SRE copilot. Give: 1) likely root cause, 2) first three actions, "
          "3) what NOT to try. If past incidents are provided, ground your answer in them, cite the "
          "service and outcome, and say when a past fix failed. If none are provided, give generic advice. Be concise.")

def ask(prompt):
    last = None
    for model in MODELS:                      # retry, then fall back to second model
        for attempt in range(2):
            try:
                r = llm.chat.completions.create(model=model, temperature=0.2,
                    messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}])
                return r.choices[0].message.content
            except Exception as e:            # function-calling / rate-limit errors
                last = e; time.sleep(1.5 * (attempt + 1))
    return f"LLM unavailable: {last}"

class Triage(BaseModel):
    alert: str
    use_memory: bool = True

class Resolve(BaseModel):
    alert: str
    fix: str
    worked: bool

app = FastAPI(title="Oncall Memory Agent")

@app.post("/api/seed")
def seed():
    for i in INCIDENTS:
        hs.retain(bank_id=BANK, content=as_text(i), context="incident postmortem")
    return {"seeded": len(INCIDENTS)}

@app.post("/api/triage")
def triage(t: Triage):
    memories = []
    prompt = f"New alert: {t.alert}"
    if t.use_memory:
        try:
            res = hs.recall(bank_id=BANK, query=t.alert)
            memories = [getattr(m, "text", str(m)) for m in res.results[:6]]
        except Exception as e:
            memories = []
        if memories:
            prompt += "\n\nPast incidents from team memory:\n- " + "\n- ".join(memories)
    return {"answer": ask(prompt), "memories": memories}

@app.post("/api/resolve")
def resolve(r: Resolve):
    hs.retain(bank_id=BANK, context="incident outcome",
              content=f"Alert: {r.alert}. Fix attempted: {r.fix}. Outcome: {'WORKED' if r.worked else 'DID NOT WORK'}.")
    return {"ok": True}

@app.get("/api/insights")
def insights():
    q = ("Across all incidents, what recurring root-cause patterns exist, which fixes reliably worked, "
         "which failed, and what permanent fixes should the team prioritize?")
    try:
        return {"text": hs.reflect(bank_id=BANK, query=q).text}
    except Exception as e:
        return {"text": f"Reflect unavailable: {e}"}

@app.get("/")
def index():
    return FileResponse("static/index.html")
app.mount("/static", StaticFiles(directory="static"), name="static")
