# My notes

Q1. D1: no, D2: on-call, D3: 30 days. I would tell the client that VIP read access should stay low-friction, night writes need a real person now, and 30 days is a practical retention window.

Q2. I would never let an LLM decide the memory-safety rule on its own. It must be deterministic because it protects secrets and personal data.

Q3. I edited the spec first, then the code. That order matters because the spec is the source of truth and the code must follow it exactly.
