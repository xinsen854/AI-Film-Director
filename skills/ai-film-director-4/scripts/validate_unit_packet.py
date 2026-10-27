#!/usr/bin/env python3
from production_unit_packet import *
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); ap.add_argument('--unit-id',required=True); a=ap.parse_args()
    e=validate_unit_packet(a.project_root,unit_id=a.unit_id); print('PASS' if not e else 'FAIL\n- '+'\n- '.join(e)); raise SystemExit(1 if e else 0)
