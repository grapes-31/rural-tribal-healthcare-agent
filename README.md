# 🏥 Rural & Tribal Healthcare Access Agent

A conversational AI agent powered by **IBM Granite (ibm/granite-4-h-small)** on **watsonx.ai**,
built to help people in rural, remote, and tribal communities access healthcare guidance.

---

## ▶️ Run the App

```bash
# Step 1 — Install dependencies (one-time)
python -m pip install flask requests

# Step 2 — Start the server
python app.py

# Step 3 — Open in browser
http://localhost:5000
```

> **On this machine (Anaconda):**
> ```
> C:\Users\nairm\anaconda3\python.exe -m pip install flask requests
> C:\Users\nairm\anaconda3\python.exe app.py
> ```

---

## 💬 What the Agent Can Do

| Topic | Details |
|---|---|
| 🤒 Symptom Guidance | First-aid advice, urgency triage |
| 🏥 Nearby Facilities | PHC / CHC / District Hospital / AYUSH |
| 📱 Telemedicine | eSanjeevani and government telehealth |
| 💊 Govt Schemes | Ayushman Bharat PMJAY, NRHM, JSY |
| 🤰 Maternal & Child | Antenatal care, immunisation, Anganwadi |
| 🧠 Mental Health | NIMHANS, iCall, Vandrevala Foundation |
| 🌿 Traditional Medicine | Culturally respectful guidance |
| 🚨 Emergency | Always directs to **108** (EMRI ambulance) |

---

## 🗂️ Project Files

| File | Purpose |
|---|---|
| `app.py` | Flask server + full chat web UI |
| `agent.py` | Standalone CLI version |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

---

## 🔌 API Details

| Setting | Value |
|---|---|
| Model | ibm/granite-4-h-small |
| Region | eu-de (Frankfurt) |
| Endpoint | eu-de.ml.cloud.ibm.com |
| Max tokens | 600 |
| Decoding | greedy |

---

## 🚨 Emergency

> **Call 108** — National Ambulance & Emergency Service, available 24×7 across India.

---

## ⚠️ Disclaimer

This agent provides **general health information only** and is **not a substitute**
for professional medical diagnosis or treatment. Always consult a qualified
healthcare professional.
