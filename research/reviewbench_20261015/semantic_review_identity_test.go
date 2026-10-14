package github

import (
    "fmt"
    "io"
    "net/http"
    "strings"
    "testing"

    "github.com/cli/go-gh/v2/pkg/api"
)

type mgcheckFrozenREST struct {
    commits string
    reviews string
}

func (m mgcheckFrozenREST) RoundTrip(req *http.Request) (*http.Response, error) {
    var data string
    switch {
    case strings.HasSuffix(req.URL.Path, "/commits"):
        data = m.commits
    case strings.HasSuffix(req.URL.Path, "/reviews"):
        data = m.reviews
    default:
        return nil, fmt.Errorf("unexpected outbound endpoint: %s", req.URL.Path)
    }
    return &http.Response{StatusCode:200, Header:http.Header{"Content-Type": []string{"application/json"}},
        Body:io.NopCloser(strings.NewReader(data)), Request:req},nil
}

func TestMGCheckCopilotHeadIdentityNotClock(t *testing.T) {
    const headSHA = "1111111111111111111111111111111111111111"
    const olderSHA = "2222222222222222222222222222222222222222"
    tests := []struct {
        name, reviewSHA, committerTime, reviewTime, user string
        want bool
    }{
        {"stale-reviewed-different-sha-but-later-time", olderSHA, "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "copilot", false},
        {"fresh-matching-sha-but-earlier-review-time", headSHA, "2026-01-03T00:00:00Z", "2026-01-02T00:00:00Z", "copilot", true},
        {"fresh-matching-sha-and-later-time", headSHA, "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "copilot-pull-request-reviewer", true},
        {"noncopilot-review-not-authority", headSHA, "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "some-other-bot", false},
    }
    for _, tc := range tests {
        t.Run(tc.name,func(t *testing.T) {
            commits := fmt.Sprintf(`[{"sha":%q,"commit":{"committer":{"date":%q}}}]`, headSHA, tc.committerTime)
            reviews := fmt.Sprintf(`[{"user":{"login":%q},"commit_id":%q,"submitted_at":%q}]`,tc.user,tc.reviewSHA,tc.reviewTime)
            rest,err := api.NewRESTClient(api.ClientOptions{Host:"github.com", AuthToken:"mock-token",
                Transport:mgcheckFrozenREST{commits:commits,reviews:reviews}})
            if err != nil {t.Fatal(err)}
            client:=&Client{rest:rest,owner:"frozen",repo:"source"}
            got,err:=client.IsCopilotReviewFresh(9)
            if err != nil {t.Fatal(err)}
            if got!=tc.want {
                t.Errorf("fresh=%v, want %v. Review SHA %s, head SHA %s; clocks are not source identity",got,tc.want,tc.reviewSHA,headSHA)
            }
        })
    }
}
