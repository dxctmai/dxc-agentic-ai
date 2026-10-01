"""Day End: save XP + lab results into progress/, then commit and push to your fork.

Used two ways:
  1. By the portal's "Day End" button (tools/portal.py calls run_day_end()).
  2. Directly: DAY_END.bat  ->  python tools/day_end.py [S01]
"""
import json
import os
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "progress"
GIT_LOCK = threading.Lock()  # portal heartbeat and Day End never run git at the same time
SESSIONS = json.loads((ROOT / "tools" / "sessions.json").read_text(encoding="utf-8"))


def load_me():
    f = ROOT / "me.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def today_session():
    """Session picked by START_DAY.bat <number> (env ASKIT_DAY). No date check.
    Without a number: the last session whose page exists."""
    n = os.environ.get("ASKIT_DAY", "").strip()
    if n.isdigit():
        key = f"S{int(n):02d}"
        if key in SESSIONS:
            return key
    have = [k for k, v in SESSIONS.items() if (ROOT / v["html"]).exists()]
    return have[-1] if have else "S01"


def run(cmd, timeout=180):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def lab_results(session):
    """Run pytest for the session's labs; return {lab: {passed, failed, total}}."""
    out = {}
    for lab in SESSIONS[session]["labs"]:
        lab_dir = ROOT / SESSIONS[session]["labs_dir"] / lab
        if not (lab_dir / "tests").exists():
            out[lab] = {"passed": [], "failed": [], "total": 0, "note": "no tests yet"}
            continue
        xml = PROGRESS / f".tmp_{lab}.xml"
        run([sys.executable, "-m", "pytest", str(lab_dir), "-q", f"--junitxml={xml}"], timeout=600)
        passed, failed = [], []
        if xml.exists():
            for tc in ET.parse(xml).getroot().iter("testcase"):
                bad = tc.find("failure") is not None or tc.find("error") is not None
                skip = tc.find("skipped") is not None
                if skip:
                    continue
                (failed if bad else passed).append(tc.get("name"))
            xml.unlink()
        out[lab] = {"passed": passed, "failed": failed, "total": len(passed) + len(failed)}
    return out


def find_downloaded_xp(session):
    """Fallback: XP file the browser downloaded (page not opened via START_DAY.bat)."""
    dl = Path.home() / "Downloads"
    files = sorted(dl.glob(f"askit_{session}_xp*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return json.loads(files[0].read_text(encoding="utf-8")) if files else None


def run_day_end(session=None, xp_payload=None):
    steps = []
    me = load_me()
    if not me:
        return False, [{"ok": False, "step": "Identity missing", "detail": "run SETUP.bat first (creates me.json)"}]
    session = session or today_session()
    if session not in SESSIONS:
        return False, [{"ok": False, "step": "Unknown session", "detail": session}]
    PROGRESS.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    # 1. XP
    xp = xp_payload or find_downloaded_xp(session)
    xp_file = PROGRESS / f"{session}_xp.json"
    if xp:
        xp["participant"] = me
        xp["saved_at"] = now
        xp_file.write_text(json.dumps(xp, indent=2), encoding="utf-8")
        steps.append({"ok": True, "step": "XP saved", "detail": f"{xp.get('xp_total', 0)} XP -> progress/{xp_file.name}"})
    elif xp_file.exists():
        steps.append({"ok": True, "step": "XP kept", "detail": "using earlier saved file"})
    else:
        steps.append({"ok": False, "step": "No XP found", "detail": "click Day End in the session page"})

    # 2. Labs
    labs = lab_results(session)
    lab_file = PROGRESS / f"{session}_lab.json"
    lab_file.write_text(json.dumps({"session": session, "participant": me, "saved_at": now, "labs": labs}, indent=2), encoding="utf-8")
    p = sum(len(v["passed"]) for v in labs.values())
    t = sum(v["total"] for v in labs.values())
    steps.append({"ok": True, "step": "Labs checked", "detail": f"{p}/{t} challenges passing"})

    # 3. Git commit + push
    with GIT_LOCK:
        return _commit_and_push(session, me, steps)


def _commit_and_push(session, me, steps):
    lab_roots = sorted({v["labs_dir"] for v in SESSIONS.values() if v.get("labs_dir") and (ROOT / v["labs_dir"]).exists()})
    run(["git", "add", "progress", "teams", "me.json", *lab_roots])
    code, _ = run(["git", "diff", "--cached", "--quiet"])
    if code != 0:
        code, msg = run(["git", "commit", "-m", f"{session} day end - {me.get('name', '')}"])
        if code != 0:
            steps.append({"ok": False, "step": "Commit failed", "detail": msg[-200:]})
            return False, steps
        steps.append({"ok": True, "step": "Committed"})
    else:
        steps.append({"ok": True, "step": "Nothing new to commit"})
    code, msg = run(["git", "push", "origin", "HEAD"])
    if code != 0:
        steps.append({"ok": False, "step": "Push failed", "detail": msg[-200:] + " - call the trainer"})
        return False, steps
    steps.append({"ok": True, "step": "Pushed to your GitHub fork"})
    return True, steps


def push_heartbeat(session):
    """Commit + push only progress/<session>_live.json. Silent on failure (retried next cycle)."""
    f = f"progress/{session}_live.json"
    if not (ROOT / f).exists() or not GIT_LOCK.acquire(timeout=5):
        return False
    try:
        run(["git", "add", f])
        code, _ = run(["git", "diff", "--cached", "--quiet", "--", f])
        if code == 0:
            return True  # nothing changed
        run(["git", "commit", "-q", "-m", f"{session} heartbeat", "--", f])
        code, _ = run(["git", "push", "-q", "origin", "HEAD"], timeout=60)
        return code == 0
    finally:
        GIT_LOCK.release()

if __name__ == "__main__":
    ok, steps = run_day_end(sys.argv[1] if len(sys.argv) > 1 else None)
    for s in steps:
        print(("[OK]  " if s["ok"] else "[!!]  ") + s["step"] + (" - " + s["detail"] if s.get("detail") else ""))
    print("\nDAY END COMPLETE" if ok else "\nDAY END NOT COMPLETE - call the trainer")
    sys.exit(0 if ok else 1)
