# jhu_software_concepts
Sources used: Chatgpt, https://realpython.com/flask-project/
Tools:
    -Moduar Functions
    -Docstrings on all major sections
    -Structured parsing (dt/dd → dictionary)
    -JSON output for downstream analysis
    -Rate limiting (time.sleep)
    -Error tolerance
@'
{"rows":[
  {"program":"Information Studies, McG"},
  {"program":"Mathematics, University Of British Columbia"},
  {"program":"Computer Science, uoft"}
]}
'@ | Out-File -Encoding utf8 sample_input.json

# Module 2 – LLM Hosting

This project hosts a tiny local LLM using Flask and llama.cpp to standardize
program and university names.

## Run server
```bash
python -m flask --app app run

python app.py --file sample_data.json --out sample_output.jsonl
