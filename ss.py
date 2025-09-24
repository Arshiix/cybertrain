import json
import csv

# Input JSON file containing tools data
INPUT_FILE = "tools.json"
OUTPUT_FILE = "tools_dataset.csv"

# Define the CSV header
HEADER = [
    "name",
    "description",
    "when_why",
    "notes",
    "how",
    "flags",
    "examples",
    "tips",
    "advanced_tips",
    "advanced_extra"
]

def flatten_flags(flags):
    if not flags:
        return ""
    return " | ".join([f"{f['flag']} => {f['explanation']}" for f in flags])

def flatten_examples(examples):
    if not examples:
        return ""
    return " | ".join([f"{e['command']} => {e['explanation']}" for e in examples])

def flatten_dict(d):
    if not d:
        return ""
    return " | ".join([f"{k}: {v}" for k, v in d.items()])

def flatten_list(lst):
    if not lst:
        return ""
    return " | ".join(lst)

# Load JSON data
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Ensure data is a list (even if single entry)
if isinstance(data, dict):
    data = [data]

# Write CSV
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=HEADER)
    writer.writeheader()

    for tool in data:
        writer.writerow({
            "name": tool.get("name", ""),
            "description": tool.get("description", ""),
            "when_why": tool.get("when_why", ""),
            "notes": tool.get("notes", ""),
            "how": tool.get("how", ""),
            "flags": flatten_flags(tool.get("flags", [])),
            "examples": flatten_examples(tool.get("examples", [])),
            "tips": flatten_dict(tool.get("tips", {})),
            "advanced_tips": flatten_list(tool.get("advanced", {}).get("advanced_tips", [])),
            "advanced_extra": flatten_list(tool.get("advanced", {}).get("tips", [])),
        })

print(f"✅ Conversion complete! Data saved to {OUTPUT_FILE}")