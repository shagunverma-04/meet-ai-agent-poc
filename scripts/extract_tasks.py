# Uses OpenAI API to extract action items from a transcript file.
# Requires OPENAI_API_KEY env var.
import argparse, os, json, time, sys
import openai

PROMPT_TEMPLATE = '''You are an assistant that extracts action items from meeting transcript segments.
Output a JSON array where each item has:
- text: concise task description
- assignee: name or email if mentioned, else null
- role: suggested role (Product Manager, Backend Engineer, Designer, QA, etc.) or null
- deadline: ISO date if mentioned or null
- priority: High/Medium/Low or null
- confidence: 0..1

Meeting date: {meeting_date}

Example:
Transcript segment: "Sanya, can you make the onboarding mockups by next Monday?"
Output:
[{{
  "text":"Create onboarding mockups",
  "assignee":"Sanya",
  "role":"Product Designer",
  "deadline":"2025-12-08",
  "priority":"High",
  "confidence":0.95
}}]

Now extract action items from the following transcript segments (JSON array of {{speaker,start,end,text}}):
{{segments}}
'''


def call_openai(prompt, model="gpt-4o-mini"):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=800
    )
    return resp['choices'][0]['message']['content']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('transcript', help='transcript.json (merged or plain)')
    parser.add_argument('--meeting_date', default=None)
    args = parser.parse_args()
    with open(args.transcript) as f:
        segments = json.load(f)
    prompt = PROMPT_TEMPLATE.format(meeting_date=args.meeting_date or "2025-12-01", segments=json.dumps(segments, indent=2))
    try:
        out = call_openai(prompt)
        # Try to parse JSON from the response:
        import re, ast
        m = re.search(r'\[.*\]', out, re.S)
        if m:
            arr_text = m.group(0)
        else:
            arr_text = out
        tasks = json.loads(arr_text)
    except Exception as e:
        print("OpenAI call failed or parsing failed:", e)
        print("Falling back to heuristic extraction.")
        tasks = []
        # Very simple heuristic: sentences containing 'need' or 'will' or 'assign' etc.
        for s in segments:
            txt = s.get('text','').lower()
            if any(k in txt for k in ['need','please','can you','will','assign','let's']):
                tasks.append({
                    "text": s['text'],
                    "assignee": None,
                    "role": None,
                    "deadline": None,
                    "priority": None,
                    "confidence": 0.5,
                    "source_segment": s
                })
    with open('tasks.json','w') as f:
        json.dump(tasks, f, indent=2)
    print("Wrote tasks.json with", len(tasks), "items")
