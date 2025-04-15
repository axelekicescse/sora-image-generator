
# 🧱 Autonomous Module – Image Generation via Sora from a Text Prompt

## 📌 Strategic Objective

This module is a standalone unit designed to integrate into a future multi-agent architecture.  
Its goal is precise and simple: **generate an AI image from a text prompt using sora.com** (a web interface with no public API).

This script does one job and must do it **perfectly**, in a way that is:

- Robust  
- Modular  
- Reusable  
- Extensible  

> ⚠️ This is not a prototype. This is a **production-grade component**, meant to be orchestrated in an automated pipeline (e.g., AI-driven TikTok content generation).

## 🎯 Module Responsibilities

- Read a prompt from `prompt.txt`
- Open sora.com in a Playwright-controlled browser (with stored session)
- Inject the prompt into the prompt field
- Start image generation
- Wait until the image is fully generated (no blind `sleep()`)
- Download the final image
- Save it in the `/images/` folder
- Log all actions in `/logs/` with timestamps

## 🧠 Project Context

This module will be integrated into a larger pipeline like so:

```
[GPT Prompt Generator] → [Image Generator (this module)] → [Video Creator] → [TikTok Captioning] → [Uploader]
```

It must therefore be:

- Plug-and-play  
- Independent from other agents  
- Driven solely by `prompt.txt` as input  
- Producing only `/images/` as output  
- Re-runnable, idempotent, loggable, and crash-safe

## 🔧 Project Structure

```
project/
├── generate_image_from_prompt.py       # Main executable
├── sora_utils.py                       # Function library (navigation, scraping)
├── prompt.txt                          # Text prompt (1 line)
├── session.json                        # Saved Playwright session (see below)
├── /images/                            # Output images
├── /logs/                              # Logs per session
├── .env                                # Optional config
└── README.md                           # This file
```

## ⚙️ Functional Overview

- Reads `prompt.txt`
  - If missing or empty, stop cleanly with error log
- Opens Sora using Playwright and `session.json`
  - If missing, show:
    `"Missing session. Please login manually to sora.com and export session.json."`
- Injects the prompt
- Clicks generate
- Waits smartly until image is ready
- Downloads the final image (not the thumbnail)
- Saves it as `YYYYMMDD_HHMMSS_hash.png` in `/images/`
- Logs the entire operation in `/logs/`

## 🔐 Session via Playwright

> ❗ Never include automated login code.

### ✅ Manual Setup:

```python
browser = playwright.chromium.launch(headless=False)
context = browser.new_context()
page = context.new_page()
page.goto("https://sora.com")
# Manually login here
context.storage_state(path="session.json")
```

## 📄 Sample Prompt

```
Futuristic woman in soft red lighting, wearing a latex suit, in a messy bedroom with analog TV and retro posters, cinematic lighting, 8K.
```

## ▶️ Run Command

```bash
python generate_image_from_prompt.py
```

## 🧪 Validation Checklist

| Test Case                   | Expected Result                          |
|-----------------------------|-------------------------------------------|
| `prompt.txt` missing/empty | Script stops, clean error shown           |
| `session.json` missing     | Script stops, clean error shown           |
| Valid prompt               | Image is generated and saved              |
| DOM broken/missing         | Logs error, does not crash                |
| Re-run                     | Existing images not overwritten           |
| Logs                       | Written cleanly with timestamp and result |

## 🧠 Developer Guidelines for Devin

- Break complex logic into helpers (`sora_utils.py`)
- Handle all failures safely
- Always log
- Use clear variable names
- Follow production practices

## 📦 Versioning

This module follows semantic versioning:
- `v1.x.x`: basic prompt → image
- `v2.x.x`: CLI options, multi-prompts
- `v3.x.x`: multi-agent integration

File format:
```
YYYYMMDD_HHMMSS_<hash>.png
```

## 🗃️ Log Format

Success:
```
[2025-04-15 18:42:01]
Prompt used: "Futuristic latex woman..."
Status: SUCCESS
File: /images/20250415_184201_a1b2c.png
Time: 23.4s
```

Failure:
```
[2025-04-15 18:45:09]
Prompt: "..."
Status: FAILURE
Error: TimeoutException on 'image-preview'
```

## 🛠️ Future Debug Mode (optional)

Possible flags:
- `--debug`: opens browser visibly
- Screenshot capture
- Saves intermediate states in `/debug_screenshots/`

## 🧱 Extensibility Targets

- Multi-prompt batch
- Post-processing
- Captioning
- Upload via FastAPI agent

## ⚙️ Config File (optional)

Use `.env` or `config.yaml` for:
- Custom paths
- Timeouts
- Retry policies

## 🔐 Security Rules

- Never commit:
  - `.env`
  - `session.json`
  - `/images/`
  - `/logs/`

---

## 🔐 Files Not Included in Repo

For security reasons, the following files are **not included in the GitHub repo**:

- `session.json` ← required to access sora.com
- `prompt.txt` ← test prompt to trigger image generation

🧪 Download link:  
https://wetransfer.com/xxxxxxxx

⚠️ Place both files in the **root of the project** before running any script.  
Also, manually create `/images/` and `/logs/` folders if missing.

---

## ✅ Developer Action Plan

Once files are in place, your mission is:

- Code only `generate_image_from_prompt.py` and `sora_utils.py`
- Follow the README exactly
- No extra features, no shortcuts

The script must:
- Read from `prompt.txt`
- Use `session.json` to access sora
- Generate and download the image into `/images/`

🧱 I want **clean, modular, commented, reusable** production-grade code.  
Not a prototype. Not a draft. A real building block.

> **Everything is ready. If you read this README properly, you should not need to ask a single question.**
