#!/usr/bin/env python3
"""Run frozen Photius gates against their strictly checked predecessor view."""
from __future__ import annotations

import argparse
import importlib
import json

from photius_current_state import ROOT, predecessor_view

STAGES = {
    'apparatus': ('repair_photius_apparatus','check'),
    'readings': ('repair_photius_readings','check'),
    'historical-readings': ('repair_photius_historical_readings','check'),
    'historical-batches': ('repair_photius_historical_batches','check'),
    'complete-review': ('repair_photius_complete_review','check'),
    'context': ('repair_photius_context','check'),
    'uncertainties': ('check_photius_uncertainties','check'),
    'uncertainty-pilot': ('check_photius_pilot_predecessor','check'),
    'uncertainty-admission': ('repair_photius_uncertainty_admission','check'),
    'editorial-substitutions': ('repair_photius_editorial_substitutions','check_literal'),
    'editorial-source': ('repair_photius_editorial_substitutions','check'),
}


def check(stage, root=ROOT, *, source_html=None):
    with predecessor_view(root) as previous:
        if stage == 'apparatus-audit':
            module = importlib.import_module('audit_photius_apparatus')
            result = module.build(previous)
            if (previous/module.REPORT).read_bytes() != module.encode(result):
                raise ValueError('Historical Photius apparatus audit drift')
            return result
        if stage == 'review-observations':
            module = importlib.import_module('build_photius_review_observations')
            outputs,result = module.build(previous)
            if any((previous/path).read_bytes() != raw for path,raw in outputs.items()):
                raise ValueError('Frozen Photius observations no longer reproduce')
            return result
        module_name, function = STAGES[stage]
        module = importlib.import_module(module_name)
        kwargs = {'source_html':source_html} if stage == 'editorial-source' else {}
        return getattr(module,function)(previous,**kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',required=True,choices=(*STAGES,'apparatus-audit','review-observations'))
    parser.add_argument('--source-html')
    args = parser.parse_args()
    result = check(args.stage,source_html=args.source_html)
    print(json.dumps(result.get('counts',result) if isinstance(result,dict) else result,ensure_ascii=False))


if __name__ == '__main__':
    main()
