import os
import subprocess
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "10"))

def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

def run_once():
    print(f"[{_now()}] [scheduler] Launching runner.py")
    completed = subprocess.run(["python", "-m", "batch_runner.runner"])
    print(f"[{_now()}] [scheduler] runner.py exited with {completed.returncode}")

def main():
    print(f"[{_now()}] [scheduler] Starting. Every {INTERVAL_MINUTES} minute(s). Ctrl+C to stop.")
    scheduler = BlockingScheduler(
        timezone="UTC",
        job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 3600},
    )
    # schedule next run explicitly 10 minutes from now
    next_run = datetime.now(timezone.utc) + timedelta(minutes=INTERVAL_MINUTES)
    scheduler.add_job(run_once, "interval", minutes=INTERVAL_MINUTES, next_run_time=next_run, id="batch_job")
    try:
        run_once()  # immediate run
        print(f"[{_now()}] [scheduler] Next scheduled run at: {next_run.isoformat()}")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print(f"[{_now()}] [scheduler] Stopped.")

if __name__ == "__main__":
    main()
