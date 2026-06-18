from modules.profiler import profile_data
from modules.findings import generate_findings
from modules.chart_selector import enrich_findings
from modules.script_gen import generate_script

profile = profile_data('../sample_data.csv')
findings = generate_findings(profile)
findings = enrich_findings(findings, profile)
script = generate_script(findings)

print('=== FINDINGS ===')
for f in findings:
    print(f'  [{f["type"].upper():<10}] {f["chart_type"]:<12} | {f["text"][:80]}...')

total_words = sum(s["word_count"] for s in script)
total_dur = sum(s["estimated_duration_seconds"] for s in script)
print(f'\n=== SCRIPT ({len(script)} segments) ===')
print(f'  Total words: {total_words}, Estimated duration: {total_dur:.1f}s')
print('ALL OK')
