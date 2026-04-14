# CoverageCheck

CoverageCheck is a text-based health insurance benefits lookup tool. Members text plain-language questions — "what's my urgent care copay?" or "is therapy covered?" — and get a direct answer based on their plan's benefit structure. No app to download, no portal to log into. Just text and get an answer.

This is a portfolio demo project. It uses a single hardcoded fictional PPO plan rather than real member data.

---

## Architecture

```
Member SMS
    ↓
Twilio (receives SMS, sends webhook)
    ↓
FastAPI /sms endpoint
    ↓
Claude API (claude-haiku-4-5-20251001)
    ↓
FastAPI returns TwiML
    ↓
Twilio sends reply SMS
    ↓
Member SMS
```

---

## Local Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourusername/coveragecheck.git
cd coveragecheck
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Where to find it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `TWILIO_ACCOUNT_SID` | [console.twilio.com](https://console.twilio.com) → Account Info |
| `TWILIO_AUTH_TOKEN` | [console.twilio.com](https://console.twilio.com) → Account Info |
| `TWILIO_PHONE_NUMBER` | Twilio console → Phone Numbers |

For local development, set `VALIDATE_TWILIO_SIGNATURE=false` in your `.env` to skip signature checks (ngrok URLs change on each restart, which breaks validation).

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`. Test it's running:

```bash
curl http://localhost:8000/health
```

### 4. Expose localhost with ngrok (for Twilio webhooks)

Twilio needs a public URL to send webhooks to. During development, use [ngrok](https://ngrok.com):

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok.io` URL — you'll need it in the next step.

---

## Twilio Configuration

1. Log in to [console.twilio.com](https://console.twilio.com)
2. Go to **Phone Numbers → Manage → Active Numbers**
3. Click your CoverageCheck number
4. Under **Messaging**, set the webhook URL to:
   ```
   https://your-ngrok-or-railway-url.com/sms
   ```
   Method: **HTTP POST**
5. Save

Now text your Twilio number and you should get a response.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Deployment to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) and create a new project from your GitHub repo
3. Add environment variables in Railway's dashboard (same as your `.env`, but set `VALIDATE_TWILIO_SIGNATURE=true`)
4. Railway auto-detects the `Procfile` and deploys
5. Copy the Railway public URL and set it as your Twilio webhook (see above)

### Render

Same steps apply for [render.com](https://render.com). Create a new Web Service, connect the repo, set env vars, and use the render URL as your Twilio webhook.

---

## Project Structure

```
coveragecheck/
├── app/
│   ├── main.py        # FastAPI app + Twilio webhook endpoint
│   ├── sms.py         # Parse inbound SMS, build TwiML response
│   ├── benefits.py    # Load plan.json
│   ├── ai.py          # Claude API integration
│   └── prompts.py     # System prompt
├── data/
│   └── plan.json      # Fictional PPO benefit structure
├── tests/
│   ├── test_benefits.py
│   ├── test_ai.py
│   └── test_webhook.py
├── requirements.txt
├── Procfile
├── .env.example
└── README.md
```

---

## Notes

- **Rate limiting**: Each phone number is limited to 20 queries per hour (in-memory, resets on server restart).
- **Twilio signature validation**: Enabled by default in production to prevent unauthorized requests. Disable locally by setting `VALIDATE_TWILIO_SIGNATURE=false`.
- **Logging**: Incoming questions are logged without phone numbers for privacy.
- **Model**: Uses `claude-haiku-4-5-20251001` — fast and cheap, well-suited for constrained SMS responses.
