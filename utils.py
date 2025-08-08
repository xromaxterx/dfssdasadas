# small helpers (placeholder)
def safe_truncate(s, n=200):
    if not s:
        return s
    return s if len(s) <= n else s[:n-1] + "…"
