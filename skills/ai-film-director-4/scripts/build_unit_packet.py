#!/usr/bin/env python3
from production_unit_packet import *
if __name__=='__main__':
    import argparse, json
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); ap.add_argument('--unit-id',required=True); a=ap.parse_args()
    print(json.dumps(write_unit_packet(a.project_root,a.unit_id),ensure_ascii=False,indent=2))
