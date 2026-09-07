"""Process-wide throttle so eval calls stay under a model's RPM limit instead
of bursting and eating 429-retry backoff, which is what made the first two
gemini-3.6-flash runs crawl. Shared between ablation.py's generate() calls
(now Ollama Cloud) and judge.py's judge calls (Gemini) - two different
providers with their own separate limits since the generation backend
migrated off Gemini, not one shared RPM budget the way this was originally
written for. One conservative interval for both is still a reasonable
simplification in practice: Ollama generation latency alone typically
exceeds the throttle interval, so this mostly ends up pacing the faster
Gemini judge calls anyway. Would need a second, separately configured
throttle to actually rate-limit each provider on its own real limit.
"""
import threading
import time

_lock = threading.Lock()
_last_call_ts = 0.0
_min_interval = 4.5  # ~13 RPM, a small margin under a 15 RPM limit


def configure(rpm: int):
    global _min_interval
    _min_interval = 60.0 / rpm * 1.1  # 10% margin


def throttle():
    global _last_call_ts
    with _lock:
        now = time.monotonic()
        wait = _min_interval - (now - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.monotonic()
