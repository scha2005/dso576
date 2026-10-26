"""Reproduce the Module 9 backend audit. No network or source writes.
Run: python audit_check.py /path/to/dso576
Requires pandas and numpy from the course environment.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
source = root / 'project/backend_analysis.py'
spec = importlib.util.spec_from_file_location('audited_backend', source)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
import pandas as pd

# Synthetic occupations, deliberately simple and unrelated to real labor data.
rows = [
    ('11-1001', 'Alpha', .1, 100, -2, 10),
    ('11-1002', 'Beta', .2, 200, 0, 20),
    ('11-1003', 'Gamma', .3, 300, 2, 30),
    ('11-1004', 'Delta', .4, 400, 4, 40),
]
df = pd.DataFrame(rows, columns=['soc_code','occupation_title','observed_exposure',
    'employment_base_year','employment_growth_pct','annual_openings'])
df['major_group_code'] = '11'
df['major_group_title'] = 'Synthetic group'
df['dominant_mode'] = 'balanced'

# Independent average-rank percentile, using only Python comparisons.
# Rank = number strictly below + (number tied + 1)/2; divide by N.
def independent_scores(records):
    weights = [('observed_exposure', .45), ('employment_base_year', .25),
               ('employment_growth_pct', .15), ('annual_openings', .15)]
    complete = [r for r in records if all(pd.notna(r[c]) for c, _ in weights)]
    answer = {}
    for r in complete:
        total = 0
        for col, weight in weights:
            below = sum(s[col] < r[col] for s in complete)
            tied = sum(s[col] == r[col] for s in complete)
            total += 100 * weight * (below + (tied + 1)/2) / len(complete)
        answer[r['soc_code']] = total
    return answer

checks = []
def check(label, condition):
    assert condition, label
    checks.append(label)

scored = b.add_priority_score(df)
expected = independent_scores(df.to_dict('records'))
check('four-row independent score agreement', all(abs(r.priority_score-expected[r.soc_code]) < 1e-9 for r in scored.itertuples()))
check('hand scores 25,50,75,100', scored.priority_score.tolist() == [25.,50.,75.,100.])
check('Alpha contributions 11.25,6.25,3.75,3.75', [scored.iloc[0][x+'_contribution'] for x in ['exposure','employment','growth','openings']] == [11.25,6.25,3.75,3.75])
ranked = b.rank_occupations(df, top_n=None)
check('descending order Delta,Gamma,Beta,Alpha', ranked.occupation_title.tolist() == ['Delta','Gamma','Beta','Alpha'])
check('top_n=2 returns Delta,Gamma', b.rank_occupations(df, top_n=2).occupation_title.tolist() == ['Delta','Gamma'])
filtered = b.filter_occupations(df, min_employment=200)
filtered_scores = b.add_priority_score(filtered)
check('filter recomputes Beta from 50 to 100/3', abs(filtered_scores.iloc[0].priority_score-100/3) < 1e-9)
single = b.add_priority_score(b.filter_occupations(df, search='Alpha'))
check('single search result Alpha scores 100', single.iloc[0].priority_score == 100)
missing = df.copy()
missing.loc[3, 'annual_openings'] = float('nan')
m = b.rank_occupations(missing, top_n=None, include_incomplete=True)
last = m[m.soc_code == '11-1004'].iloc[0]
check('missing input yields unavailable score and rank', not last.priority_score_available and pd.isna(last.priority_score) and pd.isna(last['rank']))
check('incomplete row excluded from percentile denominator', abs(m[m.soc_code == '11-1001'].iloc[0].priority_score-100/3) < 1e-9)
ties = df.copy()
ties.loc[1, ['observed_exposure','employment_base_year','employment_growth_pct','annual_openings']] = [.1,100,-2,10]
t = b.rank_occupations(ties, top_n=None)
check('average-rank tie score 37.5 and tied rank 3', t[t.soc_code.isin(['11-1001','11-1002'])].priority_score.tolist() == [37.5,37.5] and t[t.soc_code.isin(['11-1001','11-1002'])]['rank'].tolist() == [3,3])
check('title tie breaker Alpha before Beta', t.occupation_title.tolist()[-2:] == ['Alpha','Beta'])
try:
    b.filter_occupations(df, exposure_range=(.8,.2))
except ValueError:
    check('reversed exposure range rejected', True)
else:
    check('reversed exposure range rejected', False)

# Reproduce the documented default entry point from repository root.
run = subprocess.run([sys.executable, str(source)], cwd=root, text=True, capture_output=True)
real = b.build_dashboard_outputs(root/'project/data/processed/occupation_dashboard.csv', root/'project/data/processed/occupation_tasks.csv')
real_expected = independent_scores(real['eligible_occupations'].to_dict('records'))
error = max(abs(r.priority_score-real_expected[r.soc_code]) for r in real['ranking'].itertuples())
check('real-data independent score agreement', error < 1e-9)
check('real-data top25 separate from full ranking', len(real['ranking_visual']) == 25 and len(real['ranking']) > 25)
print(json.dumps({
    'real_data': {'eligible_rows': len(real['eligible_occupations']), 'ranking_rows': len(real['ranking']), 'visual_rows': len(real['ranking_visual']), 'max_absolute_score_error': error, 'top5': real['ranking'][['soc_code','occupation_title','priority_score']].head(5).to_dict('records'), 'summary': real['summary']},
    'commit': subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'], text=True).strip(),
    'backend_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'pandas_version': pd.__version__,
    'checks_passed': checks,
    'fixture_scores': expected,
    'filtered_Beta_score': float(filtered_scores.iloc[0].priority_score),
    'search_Alpha_score': float(single.iloc[0].priority_score),
    'default_entry_point_returncode': run.returncode,
    'default_entry_point_last_error': run.stderr.strip().splitlines()[-1] if run.stderr else None,
    'processed_occupation_file_exists': (root/'project/data/processed/occupation_dashboard.csv').exists(),
    'processed_task_file_exists': (root/'project/data/processed/occupation_tasks.csv').exists(),
    'pipeline_src_exists': (root/'src').exists(),
}, indent=2))
