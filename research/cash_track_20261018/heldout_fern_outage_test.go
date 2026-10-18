package api

import (
    "strings"
    "testing"
)

// Authored independently for the frozen 2026-10-18 MathGraph competition
// preflight. It calls the ORIGINAL repository's envFault implementation.
// It is not copied from the upstream contributor's test file.
func TestCashtrackHeldoutOutageEvidence(t *testing.T) {
    cases := []struct {
        name string
        originalResult string
        wantDeclaredOutage bool
    }{
        {
            name: "step_declared_only",
            originalResult: "STEP FAIL consent dispatch interrupted DURING DECLARED OUTAGE consent_cut\n",
            wantDeclaredOutage: true,
        },
        {
            name: "step_without_declared_outage",
            originalResult: "STEP FAIL consent dispatch interrupted (product API response mismatch)\n",
            wantDeclaredOutage: false,
        },
        {
            name: "declared_step_plus_unexcused_product_check",
            originalResult: "STEP FAIL consent dispatch interrupted DURING DECLARED OUTAGE consent_cut\nCHECK FAIL Equal want=200 got=201\n",
            wantDeclaredOutage: false,
        },
        {
            name: "ordinary_declared_check",
            originalResult: "CHECK FAIL Equal want=200 got=503 DURING DECLARED OUTAGE consent_cut\n",
            wantDeclaredOutage: true,
        },
        {
            name: "declared_step_with_an_unbound_check",
            originalResult: "STEP FAIL snapshot blocked DURING DECLARED OUTAGE other_cut\nCHECK FAIL unexpected business-state result\n",
            wantDeclaredOutage: false,
        },
        {
            name: "unbound_step_plus_informational_outage_notice",
            originalResult: "STEP FAIL snapshots mismatched\nNOTICE DURING DECLARED OUTAGE known_cut\n",
            wantDeclaredOutage: false,
        },
        {
            name: "declared_check_plus_unexcused_check",
            originalResult: "CHECK FAIL retry DURING DECLARED OUTAGE known_cut\nCHECK FAIL wrong invoice amount\n",
            wantDeclaredOutage: false,
        },
    }
    for _, tt := range cases {
        t.Run(tt.name, func(t *testing.T) {
            got := envFault(tt.originalResult)
            isOutage := strings.HasPrefix(got, "declared outage:")
            if isOutage != tt.wantDeclaredOutage {
                t.Fatalf("native verdict mismatch: outage=%t want=%t; envFault=%q", isOutage, tt.wantDeclaredOutage, got)
            }
        })
    }
}
