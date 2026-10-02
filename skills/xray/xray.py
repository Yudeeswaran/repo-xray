from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from .scope import SearchScope, matching_lines, count_files
from .evidence import Evidence, make_claim, new_ledger, save_ledger
from .risk import rank_risk
from .git import log, is_repo, head, current_ref, blame, GitError
from .github import search_discussion, repo_name, gh_available
from .planner import plan
from .requirements import concepts, has_numeric_conflict, textual_conflict, scope_conflict

def _semantic_polarity(claim, snippet):
    cc=concepts(claim); sc=concepts(snippet)
    if not (cc & sc):
        return "context"
    if textual_conflict(claim, snippet) or scope_conflict(claim, snippet):
        return "contradicts"
    if has_numeric_conflict(claim, snippet):
        # Multi-value claims often have aggregate values in implementation
        # comments/config (e.g. 10+20+40 = 70). Do not call those conflicts.
        if len(__import__("skills.xray.requirements", fromlist=["quantities"]).quantities(claim)) > 1 and ("total" in snippet.lower() or "sum(" in snippet.lower()):
            return "context"
        # If the claim names a concrete identifier (e.g. RequestTimeout),
        # require that identifier to occur as a standalone token before a
        # numeric mismatch can contradict it. This prevents MinRequestTimeout
        # from contradicting RequestTimeout merely because both are timeouts.
        identifiers = [x for x in re.findall(r"\b[A-Z][A-Za-z0-9_]{2,}\b", claim) if "_" in x or re.search(r"[a-z][A-Z]", x) or (x.isupper() and len(x) >= 5)]
        if identifiers:
            low = snippet.lower()
            if not any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(i.lower())}(?![A-Za-z0-9_])", low) for i in identifiers):
                return "context"
        return "contradicts"
    return "supports"

def _classify_claim(claim, hits):
    claim_lower=claim.lower()
    runtime_markers=("in production", "scales to", "10k rps", "10000 rps", "uptime", "externally", "third-party", "real-world", "occurs", "provider charges")
    direct=[h for h in hits if h.get("strength") in {"direct","test","config"}]
    if any(m in claim_lower for m in runtime_markers) and not direct:
        return "UNCHECKABLE"
    if "provider charges" in claim_lower:
        provider_test = any(h.get("strength") == "test" and "provider" in h.get("snippet", "").lower() and "charge" in h.get("snippet", "").lower() for h in hits)
        if not provider_test:
            return "UNCHECKABLE"
    if not hits: return "UNVERIFIED"
    supports=[h for h in hits if h["polarity"]=="supports"]
    contradicts=[h for h in hits if h["polarity"]=="contradicts"]
    if supports and contradicts: return "CONTRADICTED"
    if contradicts: return "CONTRADICTED"
    return "VERIFIED"

def _evidence_hits(root, claim, patterns, paths):
    out=[]
    for p,line,snippet in matching_lines(root,patterns,paths):
        pol=_semantic_polarity(claim,snippet)
        rel=str(p.relative_to(root)).lower()
        strength="test" if "/test" in "/"+rel or rel.startswith("test") or p.name.lower().startswith("test") else "config" if p.suffix.lower() in {".yml",".yaml",".toml",".ini",".conf"} or "config" in rel else "direct" if p.suffix.lower() not in {".md",".rst",".txt"} else "discussion"
        out.append(Evidence(source_type="repository", locator={"file":str(p.relative_to(root)),"line":line}, snippet=snippet, strength=strength, polarity=pol, confidence=0.9 if pol != "context" else 0.6).__dict__.copy())
    return out

def verify_claim(root, claim, patterns, paths=("**/*",), include_github=False, git_limit=50, github_limit=10):
    root=Path(root).resolve(); patterns=list(patterns)
    hits=_evidence_hits(root,claim,patterns,paths)
    git_items=[]
    git_error=None
    repo_ok=False
    try:
        repo_ok=is_repo(root)
        if repo_ok:
            git_items=log(root,git_limit)
    except GitError as exc:
        git_error=str(exc)
    gh_items={"issues":[],"pull_requests":[],"errors":[]}
    if include_github:
        gh_items=search_discussion(root," OR ".join(patterns[:5]),github_limit,hydrate=True)
        for item in gh_items.get("issues",[]):
            hits.append(Evidence(source_type="github_issue", locator={"number":item.get("number"),"url":item.get("url")}, snippet=(item.get("title") or "")+" "+(item.get("body") or ""), strength="discussion", polarity="context", confidence=0.45).__dict__.copy())
        for item in gh_items.get("pull_requests",[]):
            hits.append(Evidence(source_type="github_pr", locator={"number":item.get("number"),"url":item.get("url")}, snippet=(item.get("title") or "")+" "+(item.get("body") or ""), strength="discussion", polarity="context", confidence=0.45).__dict__.copy())
    classification=_classify_claim(claim,hits)
    github_scope={"requested": include_github, "repository": repo_name(root) if include_github else None, "issues": len(gh_items.get("issues",[])), "pull_requests": len(gh_items.get("pull_requests",[])), "errors": gh_items.get("errors",[])}
    scope=SearchScope(str(root),list(paths),patterns,git_range="HEAD~50..HEAD" if repo_ok else None,github_scope=github_scope,ignored_dirs=None).to_dict()
    notes=[]
    if git_error:
        notes.append(f"Git history collection failed: {git_error}")
    if gh_items.get("errors"):
        notes.append("GitHub evidence collection reported errors: " + "; ".join(gh_items["errors"]))
    if classification=="UNVERIFIED":
        notes.append("No supporting or contradictory evidence was found within the recorded search scope.")
        confidence=0.2
    elif classification=="CONTRADICTED":
        notes.append("At least one collected repository evidence item conflicts with the claim.")
        confidence=0.9
    elif classification=="UNCHECKABLE":
        notes.append("The claim requires evidence that cannot be established by the collected static evidence within this scope.")
        confidence=0.2
    else:
        notes.append("Evidence supporting the claim was found within the recorded search scope.")
        confidence=0.85
    risk=rank_risk(claim,hits,classification)
    c=make_claim(claim,classification,hits,scope,risk,confidence,notes)
    metadata={"git_head":None,"git_ref":None,"github_repo":repo_name(root) if include_github else None, "git_error":git_error, "github_errors":gh_items.get("errors",[])}
    if repo_ok:
        try:
            metadata["git_head"]=head(root); metadata["git_ref"]=current_ref(root)
        except GitError as exc:
            metadata["git_error"]=str(exc)
    return new_ledger(root,[c],metadata=metadata)

def scan(root, patterns, paths=("**/*",), claim=None, github=False):
    root=Path(root).resolve(); patterns=list(patterns)
    if claim:
        return verify_claim(root,claim,patterns,paths,github)
    hits=_evidence_hits(root," ".join(patterns),patterns,paths)
    scope=SearchScope(str(root),list(paths),patterns,git_range="HEAD~50..HEAD" if is_repo(root) else None,github_scope=["issues","pull_requests"] if github else []).to_dict()
    return {"schema_version":"1.0","root":str(root),"matches":hits,"scope":scope,"git":log(root,50) if is_repo(root) else [],"plan":plan(root,claims=max(1,len(hits)//20),github_items=0),"file_count":count_files(root,paths)}

def main():
    ap=argparse.ArgumentParser(prog="repo-xray")
    sub=ap.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("scan",help="scan repository or verify a claim")
    s.add_argument("root",nargs="?",default="."); s.add_argument("--pattern",action="append",required=True); s.add_argument("--claim"); s.add_argument("--github",action="store_true"); s.add_argument("--path",action="append",default=["**/*"]); s.add_argument("--out")
    c=sub.add_parser("claim",help="verify a claim"); c.add_argument("root"); c.add_argument("claim"); c.add_argument("--pattern",action="append",required=True); c.add_argument("--github",action="store_true"); c.add_argument("--out")
    args=ap.parse_args()
    if args.cmd=="scan": result=scan(args.root,args.pattern,paths=args.path,claim=args.claim,github=args.github)
    else: result=verify_claim(args.root,args.claim,args.pattern,include_github=args.github)
    if args.out: save_ledger(result,args.out)
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__": main()
