"""
Rural & Tribal Healthcare Access Agent
Powered by IBM Granite (ibm/granite-4-h-small) on watsonx.ai
"""

import os
import json
import requests

# ── Configuration ──────────────────────────────────────────────────────────────
API_KEY    = "plPofexQheLPn_4dgPkCpLInahQf-2WKhcfLptZ2KvcG"
PROJECT_ID = "bba47c87-2198-4ea8-b9d7-1b7c092ea274"
MODEL_ID   = "ibm/granite-4-h-small"
GEN_URL    = "https://eu-de.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
IAM_URL    = "https://iam.cloud.ibm.com/identity/token"

# ── IAM Token ──────────────────────────────────────────────────────────────────
def get_iam_token(api_key: str) -> str:
    """Exchange IBM Cloud API key for a Bearer token."""
    response = requests.post(
        IAM_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


# ── Granite Generation ─────────────────────────────────────────────────────────
def generate_response(token: str, prompt: str) -> str:
    """Call the watsonx.ai text generation endpoint."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {
        "model_id": MODEL_ID,
        "project_id": PROJECT_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 600,
            "min_new_tokens": 30,
            "stop_sequences": ["User:", "Human:"],
            "repetition_penalty": 1.1,
        },
    }
    response = requests.post(GEN_URL, headers=headers, json=body, timeout=60)
    response.raise_for_status()
    result = response.json()
    return result["results"][0]["generated_text"].strip()


# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a compassionate and knowledgeable Rural & Tribal Healthcare Access Agent.
Your mission is to assist people living in rural, remote, and tribal communities who have limited access to healthcare.

You can help with:
1. SYMPTOM GUIDANCE — Describe symptoms and get first-aid advice and urgency triage (when to seek immediate care).
2. NEARBY RESOURCES — Suggest types of healthcare facilities (PHC, CHC, District Hospital, AYUSH centres) and how to locate them.
3. TELEMEDICINE — Explain how to use government telemedicine services like eSanjeevani (India) or tribal health programmes.
4. GOVERNMENT SCHEMES — Provide information on Ayushman Bharat / PMJAY, Janani Suraksha Yojana, National Rural Health Mission (NRHM), and tribal sub-plans.
5. MATERNAL & CHILD HEALTH — Guide on antenatal care, immunisation schedules, nutrition (ICDS/Anganwadi), and safe delivery.
6. MENTAL HEALTH — Offer information on NIMHANS helplines, iCall, Vandrevala Foundation, and stress/trauma support.
7. TRADITIONAL & INTEGRATIVE MEDICINE — Respect local healing traditions while advising when modern medicine is essential.
8. EMERGENCY PROTOCOLS — Ambulance numbers (108 in India), EMRI, and what to do while waiting for help.

Guidelines:
- Use simple, clear language. Avoid jargon.
- Be culturally sensitive and respectful of tribal customs.
- Always recommend consulting a qualified healthcare professional for diagnosis and treatment.
- For emergencies (chest pain, difficulty breathing, unconsciousness, heavy bleeding, snakebite), always say CALL 108 IMMEDIATELY.
- Do not diagnose; provide guidance and referrals only.
- When unsure, err on the side of caution and advise visiting the nearest health facility.

You are multilingual — if the user writes in Hindi or another Indian language, respond in the same language.
"""


# ── Conversation Memory ────────────────────────────────────────────────────────
class HealthAgent:
    def __init__(self):
        print("🔐 Authenticating with IBM Cloud…")
        self.token = get_iam_token(API_KEY)
        self.history: list[dict] = []
        print("✅ Authentication successful.\n")

    def _build_prompt(self, user_message: str) -> str:
        """Build a full prompt from system context + conversation history."""
        prompt = SYSTEM_PROMPT + "\n\n"
        prompt += "Conversation so far:\n"
        for turn in self.history[-6:]:          # keep last 6 turns (3 exchanges)
            prompt += f"User: {turn['user']}\nAgent: {turn['agent']}\n\n"
        prompt += f"User: {user_message}\nAgent:"
        return prompt

    def chat(self, user_message: str) -> str:
        """Send a message and return the agent's response."""
        prompt   = self._build_prompt(user_message)
        response = generate_response(self.token, prompt)
        self.history.append({"user": user_message, "agent": response})
        return response

    def reset(self):
        """Clear conversation history."""
        self.history = []
        print("🔄 Conversation history cleared.\n")


# ── CLI Banner ─────────────────────────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════════════════════════════════╗
║        🏥  RURAL & TRIBAL HEALTHCARE ACCESS AGENT  🏥                  ║
║        Powered by IBM Granite on watsonx.ai                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║  I can help you with:                                                   ║
║  • Symptom guidance & first-aid triage                                  ║
║  • Nearby health facilities (PHC / CHC / District Hospital)             ║
║  • Telemedicine (eSanjeevani & government services)                     ║
║  • Government health schemes (Ayushman Bharat, NRHM, JSY…)             ║
║  • Maternal & child health, immunisation, nutrition                     ║
║  • Mental health helplines & support                                    ║
║  • Emergency protocols — Ambulance: 108                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Commands:  'reset' — clear chat history  |  'quit' — exit             ║
╚══════════════════════════════════════════════════════════════════════════╝
"""


# ── Main Loop ──────────────────────────────────────────────────────────────────
def main():
    print(BANNER)
    agent = HealthAgent()

    print("Agent: Hello! I am your Rural & Tribal Healthcare Access Agent.")
    print("       How can I help you today? (Type your question below)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAgent: Take care and stay healthy. Goodbye! 🙏")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "bye"}:
            print("Agent: Take care and stay healthy. Goodbye! 🙏")
            break

        if user_input.lower() == "reset":
            agent.reset()
            print("Agent: Memory cleared. How can I help you?\n")
            continue

        print("\nAgent: ", end="", flush=True)
        try:
            reply = agent.chat(user_input)
            print(reply)
        except requests.exceptions.HTTPError as e:
            print(f"[API Error] {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"[Error] {e}")
        print()


if __name__ == "__main__":
    main()
