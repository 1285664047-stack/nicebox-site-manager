AI Website Generator

This skill helps users generate websites through AI-guided dialogue.

Base URL:

`http://aidev.nicebox.cn/api/openclaw`

Authentication:

Authorization: $AIBOX_API_KEY
Available Tools
1. guide_dialogue

Start or continue guided dialogue to collect website requirements.

python3 {baseDir}/scripts/guide_dialogue.py \
  --message "I want a lawyer website" \
  --session-id ""

Options:

--message: User input message (optional for first call)
--session-id: Session ID from previous step (empty for first call)
2. guide_collect

Summarize collected website requirements.

python3 {baseDir}/scripts/guide_collect.py \
  --session-id "xxx"
3. generate_website

Generate website based on collected requirements.

python3 {baseDir}/scripts/generate_website.py \
  --session-id "xxx"
Workflow (VERY IMPORTANT)

When user wants to create a website:

ALWAYS start with guide_dialogue
Continue calling guide_dialogue until is_complete = true
When complete:
Call guide_collect
Show summary to user
Then automatically call generate_website
Inform user that website is being generated
Rules
Always keep and reuse session_id
Never skip guide_dialogue unless user provides full structured info
Never call generate_website before guide_collect
Do not invent website data — always rely on collected info
Notes
All APIs use Authorization header
API Key must be set via:
export AIBOX_API_KEY="your_api_key"
