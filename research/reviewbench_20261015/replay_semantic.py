#!/usr/bin/env python3
"""Retrospective source-native consequence test of ReviewBench Go PR #9.

NO golden findings read; observer authored after PR metadata and code inspection,
so discovery is NOT blind or autonomous. All edits ephemeral in owned CI worktree.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

FROZEN_HEAD="f98281938e63acd1d2df9b89d6af98dcf58c9fa8"
SRC="internal/github/github.go"
TEST="internal/github/mgcheck_freshness_test.go"
NEW_FUNCTION='''func (c *Client) IsCopilotReviewFresh(prNumber int) (bool, error) {
    var commits []struct { SHA string `json:"sha"` }
    err := c.rest.Get(fmt.Sprintf("repos/%s/%s/pulls/%d/commits", c.owner, c.repo, prNumber), &commits)
    if err != nil { return false, fmt.Errorf("failed to get PR commits: %w", err) }
    if len(commits) == 0 { return false, nil }
    headSHA := commits[len(commits)-1].SHA
    var reviews []struct {
        User struct { Login string `json:"login"` } `json:"user"`
        CommitID string `json:"commit_id"`
        SubmittedAt time.Time `json:"submitted_at"`
    }
    err = c.rest.Get(fmt.Sprintf("repos/%s/%s/pulls/%d/reviews", c.owner, c.repo, prNumber), &reviews)
    if err != nil { return false, fmt.Errorf("failed to get reviews: %w", err) }
    for _, r := range reviews {
        if isCopilotUser(r.User.Login) && r.CommitID == headSHA { return true, nil }
    }
    return false, nil
}

'''


def run(*args,cwd):
    return subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
    r=run("git","rev-parse","HEAD",cwd=repo)
    if r.returncode or r.stdout.strip()!=FROZEN_HEAD:
        raise RuntimeError("UNKNOWN_SOURCE_IDENTITY: original frozen head not present")
    src=repo/SRC; fixture=repo/TEST
    original=src.read_bytes()
    if fixture.exists(): raise RuntimeError("test target already exists")
    testbytes=(Path(__file__).parent/"semantic_review_identity_test.go").read_bytes()
    out.mkdir(parents=True,exist_ok=True)
    receipt={"source_head":FROZEN_HEAD,"original_sha256":digest(original),
             "test_sha256":digest(testbytes),"method":"human-authored after PR title+diff, not blinded",
             "independent_authority":"PR body explicitly claims commit_id must match current PR HEAD",
             "golden_reference_used":False,"arm":[]}
    try:
        fixture.write_bytes(testbytes)
        for arm in ("original","candidate_patch","removed_patch"):
            if arm == "candidate_patch":
                text=original.decode()
                begin=text.index("func (c *Client) IsCopilotReviewFresh(")
                end=text.index("func (c *Client) RequestCopilotReview(",begin)
                src.write_text(text[:begin]+NEW_FUNCTION+text[end:])
                receipt["candidate_patch_sha256"]=digest(src.read_bytes())
            if arm == "removed_patch":
                src.write_bytes(original)
                if digest(src.read_bytes())!=receipt["original_sha256"]:
                    raise RuntimeError("FAILED_CAUSAL_RESTORE")
            proc=run("go","test","./internal/github","-run","^TestMGCheckCopilotHeadIdentityNotClock$","-count=1","-v",cwd=repo)
            (out/f"{arm}.log").write_text(proc.stdout)
            actual="PASS" if proc.returncode == 0 else "FAIL"
            expect="PASS" if arm=="candidate_patch" else "FAIL"
            receipt["arm"].append({"name":arm,"actual":actual,"expected":expect,"exit":proc.returncode})
            if actual != expect: raise RuntimeError(f"{arm}: expected {expect}, observed {actual}")
            if arm=="original" and "stale-reviewed-different-sha" not in proc.stdout:
                raise RuntimeError("original failed for unrelated cause")
        receipt["qualification"]="WARRANTED_BOUNDED_RETROSPECTIVE_SOURCE_NATIVE_CONTRACT_SEPARATOR"
    finally:
        src.write_bytes(original)
        if fixture.exists(): fixture.unlink()
        receipt["final_source_restored"]=digest(src.read_bytes())==digest(original)
        receipt["fixture_removed"]=not fixture.exists()
        (out/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    if not receipt["final_source_restored"] or not receipt["fixture_removed"]:
        raise RuntimeError("restoration control failed")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__":
    main()
