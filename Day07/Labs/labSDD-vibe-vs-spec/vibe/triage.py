def triage(ticket):
    title = str(ticket.get("title", ""))
    description = str(ticket.get("description", ""))
    affected_users = ticket.get("affected_users", 1)

    text = f"{title} {description}".lower()

    if affected_users >= 50 or "outage" in text or "down" in text:
        priority = "P1"
        queue = "Network"
        sla_hours = 4
    elif affected_users >= 10 or "urgent" in text or "blocked" in text:
        priority = "P2"
        queue = "General"
        sla_hours = 8
    elif affected_users >= 2:
        priority = "P3"
        queue = "General"
        sla_hours = 24
    else:
        priority = "P4"
        queue = "General"
        sla_hours = 72

    return {"priority": priority, "queue": queue, "sla_hours": sla_hours}