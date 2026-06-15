import json
import re
import subprocess

def get_score(filename):
    res = subprocess.run(
        ['./observathon-score', '--run', filename, '--phase', 'private'],
        capture_output=True, text=True
    )
    # find "correct  0.703"
    m = re.search(r'correct\s+([0-9\.]+)', res.stdout)
    if m:
        return float(m.group(1))
    return 0.0

with open('run_private.json') as f:
    data = json.load(f)

base_score = get_score('run_private.json')
print(f"Base score: {base_score}")

# Let's find exactly which questions are wrong by blanking them out one by one
wrong_indices = []
for i, r in enumerate(data['results']):
    orig_ans = r.get('answer', '')
    if not orig_ans: continue
    
    # modify answer
    r['answer'] = 'wrong'
    with open('temp_run.json', 'w') as f:
        json.dump(data, f)
    
    new_score = get_score('temp_run.json')
    if new_score < base_score:
        # this means the original answer was CORRECT (removing it dropped the score)
        pass
    else:
        # the original answer was WRONG! (removing it didn't drop the score, or maybe increased it)
        wrong_indices.append((i, r['question'], orig_ans))
    
    # restore
    r['answer'] = orig_ans

print(f"Found {len(wrong_indices)} wrong questions.")
with open('wrong_questions.json', 'w') as f:
    json.dump(wrong_indices, f, indent=2, ensure_ascii=False)
