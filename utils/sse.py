def sse_message(data: str, event: str = None) -> str:
    """Format a Server-Sent Event message."""
    lines = []
    if event:
        lines.append(f"event: {event}")
    for line in data.splitlines():
        lines.append(f"data: {line}")
    lines.append("")
    return "\n".join(lines)
