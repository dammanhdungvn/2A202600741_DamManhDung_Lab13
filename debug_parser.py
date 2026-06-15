import json

def main():
    try:
        with open("run_public.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading run_public.json: {e}")
        return

    phase = data.get("phase", "UNKNOWN")
    print(f"\n\033[1;36m{'='*60}\033[0m")
    print(f"\033[1;32m  🚀 OBSERVATHON RUN REPORT (Phase: {phase}) \033[0m")
    print(f"\033[1;36m{'='*60}\033[0m")

    results = data.get("results", [])
    success = [r for r in results if r.get("status") == "ok"]
    fails = [r for r in results if r.get("status") != "ok"]

    print(f"\033[1;37mTotal Requests:\033[0m {len(results)}")
    print(f"\033[1;32mSUCCESS (OK):  \033[0m {len(success)}")
    print(f"\033[1;31mFAILED (Errors):\033[0m {len(fails)}")

    if fails:
        print(f"\n\033[1;31m{'='*18} FAILED REQUESTS DETAILS {'='*17}\033[0m")
        for i, r in enumerate(fails[:15]):
            print(f"\n\033[1;33m[Q{i+1}]\033[0m {r.get('question')}")
            print(f"\033[1;31m[STATUS]\033[0m {r.get('status')}")
            ans = r.get("answer")
            if ans:
                print(f"\033[1;34m[ANSWER]\033[0m {ans}")
        if len(fails) > 15:
            print(f"\n\033[1;35m...and {len(fails) - 15} more failures not shown.\033[0m")
    else:
        print(f"\n\033[1;32m✨ ALL REQUESTS PASSED SUCCESSFULLY! ✨\033[0m")
    
    print(f"\033[1;36m{'='*60}\033[0m\n")

if __name__ == "__main__":
    main()
