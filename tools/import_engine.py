import sys
import os
import argparse
from pathlib import Path

# Ensure local imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.repository_intelligence.repo_importer import RepoImporter
from core.repository_intelligence.intelligence_engine import IntelligenceEngine
from core.strategy.goal_engine import GoalEngine
from core.kernel.live_kernel import LiveKernel
from core.observability.logger import dgm_logger

def main():
    parser = argparse.ArgumentParser(description="DGM-MAT Import & Intelligence Engine (v1-v7)")
    parser.add_argument("urls", nargs="*", help="Repository URLs to import manually (v1)")
    parser.add_argument("--discover", action="store_true", help="Run ecosystem discovery (v2-v4)")
    parser.add_argument("--goal", type=str, help="Execute a goal-driven plan (v6)")
    parser.add_argument("--kernel", action="store_true", help="Start the Live Execution Kernel (v7)")
    parser.add_argument("--mode", type=str, default="SAFE", choices=["SAFE", "SEMI", "AUTO"], help="Execution mode")
    parser.add_argument("--interval", type=int, default=60, help="Kernel cycle interval in seconds")

    args = parser.parse_args()

    importer = RepoImporter()

    # [v7] Kernel Mode
    if args.kernel:
        kernel = LiveKernel(mode=args.mode, interval=args.interval)
        kernel.start()
        return

    # [v6] Goal Mode
    if args.goal:
        goal_engine = GoalEngine(importer=importer)
        print(f"\n--- GOAL ANALYSIS: {args.goal} ---")
        plan = goal_engine.create_plan(args.goal)
        for step in plan:
            print(f"- {step['action'].upper()}: {step['url']} ({step['reason']})")

        results = goal_engine.execute_plan(plan, mode=args.mode)
        print("\n--- EXECUTION RESULTS ---")
        for res in results:
            print(f"- {res['url']}: {res['status']}")
        return

    # [v2-v4] Discovery Mode
    if args.discover:
        intel = IntelligenceEngine()
        print("\n--- ECOSYSTEM DISCOVERY ---")
        opps = intel.discover_opportunities()
        if not opps:
            print("No new opportunities detected. Ecosystem is balanced.")
        for opp in opps:
            print(f"🔥 OPPORTUNITY: {opp['name']} (Score: {opp['score']}) -> Fills gap: {opp['gap_filled']}")
            print(f"   URL: {opp['url']}")
        return

    # [v1] Manual Import Mode
    urls = args.urls if args.urls else []
    if urls:
        results = []
        dgm_logger.info(f"Starting manual import of {len(urls)} repositories...")
        for url in urls:
            try:
                res = importer.import_repo(url)
                results.append(res)
                print(f"✅ Imported {res['repo_name']} as {res['classification']}")
            except Exception as e:
                dgm_logger.error(f"Failed to import {url}: {e}")
                results.append({"url": url, "status": "error", "message": str(e)})

        print("\n" + "="*30)
        print("IMPORT SUMMARY")
        print("="*30)
        for r in results:
            if r.get("status") == "imported":
                print(f"- {r['repo_name']}: {r['classification']} ({r['path']})")
            else:
                print(f"- ERROR: {r.get('url') or r.get('repo_name')} - {r.get('message')}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
