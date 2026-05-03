"""Find available Claude models."""
import os
from dotenv import load_dotenv
load_dotenv()
import anthropic

c = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Try different model names
models = [
    "claude-sonnet-4-5-20241022",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-sonnet-4-20250514",
    "claude-3-7-sonnet-latest",
    "claude-3-7-sonnet-20250219",
]

for m in models:
    try:
        r = c.messages.create(model=m, max_tokens=5, messages=[{"role": "user", "content": "hi"}])
        print(f"  OK: {m} -> {r.content[0].text}")
    except Exception as e:
        err = str(e)
        if "not_found" in err:
            print(f"  404: {m}")
        elif "401" in err:
            print(f"  AUTH: {m}")
        else:
            print(f"  ERR: {m} -> {err[:80]}")
