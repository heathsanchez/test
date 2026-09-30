#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def lit(s):
    return json.dumps(str(s))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", required=True)
    args=ap.parse_args()

    result=json.loads(Path(args.result).read_text())
    candidate=result["candidate_sha"]
    authority=result["base_sha"]

    vals={
        "campaign":"nucleus",
        "residual":args.test,
        "candidate":candidate,
        "authority":authority,
        "corpus":args.corpus,
        "originEvidence":args.evidence,
    }

    def pins():
        return "\n".join(
            f"    && context.input.{k} == {lit(v)}"
            for k,v in vals.items()
            if k != "campaign"
        )

    policy=f'''// Generated from a source-pinned Nucleus qualification result.
// Do not edit this emitted policy by hand.
@id("nucleus_generated_admission_gate")
permit (
    principal,
    action == Nucleus::Action::"Admit",
    resource
)
when {{
    context.input.campaign == "nucleus"
{pins()}
}}
when temporal {{
    formerly within 24h (
        Nucleus::Action::"FullReclosureGreen"::response{{
            input.campaign: context.input.campaign,
            input.residual: context.input.residual,
            input.candidate: context.input.candidate,
            input.authority: context.input.authority,
            input.corpus: context.input.corpus,
            input.originEvidence: context.input.originEvidence
        }}
        && formerly within 24h (
            Nucleus::Action::"ControlsGreen"::response{{
                input.campaign: context.input.campaign,
                input.residual: context.input.residual,
                input.candidate: context.input.candidate,
                input.authority: context.input.authority,
                input.corpus: context.input.corpus,
                input.originEvidence: context.input.originEvidence
            }}
            && formerly within 24h (
                Nucleus::Action::"CandidateDerived"::response{{
                    input.campaign: context.input.campaign,
                    input.residual: context.input.residual,
                    input.candidate: context.input.candidate,
                    input.authority: context.input.authority,
                    input.corpus: context.input.corpus,
                    input.originEvidence: context.input.originEvidence
                }}
                && formerly within 24h
                    Nucleus::Action::"ResidualObserved"::response{{
                        input.campaign: context.input.campaign,
                        input.residual: context.input.residual,
                        input.candidate: context.input.candidate,
                        input.authority: context.input.authority,
                        input.corpus: context.input.corpus,
                        input.originEvidence: context.input.originEvidence
                    }}
            )
        )
    )
}}
unless temporal {{
    formerly within 24h
        Nucleus::Action::"CandidateRejected"::response{{
            input.campaign: context.input.campaign,
            input.residual: context.input.residual,
            input.candidate: context.input.candidate,
            input.authority: context.input.authority,
            input.corpus: context.input.corpus,
            input.originEvidence: context.input.originEvidence
        }}
}};
'''
    Path(args.out).write_text(policy)

if __name__=="__main__":
    main()
