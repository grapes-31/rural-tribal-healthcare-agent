"""
Rural & Tribal Healthcare Access Agent
Flask Web Application — IBM Granite (ibm/granite-4-h-small) on watsonx.ai
Run:  python app.py
Open: http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
import requests
import threading

# ── IBM watsonx.ai Configuration ───────────────────────────────────────────────
API_KEY    = "plPofexQheLPn_4dgPkCpLInahQf-2WKhcfLptZ2KvcG"
PROJECT_ID = "bba47c87-2198-4ea8-b9d7-1b7c092ea274"
MODEL_ID   = "ibm/granite-4-h-small"
GEN_URL    = "https://eu-de.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
IAM_URL    = "https://iam.cloud.ibm.com/identity/token"

app = Flask(__name__)

# ── Thread-safe IAM token cache ────────────────────────────────────────────────
_token_lock   = threading.Lock()
_cached_token = None

def get_iam_token() -> str:
    global _cached_token
    with _token_lock:
        resp = requests.post(
            IAM_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": API_KEY,
            },
            timeout=30,
        )
        resp.raise_for_status()
        _cached_token = resp.json()["access_token"]
    return _cached_token


def generate_response(prompt: str) -> str:
    token = get_iam_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    body = {
        "model_id":   MODEL_ID,
        "project_id": PROJECT_ID,
        "input":      prompt,
        "parameters": {
            "decoding_method":    "greedy",
            "max_new_tokens":     600,
            "min_new_tokens":     30,
            "stop_sequences":     ["User:", "Human:"],
            "repetition_penalty": 1.1,
        },
    }
    resp = requests.post(GEN_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()["results"][0]["generated_text"].strip()


# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a compassionate Rural & Tribal Healthcare Access Agent.
Help people in rural, remote, and tribal communities with limited healthcare access.

You assist with:
1. SYMPTOM GUIDANCE - First-aid advice and urgency triage. When to seek immediate care.
2. NEARBY FACILITIES - PHC, CHC, District Hospital, AYUSH centres and how to reach them.
3. TELEMEDICINE - eSanjeevani and government telehealth services.
4. GOVERNMENT SCHEMES - Ayushman Bharat/PMJAY, NRHM, Janani Suraksha Yojana, tribal health plans.
5. MATERNAL & CHILD HEALTH - Antenatal care, immunisation schedules, Anganwadi/ICDS nutrition.
6. MENTAL HEALTH - NIMHANS (080-46110007), iCall (9152987821), Vandrevala Foundation (1860-2662-345).
7. TRADITIONAL MEDICINE - Respect local traditions, advise when modern care is essential.
8. EMERGENCY PROTOCOLS - Ambulance 108 (EMRI), what to do while waiting for help.

Rules:
- Use simple, clear language. Avoid medical jargon.
- Be culturally sensitive and respectful of tribal customs.
- Never diagnose. Provide guidance and referrals only.
- For emergencies (chest pain, breathing difficulty, unconsciousness, heavy bleeding, snakebite) always say: CALL 108 IMMEDIATELY.
- If unsure, advise visiting the nearest health facility.
- If the user writes in Hindi or another Indian language, reply in that language.
"""

# ── Conversation history (in-memory) ──────────────────────────────────────────
history: list[dict] = []


def build_prompt(user_msg: str) -> str:
    prompt = SYSTEM_PROMPT + "\n\nConversation:\n"
    for turn in history[-6:]:
        prompt += f"User: {turn['user']}\nAgent: {turn['agent']}\n\n"
    prompt += f"User: {user_msg}\nAgent:"
    return prompt


# ── HTML Chat Interface ────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Rural & Tribal Healthcare Agent</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:-apple-system,'Segoe UI',sans-serif;background:#0d1b2a;color:#e2e8f0;display:flex;flex-direction:column;height:100vh;overflow:hidden}

/* ── HEADER ── */
.header{background:linear-gradient(90deg,#0f4c2a,#1a6b3c);padding:14px 20px;display:flex;align-items:center;gap:12px;box-shadow:0 2px 10px #0006;flex-shrink:0}
.header-icon{font-size:1.8rem}
.header-text h1{font-size:1.1rem;font-weight:700;color:#fff}
.header-text p{font-size:.75rem;color:#86efac;margin-top:1px}
.header-badge{margin-left:auto;background:#065f46;border:1px solid #34d399;color:#6ee7b7;font-size:.7rem;padding:3px 10px;border-radius:999px}

/* ── LAYOUT ── */
.main{display:flex;flex:1;overflow:hidden}

/* ── SIDEBAR ── */
.sidebar{width:220px;background:#0f2133;border-right:1px solid #1e3a52;display:flex;flex-direction:column;overflow-y:auto;flex-shrink:0}
.sidebar-section{padding:14px 12px 6px}
.sidebar-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:8px}
.qbtn{display:flex;align-items:center;gap:8px;width:100%;background:transparent;border:none;color:#94a3b8;padding:8px 10px;border-radius:8px;cursor:pointer;font-size:.78rem;text-align:left;transition:all .15s}
.qbtn:hover{background:#1e3a52;color:#e2e8f0}
.qbtn .qi{font-size:1rem;width:20px;text-align:center;flex-shrink:0}
.sidebar-divider{height:1px;background:#1e3a52;margin:8px 12px}
.emergency{margin:auto 12px 14px;background:#1a0a0a;border:1px solid #7f1d1d;border-radius:10px;padding:12px;text-align:center}
.emergency .e-label{font-size:.65rem;font-weight:700;color:#fca5a5;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.emergency .e-num{font-size:1.5rem;font-weight:900;color:#fff;letter-spacing:3px}
.emergency .e-sub{font-size:.65rem;color:#fca5a5;margin-top:3px}

/* ── CHAT AREA ── */
.chat{flex:1;display:flex;flex-direction:column;overflow:hidden}
.messages{flex:1;overflow-y:auto;padding:20px 16px;display:flex;flex-direction:column;gap:14px}
.messages::-webkit-scrollbar{width:4px}
.messages::-webkit-scrollbar-thumb{background:#1e3a52;border-radius:2px}

/* ── WELCOME ── */
.welcome{background:#0f2133;border:1px solid #1e3a52;border-radius:14px;padding:20px;max-width:500px;align-self:center;margin:auto}
.welcome h2{font-size:.95rem;color:#34d399;margin-bottom:8px}
.welcome p{font-size:.82rem;color:#94a3b8;line-height:1.65}
.welcome ul{margin-top:10px;padding-left:16px;font-size:.8rem;color:#94a3b8;line-height:1.9}
.welcome li strong{color:#6ee7b7}

/* ── MESSAGES ── */
.msg{display:flex;gap:10px;max-width:80%;animation:rise .25s ease}
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.msg.user{align-self:flex-end;flex-direction:row-reverse}
.avatar{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0}
.msg.agent .avatar{background:#0f4c2a}
.msg.user  .avatar{background:#1e3a6e}
.bubble{padding:10px 14px;border-radius:14px;font-size:.85rem;line-height:1.65;white-space:pre-wrap;word-break:break-word;max-width:100%}
.msg.agent .bubble{background:#0f2133;border:1px solid #1e3a52;color:#d1fae5;border-bottom-left-radius:3px}
.msg.user  .bubble{background:#1e3a6e;color:#dbeafe;border-bottom-right-radius:3px}
.ts{font-size:.62rem;color:#334155;margin-top:4px;align-self:flex-end}

/* ── TYPING ── */
.typing-wrap{display:flex;gap:10px;align-items:center}
.typing-wrap .avatar{background:#0f4c2a}
.dots{display:flex;gap:4px;padding:10px 14px;background:#0f2133;border:1px solid #1e3a52;border-radius:14px;border-bottom-left-radius:3px}
.dots span{width:7px;height:7px;background:#34d399;border-radius:50%;animation:dot 1.2s infinite}
.dots span:nth-child(2){animation-delay:.2s}
.dots span:nth-child(3){animation-delay:.4s}
@keyframes dot{0%,80%,100%{opacity:.2;transform:scale(.8)}40%{opacity:1;transform:scale(1)}}

/* ── INPUT ── */
.input-row{padding:12px 16px;background:#0f2133;border-top:1px solid #1e3a52;display:flex;gap:8px;align-items:flex-end;flex-shrink:0}
.input-row textarea{flex:1;background:#0d1b2a;border:1px solid #1e3a52;border-radius:10px;color:#e2e8f0;font-family:inherit;font-size:.85rem;padding:10px 13px;resize:none;outline:none;min-height:42px;max-height:110px;line-height:1.5;transition:border-color .2s}
.input-row textarea:focus{border-color:#34d399}
.input-row textarea::placeholder{color:#334155}
.btn-send{width:42px;height:42px;border-radius:10px;background:#0f4c2a;border:none;color:#fff;font-size:1.1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .2s}
.btn-send:hover{background:#1a6b3c}
.btn-send:disabled{background:#1e3a52;cursor:not-allowed}
.btn-reset{height:42px;padding:0 12px;border-radius:10px;background:transparent;border:1px solid #1e3a52;color:#64748b;font-size:.75rem;cursor:pointer;flex-shrink:0;transition:all .2s}
.btn-reset:hover{background:#1e3a52;color:#e2e8f0}

/* ── STATUS ── */
.status{background:#0a1520;border-top:1px solid #1e3a52;padding:5px 16px;display:flex;gap:16px;font-size:.68rem;color:#334155;flex-shrink:0}
.pulse{display:inline-block;width:6px;height:6px;background:#34d399;border-radius:50%;margin-right:5px;animation:p 2s infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.3}}
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div class="header-icon">🏥</div>
  <div class="header-text">
    <h1>Rural &amp; Tribal Healthcare Access Agent</h1>
    <p>Compassionate AI guidance for remote &amp; tribal communities</p>
  </div>
  <div class="header-badge">IBM Granite · watsonx.ai</div>
</div>

<div class="main">

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">Quick Topics</div>
      <button class="qbtn" onclick="ask('What first-aid should I give for high fever in a child?')"><span class="qi">🤒</span>Child Fever</button>
      <button class="qbtn" onclick="ask('How do I use the eSanjeevani telemedicine service?')"><span class="qi">📱</span>Telemedicine</button>
      <button class="qbtn" onclick="ask('Tell me about Ayushman Bharat PMJAY scheme benefits')"><span class="qi">💊</span>Ayushman Bharat</button>
      <button class="qbtn" onclick="ask('What healthcare facilities are available in rural areas?')"><span class="qi">🏥</span>Nearby Facilities</button>
      <button class="qbtn" onclick="ask('Guide me on antenatal care for pregnant women in tribal areas')"><span class="qi">🤰</span>Maternal Health</button>
      <button class="qbtn" onclick="ask('What immunizations does my 6-month-old baby need?')"><span class="qi">💉</span>Immunisation</button>
      <button class="qbtn" onclick="ask('What mental health helplines are available in rural India?')"><span class="qi">🧠</span>Mental Health</button>
      <button class="qbtn" onclick="ask('A person was bitten by a snake. What do I do immediately?')"><span class="qi">🐍</span>Snakebite</button>
      <button class="qbtn" onclick="ask('Tell me about the National Rural Health Mission NRHM')"><span class="qi">📋</span>NRHM Scheme</button>
      <button class="qbtn" onclick="ask('How does Anganwadi help children get nutrition support?')"><span class="qi">🌾</span>Anganwadi / ICDS</button>
    </div>
    <div class="sidebar-divider"></div>
    <div class="emergency">
      <div class="e-label">🚨 Emergency</div>
      <div class="e-num">📞 108</div>
      <div class="e-sub">National Ambulance</div>
      <div class="e-sub">Available 24×7 across India</div>
    </div>
  </div>

  <!-- CHAT -->
  <div class="chat">
    <div class="messages" id="msgs">
      <div class="welcome">
        <h2>🌿 Welcome — How can I help you today?</h2>
        <p>I am your <strong style="color:#6ee7b7">Rural &amp; Tribal Healthcare Access Agent</strong>, here to help communities with limited healthcare access.</p>
        <ul>
          <li><strong>Symptom guidance</strong> &amp; first-aid triage</li>
          <li><strong>Nearby PHC / CHC</strong> / District Hospital</li>
          <li><strong>eSanjeevani</strong> telemedicine services</li>
          <li><strong>Govt schemes</strong> — Ayushman Bharat, NRHM, JSY</li>
          <li><strong>Maternal &amp; child</strong> health support</li>
          <li><strong>Mental health</strong> helplines</li>
        </ul>
        <p style="margin-top:10px;font-size:.75rem;color:#475569">Type below or click a topic on the left →</p>
      </div>
    </div>

    <div class="input-row">
      <textarea id="inp" rows="1" placeholder="Ask your health question… (e.g. My child has fever for 2 days, what should I do?)"
        onkeydown="onKey(event)" oninput="resize(this)"></textarea>
      <button class="btn-reset" onclick="resetChat()">🔄 Reset</button>
      <button class="btn-send" id="sendBtn" onclick="send()">➤</button>
    </div>

    <div class="status">
      <span><span class="pulse"></span>Connected · IBM watsonx.ai</span>
      <span>Model: ibm/granite-4-h-small</span>
      <span>Region: eu-de (Frankfurt)</span>
    </div>
  </div>
</div>

<script>
  function now(){
    const d=new Date();
    return d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0');
  }
  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

  function addMsg(role,text){
    const box=document.getElementById('msgs');
    const d=document.createElement('div');
    d.className='msg '+role;
    const av=role==='agent'?'🏥':'👤';
    d.innerHTML=`<div class="avatar">${av}</div><div><div class="bubble">${esc(text)}</div><div class="ts">${now()}</div></div>`;
    box.appendChild(d);
    box.scrollTop=box.scrollHeight;
  }

  function showTyping(){
    const box=document.getElementById('msgs');
    const d=document.createElement('div');
    d.className='msg agent'; d.id='typing';
    d.innerHTML='<div class="avatar">🏥</div><div class="dots"><span></span><span></span><span></span></div>';
    box.appendChild(d);
    box.scrollTop=box.scrollHeight;
  }
  function hideTyping(){const t=document.getElementById('typing');if(t)t.remove();}

  async function send(){
    const inp=document.getElementById('inp');
    const msg=inp.value.trim();
    if(!msg)return;
    inp.value=''; resize(inp);
    addMsg('user',msg);
    document.getElementById('sendBtn').disabled=true;
    showTyping();
    try{
      const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
      const data=await r.json();
      hideTyping();
      addMsg('agent', data.error ? '⚠️ '+data.error : data.response);
    }catch(e){
      hideTyping();
      addMsg('agent','⚠️ Network error — please try again.');
    }
    document.getElementById('sendBtn').disabled=false;
    document.getElementById('inp').focus();
  }

  async function resetChat(){
    await fetch('/reset',{method:'POST'});
    const box=document.getElementById('msgs');
    box.innerHTML='<div class="welcome"><h2 style="color:#34d399">🔄 Conversation reset</h2><p style="color:#94a3b8;margin-top:6px;font-size:.82rem">How can I help you with your health question?</p></div>';
  }

  function ask(q){document.getElementById('inp').value=q;send();}
  function onKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}}
  function resize(t){t.style.height='auto';t.style.height=Math.min(t.scrollHeight,110)+'px';}
</script>
</body>
</html>
"""

# ── In-memory conversation history ────────────────────────────────────────────
history: list[dict] = []


# ── Flask Routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400
    try:
        prompt   = build_prompt(user_msg)
        response = generate_response(prompt)
        history.append({"user": user_msg, "agent": response})
        return jsonify({"response": response})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/reset", methods=["POST"])
def reset():
    history.clear()
    return jsonify({"status": "ok"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_ID})


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print()
    print("=" * 52)
    print("  🏥  Rural & Tribal Healthcare Access Agent")
    print("      Powered by IBM Granite on watsonx.ai")
    print("=" * 52)
    print("  🌐  http://localhost:5000")
    print("  Press Ctrl+C to stop")
    print("=" * 52)
    print()
    app.run(host="0.0.0.0", port=5000, debug=False)
