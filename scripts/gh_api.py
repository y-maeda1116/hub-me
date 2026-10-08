"""Shared `gh api` helper for the profile scripts."""
import subprocess
import sys
import time

OWNER = "y-maeda1116"

RETRY_MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 60


def run_gh_api(args: list[str]):
    """Run `gh api`, retrying transient failures with linear backoff.

    GitHub's secondary rate limit answers HTTP 403 with "wait a few
    minutes" even when the primary quota is fine, so a burst of API
    calls from another step can fail these requests. Retrying keeps a
    transient 403 from failing the whole daily run.

    HTTP 404 is returned immediately: it is an expected answer (e.g.
    `releases/latest` for a repo without releases), not a transient error.
    """
    result = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        result = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
        if (result.returncode == 0
                or attempt == RETRY_MAX_ATTEMPTS
                or "HTTP 404" in (result.stderr or "")):
            return result
        delay = RETRY_DELAY_SECONDS * attempt
        print(
            f"warning: gh api {args[0][:80]} failed (rc={result.returncode}); "
            f"retrying in {delay}s: {(result.stderr or '').strip()[:200]}",
            file=sys.stderr,
        )
        time.sleep(delay)
    return result
