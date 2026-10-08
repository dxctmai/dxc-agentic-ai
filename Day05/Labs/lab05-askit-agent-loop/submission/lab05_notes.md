# Lab 5 notes

Name: Thanh Mai

## Lab 5A: one tool call
Question I asked: How do I fix VPN error 809?
Tool I guessed the model would ask for: search_kb
Tool the model really asked for: search_kb  with inputs  {"query": "vpn error 809"}
One question where the model asked for NO tool: How old are you?

## Lab 5B: the loop
Question I asked: What is the status of TKT-9999?
How many steps did the agent take, and which tools did it use? 2 steps, tool get_ticket and result_block
What happened when I set MAX_STEPS = 2 (then I set it back to 6): 2 steps

## Lab 5C: approval and cost
Which tools asked for my approval? get_user({"user_id": "EMP-1021"}), reset_password({"user_id": "EMP-1021"})
Tokens used for one question (printed at the end of run_agent.py): 1682
Estimated cost of one question in USD: $0.00008

## Incident: the agent stuck in a loop
How many steps did the agent take before I changed anything? 6
Why did it keep repeating the same call? (one sentence) STOP_ON_REPEAT is False
How many steps did it take after I changed STOP_ON_REPEAT to True? 2
