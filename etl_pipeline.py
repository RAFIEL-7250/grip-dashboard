"""
GRIP Performance ETL Pipeline
Extract from Excel → Clean → Pre-compute multi-dimensional aggregates → Cache to JSON
"""

import openpyxl
import json
from collections import defaultdict
import os

EXCEL_PATH = "/Users/xuli/Documents/Category Project/2026-B27 Budget Framing/2026 GRIP/04. GRIP Performance/20260601_GRIP_Financial reporting_vLIVE1.xlsx"
CACHE_DIR = os.path.dirname(__file__)


def extract_rp_data(filepath):
    """Extract all Retail & Promotion rows from Raw data_MySourcing"""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb['Raw data_MySourcing']
    
    rows = []
    for i, row in enumerate(ws.iter_rows(min_row=6, values_only=True)):
        vals = [str(c) if c is not None else '' for c in row]
        domain = vals[10].strip() if len(vals) > 10 else ''
        if 'Retail' not in domain:
            continue
        
        period = vals[0].strip()
        zone = vals[2].strip()
        country = vals[5].strip()
        master_project = vals[7].strip()
        project = vals[8].strip()
        status = vals[9].strip()
        wg = vals[11].strip()
        buyer = vals[12].strip()
        perf_type = vals[13].strip()
        division = vals[14].strip()
        
        amount_eur = 0.0
        try:
            if vals[15].strip():
                amount_eur = float(vals[15])
        except:
            pass
        
        latest_eur = 0.0
        try:
            if vals[16].strip():
                latest_eur = float(vals[16])
        except:
            pass
        
        rows.append({
            'period': period, 'zone': zone, 'country': country,
            'master_project': master_project, 'project': project,
            'status': status, 'wg': wg, 'buyer': buyer,
            'perf_type': perf_type, 'division': division,
            'amount_eur': amount_eur, 'latest_eur': latest_eur
        })
    
    wb.close()
    return rows


def pivot(data, group_keys, min_value=0.01):
    """Generic pivot: group by keys, compute T3/T5/delta"""
    result = defaultdict(lambda: {'T3': 0, 'T5': 0, 'latest': 0})
    for r in data:
        key = tuple(r[k] for k in group_keys)
        if r['period'] == 'T3':
            result[key]['T3'] += r['amount_eur']
        elif r['period'] == 'T5':
            result[key]['T5'] += r['amount_eur']
        result[key]['latest'] = max(result[key]['latest'], r['latest_eur'])
    
    output = []
    for key, vals in result.items():
        if vals['T3'] < min_value and vals['T5'] < min_value:
            continue
        row = {group_keys[i]: key[i] for i in range(len(group_keys))}
        row['T3'] = round(vals['T3'], 2)
        row['T5'] = round(vals['T5'], 2)
        row['delta'] = round(vals['T5'] - vals['T3'], 2)
        row['delta_pct'] = round(
            (row['delta'] / vals['T3'] * 100) if vals['T3'] > 0.01 else (999 if vals['T5'] > 0.01 else 0), 1
        )
        row['latest'] = round(vals['latest'], 2)
        output.append(row)
    return output


def build_all_views(rp_data):
    """Pre-compute all dimensional views"""
    
    raw_t3 = round(sum(r['amount_eur'] for r in rp_data if r['period'] == 'T3'), 2)
    raw_t5 = round(sum(r['amount_eur'] for r in rp_data if r['period'] == 'T5'), 2)
    
    # Core KPI
    summary = {
        'budget': 68570,  # from Dashboard overview_Total
        't3': 68741,
        't5': 65716,
        'latest': 65388,
        'delta_vs_budget': -2854,
        'raw_t3': raw_t3,
        'raw_t5': raw_t5,
        'raw_delta': round(raw_t5 - raw_t3, 2)
    }
    
    # Project-level (detailed, for waterfall & ranking)
    proj_data = defaultdict(lambda: {'T3': 0, 'T5': 0, 'latest': 0})
    for r in rp_data:
        key = (r['project'], r['master_project'], r['zone'], r['division'], 
               r['wg'], r['perf_type'], r['buyer'], r['status'], r['country'])
        if r['period'] == 'T3':
            proj_data[key]['T3'] += r['amount_eur']
        elif r['period'] == 'T5':
            proj_data[key]['T5'] += r['amount_eur']
        proj_data[key]['latest'] = max(proj_data[key]['latest'], r['latest_eur'])
    
    projects = []
    for (proj, mp, zone, div, wg, pt, buyer, status, country), vals in proj_data.items():
        if vals['T3'] < 0.01 and vals['T5'] < 0.01:
            continue
        projects.append({
            'project': proj, 'master_project': mp, 'zone': zone,
            'division': div, 'wg': wg, 'perf_type': pt,
            'buyer': buyer, 'status': status, 'country': country,
            'T3': round(vals['T3'], 2), 'T5': round(vals['T5'], 2),
            'delta': round(vals['T5'] - vals['T3'], 2),
            'delta_pct': round((vals['T5']-vals['T3'])/vals['T3']*100, 1) if vals['T3'] > 0.01 else (999 if vals['T5'] > 0.01 else 0),
            'latest': round(vals['latest'], 2)
        })
    
    projects.sort(key=lambda x: x['delta'])
    
    # Waterfall analysis
    removed_val = round(sum(p['T3'] for p in projects if p['T3'] > 0 and p['T5'] < 0.01), 2)
    added_val = round(sum(p['T5'] for p in projects if p['T3'] < 0.01 and p['T5'] > 0), 2)
    reduced_val = round(sum(p['delta'] for p in projects if p['delta'] < -0.01 and p['T3'] > 0.01 and p['T5'] > 0.01), 2)
    increased_val = round(sum(p['delta'] for p in projects if p['delta'] > 0.01 and p['T3'] > 0.01 and p['T5'] > 0.01), 2)
    
    num_removed = sum(1 for p in projects if p['T3'] > 0 and p['T5'] < 0.01)
    num_added = sum(1 for p in projects if p['T3'] < 0.01 and p['T5'] > 0)
    num_reduced = sum(1 for p in projects if p['delta'] < -0.01 and p['T3'] > 0.01 and p['T5'] > 0.01)
    num_increased = sum(1 for p in projects if p['delta'] > 0.01 and p['T3'] > 0.01 and p['T5'] > 0.01)
    num_unchanged = sum(1 for p in projects if abs(p['delta']) < 0.01 and p['T3'] > 0.01 and p['T5'] > 0.01)
    
    waterfall = {
        't3_total': raw_t3,
        'removed': {'count': num_removed, 'value': removed_val},
        'added': {'count': num_added, 'value': added_val},
        'reduced': {'count': num_reduced, 'value': reduced_val},
        'increased': {'count': num_increased, 'value': increased_val},
        'unchanged': {'count': num_unchanged},
        'net_change': round(-removed_val + added_val + reduced_val + increased_val, 2)
    }
    
    # Pivot views
    return {
        'summary': summary,
        'waterfall': waterfall,
        'by_zone_perf_type': pivot(rp_data, ['zone', 'perf_type']),
        'by_zone_wg': pivot(rp_data, ['zone', 'wg']),
        'by_division_wg': pivot(rp_data, ['division', 'wg']),
        'by_zone_country': pivot(rp_data, ['zone', 'country']),
        'by_wg': pivot(rp_data, ['wg']),
        'by_division': pivot(rp_data, ['division']),
        'by_status': pivot(rp_data, ['status', 'perf_type']),
        'projects': projects,
        'top_declines': [p for p in projects if p['delta'] < -0.01][:30],
        'top_increases': sorted([p for p in projects if p['delta'] > 0.01], 
                                key=lambda x: x['delta'], reverse=True)[:20],
        # Quick lookup lists for UI filters
        'filters': {
            'zones': sorted(set(r['zone'] for r in rp_data if r['zone'])),
            'divisions': sorted(set(r['division'] for r in rp_data if r['division'])),
            'wgs': sorted(set(r['wg'] for r in rp_data if r['wg'])),
            'perf_types': sorted(set(r['perf_type'] for r in rp_data if r['perf_type'])),
            'statuses': sorted(set(r['status'] for r in rp_data if r['status'])),
        }
    }


def main():
    print("🔧 Extracting Retail & Promotion data from Excel...")
    rp_data = extract_rp_data(EXCEL_PATH)
    print(f"   Extracted {len(rp_data)} rows")
    
    print("📊 Building multi-dimensional views...")
    views = build_all_views(rp_data)
    
    cache_path = os.path.join(CACHE_DIR, 'data_cache.json')
    with open(cache_path, 'w') as f:
        json.dump(views, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cache written to {cache_path}")
    print(f"   Summary: Budget={views['summary']['budget']} → T3={views['summary']['raw_t3']} → T5={views['summary']['raw_t5']}")
    print(f"   Waterfall: Removed={views['waterfall']['removed']['count']} Added={views['waterfall']['added']['count']} Reduced={views['waterfall']['reduced']['count']} Increased={views['waterfall']['increased']['count']}")
    print(f"   Projects: {len(views['projects'])} | Top declines: {len(views['top_declines'])}")


if __name__ == '__main__':
    main()
