from __future__ import annotations
import argparse, json
from .xray import scan, verify_claim
from .mutate import mutate
from .planner import plan
from .ci import check
from .evidence import save_ledger, load_ledger
from .validation import validate_artifact, SchemaValidationError

def main():
    ap=argparse.ArgumentParser(prog="repo-xray")
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("plan"); p.add_argument("root",nargs="?",default="."); p.add_argument("--claims",type=int,default=10); p.add_argument("--github-items",type=int,default=0); p.add_argument("--mutations",type=int,default=0); p.add_argument("--out")
    s=sub.add_parser("scan"); s.add_argument("root",nargs="?",default="."); s.add_argument("--pattern",action="append",default=[]); s.add_argument("--claim"); s.add_argument("--github",action="store_true"); s.add_argument("--out")
    c=sub.add_parser("claim"); c.add_argument("root"); c.add_argument("claim"); c.add_argument("--pattern",action="append",required=True); c.add_argument("--github",action="store_true"); c.add_argument("--out")
    m=sub.add_parser("mutate", aliases=["change"]); m.add_argument("root"); m.add_argument("change"); m.add_argument("--github",action="store_true"); m.add_argument("--out")
    v=sub.add_parser("validate"); v.add_argument("ledger")
    ci=sub.add_parser("ci"); ci.add_argument("ledger"); ci.add_argument("--baseline")
    a=ap.parse_args()
    if a.cmd=="plan": r=plan(a.root,a.claims,a.github_items,a.mutations)
    elif a.cmd=="scan": r=scan(a.root,a.pattern or ["TODO","FIXME"],claim=a.claim,github=a.github)
    elif a.cmd=="claim": r=verify_claim(a.root,a.claim,a.pattern,include_github=a.github)
    elif a.cmd=="mutate": r=mutate(a.root,a.change,include_github=a.github)
    elif a.cmd=="validate":
        r=load_ledger(a.ledger)
        try:
            validate_artifact(r)
        except (SchemaValidationError, OSError, ValueError) as exc:
            print(f"invalid: {exc}")
            raise SystemExit(2)
        print("valid"); return
    else:
        r=check(a.ledger,a.baseline); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r["ok"] else 2)
    if getattr(a,"out",None): save_ledger(r,a.out)
    print(json.dumps(r,indent=2,sort_keys=True))
if __name__=="__main__": main()
