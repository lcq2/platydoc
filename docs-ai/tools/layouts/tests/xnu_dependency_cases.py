# SPDX-License-Identifier: GPL-2.0-only
"""Real-header single-directive interventions, separate from supported profiles."""
import copy

from xnu_cases import load_cases as baseline_cases, validate as validate_baseline, requests_hash


OVERRIDES = {
    'probe-no-cpi': {'CONFIG_PERVASIVE_CPI': '0'},
    'probe-no-energy': {'CONFIG_PERVASIVE_ENERGY': '0'},
    'probe-neither-counter': {'CONFIG_PERVASIVE_CPI': '0', 'CONFIG_PERVASIVE_ENERGY': '0'},
    'probe-secure-metrics': {'CONFIG_SPTM': '1'},
    'probe-defined-one-task-suspend': {'CONFIG_TASK_SUSPEND_STATS': '1'},
}


def load_cases(bundle):
    result = baseline_cases(bundle)
    baseline = next(request for name, request in result if name == 'release-t8103')
    for name, overrides in OVERRIDES.items():
        request = copy.deepcopy(baseline)
        request['macros'].update(overrides)
        result.append((name, request))
    for _, request in result:
        request['trace_dependencies'] = True
    return result


def validate(name, result):
    if name not in OVERRIDES:
        return validate_baseline(name, result)
    assert result['status'] == 'ok' and not result['diagnostics'], (name, result.get('diagnostics'))
    records = {record['name']: record for record in result['records']}
    track, task = records['recount_track'], records['task']
    expected_track = {'probe-no-cpi': 32, 'probe-no-energy': 56, 'probe-neither-counter': 24,
                      'probe-secure-metrics': 88, 'probe-defined-one-task-suspend': 64}[name]
    assert track['size_bytes'] == expected_track and track['alignment_bytes'] == 8, (name, track)
    assert task['size_bytes'] == (2016 if name == 'probe-defined-one-task-suspend' else 1632)
    assert task['alignment_bytes'] == 8
    for macro, value in OVERRIDES[name].items():
        assert result['effective_macros'][macro]['replacement'] == value, (name, macro)
    usage, metrics = records['recount_usage'], records['recount_metrics']
    fields = {field['name']: field for field in usage['fields']}
    assert fields['ru_metrics']['type']['count'] == (3 if name == 'probe-secure-metrics' else 2)
    assert ('ru_energy_nj' in fields) == (name not in {'probe-no-energy', 'probe-neither-counter'})
    cpi = name not in {'probe-no-cpi', 'probe-neither-counter'}
    assert [field['name'] for field in metrics['fields']] == (['rm_time_mach', 'rm_instructions', 'rm_cycles'] if cpi else ['rm_time_mach'])
    if name == 'probe-secure-metrics':
        assert result['effective_macros']['RECOUNT_SECURE_METRICS']['replacement'] == '1'
    if name == 'probe-defined-one-task-suspend':
        task_fields = {field['name']: field for field in task['fields']}
        assert task_fields['t_suspend_stats']['offset_bits'] == 132 * 8
        assert task_fields['user_stop_count']['offset_bits'] == 516 * 8
    return {'kind': 'what-if-source-layout-only', 'recount_size_bytes': expected_track,
            'task_size_bytes': task['size_bytes'], 'requested_intervention': OVERRIDES[name],
            'note': 'Controlled preprocessor intervention; not a generated product configuration.'}
