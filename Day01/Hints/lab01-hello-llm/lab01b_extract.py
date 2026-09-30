"""Lab C - Structured ticket extraction + your first Langfuse trace.

Run:   python Day01\\Labs\\lab01-hello-llm\\lab01b_extract.py
Check: pytest Day01\\Labs\\lab01-hello-llm -k "challenge_4 or challenge_5 or challenge_6"

Complete TODO-4, TODO-5, TODO-6. Everything else is ready.
"""
import json
import sys
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # lets us import askit_core
from askit_core import bedrock, config, data  # noqa: E402
from askit_core.tracing import langfuse, observe  # noqa: E402,F401

HERE = Path(__file__).parent
RESULTS_FILE = HERE / "submission" / "lab01b_results.json"

Category = Literal["Access", "Network", "Hardware", "Software", "Email", "Security", "Other"]
Priority = Literal["Low", "Medium", "High", "Critical"]
Sentiment = Literal["Calm", "Frustrated", "Urgent"]


class Ticket(BaseModel):
    """The fields AskIT extracts from every ticket."""

    # TODO-4: Add these 5 fields (use the types above and Field(description=...)):
    #   category:  Category
    #   priority:  Priority
    #   user_id:   Optional[str], default None, must match pattern r"^EMP-\d{4}$"
    #              -> Field(default=None, pattern=r"^EMP-\d{4}$", description="...")
    #   summary:   str, at most 120 characters  -> Field(max_length=120, description="...")
    #   sentiment: Sentiment
    category: Category = Field(description="Ticket category")
    priority: Priority = Field(description="Business priority per Orbit SLA rules")
    user_id: Optional[str] = Field(default=None, pattern=r"^EMP-\d{4}$", description="Employee ID if present in the text")
    summary: str = Field(max_length=120, description="One-line summary of the problem")
    sentiment: Sentiment = Field(description="How the user feels")


TOOL_NAME = "record_ticket"


def ticket_tool():
    """Tells the model: 'fill in this form' (the Ticket schema). Ready-made."""
    return {
        "toolSpec": {
            "name": TOOL_NAME,
            "description": "Record the structured fields of an IT helpdesk ticket.",
            "inputSchema": {"json": Ticket.model_json_schema()},
        }
    }


SYSTEM = (
    "You are AskIT, the Orbit Corp IT helpdesk triage assistant. "
    "Extract the ticket fields. Priority rules: Critical = security incident or many users down; "
    "High = one user fully blocked or a deadline at risk; Medium = workaround exists; Low = request or question. "
    "Set user_id only if an ID like EMP-1234 appears in the text."
)


def extract_ticket(client, model_id, text, temperature=0.0):
    """Send the ticket text to Bedrock and return a validated Ticket."""
    # TODO-5: Force the model to answer by calling our tool, then validate the result.
    #   response = client.converse(
    #       modelId=model_id,
    #       system=[{"text": SYSTEM}],
    #       messages=[{"role": "user", "content": [{"text": text}]}],
    #       inferenceConfig={"temperature": temperature, "maxTokens": 500},
    #       toolConfig={"tools": [ticket_tool()], "toolChoice": {"tool": {"name": TOOL_NAME}}},
    #   )
    #   Loop over response["output"]["message"]["content"]; the block with a "toolUse" key
    #   holds the answer in block["toolUse"]["input"].
    #   return Ticket.model_validate(that_input)
    response = client.converse(
        modelId=model_id,
        system=[{"text": SYSTEM}],
        messages=[{"role": "user", "content": [{"text": text}]}],
        inferenceConfig={"temperature": temperature, "maxTokens": 500},
        toolConfig={"tools": [ticket_tool()], "toolChoice": {"tool": {"name": TOOL_NAME}}},
    )
    for block in response["output"]["message"]["content"]:
        if "toolUse" in block:
            return Ticket.model_validate(block["toolUse"]["input"])
    raise ValueError("Model did not call the tool")


# TODO-6: Trace every extraction in Langfuse.
#   a) Add this decorator on the line directly above the function below:
#          @observe(as_type="generation", name="extract_ticket")
#   b) Inside the function, after `t = ...`, add:
#          langfuse.update_current_generation(model=model_id, input=text, output=t.model_dump())
@observe(as_type="generation", name="extract_ticket")
def extract_ticket_traced(client, model_id, text):
    t = extract_ticket(client, model_id, text)
    langfuse.update_current_generation(model=model_id, input=text, output=t.model_dump())
    return t


def main():
    config.require_models()
    client = bedrock.client()
    tickets = data.load_tickets()[:5]
    rows = []
    for tk in tickets:
        text = f"Subject: {tk['subject']}\n{tk['description']}"
        t = extract_ticket_traced(client, config.SMALL_MODEL, text)
        match = t.category == tk["category"] and t.priority == tk["priority"]
        print(f"{tk['ticket_id']}  {t.category:9} {t.priority:8} {t.sentiment:10} {'OK ' if match else 'DIFF'}  {t.summary}")
        rows.append({"ticket_id": tk["ticket_id"], "extracted": t.model_dump(),
                     "label": {"category": tk["category"], "priority": tk["priority"]}, "match": match})
    langfuse.flush()
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    RESULTS_FILE.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nSaved {RESULTS_FILE.relative_to(HERE.parents[2])}")
    print("Now open Langfuse -> Tracing -> click your latest 'extract_ticket' trace -> copy the URL")
    print("and paste it into Day01\\Labs\\lab01-hello-llm\\submission\\trace_url.txt")


if __name__ == "__main__":
    main()
