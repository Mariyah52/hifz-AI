from slowapi import Limiter
from slowapi.util import get_remote_address

"""
In-memory rate limiting (slowapi's default storage) — fine for a single
server, same caveat as the scheduler in app/scheduler.py: running more
than one instance of this app would enforce the limit per-instance, not
globally. A real horizontally-scaled deployment would point slowapi at a
shared Redis backend instead (slowapi supports this directly; swapping
the storage_uri is the only change needed, not a redesign).
"""
limiter = Limiter(key_func=get_remote_address)
