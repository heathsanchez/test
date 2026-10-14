package github

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "strings"
    "testing"
    "github.com/cli/go-gh/v2/pkg/api"
)

type mgcheckPagedAPI struct {
    commits [2]string
    reviews [2]string
    pagedEndpoint string
    prHead string
}
func (p *mgcheckPagedAPI) RoundTrip(req *http.Request) (*http.Response, error) {
    if strings.HasSuffix(req.URL.Path, "/pulls/9") {
        payload:=fmt.Sprintf("{\"head\":{\"sha\":%q}}",p.prHead)
        return &http.Response{StatusCode:200,
            Header:http.Header{"Content-Type":[]string{"application/json"}},
            Body:io.NopCloser(strings.NewReader(payload)),Request:req},nil
    }
    if v:=req.URL.Query().Get("page"); v!="" && v!="1" && v!="2" {
        return &http.Response{StatusCode:200,
            Header:http.Header{"Content-Type":[]string{"application/json"}},
            Body:io.NopCloser(strings.NewReader("[]")),Request:req},nil
    }
    var pages [2]string
    endpoint := ""
    switch {
    case strings.HasSuffix(req.URL.Path, "/commits"):
        pages=p.commits
        endpoint="commits"
    case strings.HasSuffix(req.URL.Path, "/reviews"):
        pages=p.reviews
        endpoint="reviews"
    default:
        return nil,fmt.Errorf("unrecognized mock REST endpoint: %s",req.URL.Path)
    }
    page:=0
    if req.URL.Query().Get("page")=="2" {page=1}
    headers:=http.Header{"Content-Type":[]string{"application/json"}}
    if page==0 && endpoint==p.pagedEndpoint {
        headers.Set("Link",fmt.Sprintf(
            "<https://api.github.com/repos/frozen/source/pulls/9/%s?page=2>; rel=\"next\"",
            endpoint))
    }
    return &http.Response{
        StatusCode:200,Header:headers,
        Body:io.NopCloser(strings.NewReader(pages[page])),Request:req},nil
}
func mgcheckJSON(t *testing.T,v any) string {
    t.Helper()
    data,err:=json.Marshal(v)
    if err!=nil {t.Fatal(err)}
    return string(data)
}
func mgcheckClient(t *testing.T,p *mgcheckPagedAPI) *Client {
    t.Helper()
    rest,err:=api.NewRESTClient(api.ClientOptions{
        Host:"github.com",AuthToken:"mock-token",Transport:p})
    if err!=nil {t.Fatal(err)}
    return &Client{rest:rest,owner:"frozen",repo:"source"}
}
func mgcheckCommit(sha,when string) any {
    return map[string]any{"sha":sha,"commit":map[string]any{
        "committer":map[string]any{"date":when}}}
}
func mgcheckReview(who,sha,when string) any {
    return map[string]any{
        "user":map[string]any{"login":who},
        "commit_id":sha,"submitted_at":when,"state":"COMMENTED"}
}

func TestMGCheckStrongReviewerPaginationResidual(t *testing.T) {
    const headSHA="1111111111111111111111111111111111111111"
    const previousSHA="2222222222222222222222222222222222222222"
    t.Run("commit_page_two_current_head",func(t *testing.T){
        firstPage:=make([]any,30)
        for i:=range firstPage {
            firstPage[i]=mgcheckCommit(previousSHA,"2026-01-03T00:00:00Z")
        }
        secondPage:=[]any{mgcheckCommit(headSHA,"2026-01-02T00:00:00Z")}
        reviews:=[]any{mgcheckReview("copilot",headSHA,"2026-01-02T12:00:00Z")}
        rt:=&mgcheckPagedAPI{
            prHead:headSHA,
            commits:[2]string{mgcheckJSON(t,firstPage),mgcheckJSON(t,secondPage)},
            reviews:[2]string{mgcheckJSON(t,reviews),"[]"},
            pagedEndpoint:"commits"}
        fresh,err:=mgcheckClient(t,rt).IsCopilotReviewFresh(9)
        if err!=nil {t.Fatal(err)}
        if !fresh {
            t.Error("expected fresh current-head review at 31st commit; only first page was processed")
        }
    })
    t.Run("review_page_two_current_copilot",func(t *testing.T){
        commits:=[]any{mgcheckCommit(headSHA,"2026-01-01T00:00:00Z")}
        firstPage:=make([]any,30)
        for i:=range firstPage {
            firstPage[i]=mgcheckReview("some-other-bot",previousSHA,"2026-01-01T00:00:00Z")
        }
        secondPage:=[]any{mgcheckReview("copilot",headSHA,"2026-01-03T00:00:00Z")}
        rt:=&mgcheckPagedAPI{
            prHead:headSHA,
            commits:[2]string{mgcheckJSON(t,commits),"[]"},
            reviews:[2]string{mgcheckJSON(t,firstPage),mgcheckJSON(t,secondPage)},
            pagedEndpoint:"reviews"}
        fresh,err:=mgcheckClient(t,rt).IsCopilotReviewFresh(9)
        if err!=nil {t.Fatal(err)}
        if !fresh {
            t.Error("expected fresh review on 31st review page item; only first page was processed")
        }
    })
}
func TestMGCheckStrongReviewerSinglePageControl(t *testing.T) {
    const headSHA="1111111111111111111111111111111111111111"
    rt:=&mgcheckPagedAPI{
            prHead:headSHA,
        commits:[2]string{mgcheckJSON(t,[]any{mgcheckCommit(headSHA,"2026-01-01T00:00:00Z")}),"[]"},
        reviews:[2]string{mgcheckJSON(t,[]any{mgcheckReview("copilot",headSHA,"2026-01-03T00:00:00Z")}),"[]"},
        pagedEndpoint:"none"}
    fresh,err:=mgcheckClient(t,rt).IsCopilotReviewFresh(9)
    if err!=nil {t.Fatal(err)}
    if !fresh {t.Error("unchanged simple first-page positive control failed")}
}


func TestMGCheckStrongReviewerDismissedNotFresh(t *testing.T) {
    const headSHA="1111111111111111111111111111111111111111"
    commits:=[]any{mgcheckCommit(headSHA,"2026-01-01T00:00:00Z")}
    review:=map[string]any{
        "user":map[string]any{"login":"copilot"},
        "commit_id":headSHA,"submitted_at":"2026-01-03T00:00:00Z",
        "state":"DISMISSED"}
    rt:=&mgcheckPagedAPI{
        prHead:headSHA,
        commits:[2]string{mgcheckJSON(t,commits),"[]"},
        reviews:[2]string{mgcheckJSON(t,[]any{review}),"[]"},
        pagedEndpoint:"none"}
    fresh,err:=mgcheckClient(t,rt).IsCopilotReviewFresh(9)
    if err!=nil {t.Fatal(err)}
    if fresh {t.Error("a dismissed review must not count as a current active review")}
}

func TestMGCheckStrongReviewerMissingHeadFailsClosed(t *testing.T) {
    const headSHA="1111111111111111111111111111111111111111"
    rt:=&mgcheckPagedAPI{
        prHead:"",
        commits:[2]string{"[]","[]"},
        reviews:[2]string{mgcheckJSON(t,[]any{mgcheckReview("copilot",headSHA,"2026-01-03T00:00:00Z")}),"[]"},
        pagedEndpoint:"none"}
    fresh,_:=mgcheckClient(t,rt).IsCopilotReviewFresh(9)
    if fresh {t.Error("missing authoritative PR head cannot justify freshness")}
}
