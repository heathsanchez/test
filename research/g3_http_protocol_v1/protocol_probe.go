// Protocol observer V1: finite future-relative trace quotient for a Go HTTP writer.
//
// This grammar was declared before the source implementation was inspected.
// It is a HUMAN-DECLARED experiment, not an autonomous new-operator invention.
// It runs as an external file from within each exact-pinned go-chi module checkout.
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"

	"github.com/go-chi/chi/v5/middleware"
)

// The same downstream recorder is used for direct and wrapped executions.
type recorder struct {
	*httptest.ResponseRecorder
	flushes int
}

func newRecorder() *recorder {
	return &recorder{ResponseRecorder: &httptest.ResponseRecorder{
		HeaderMap: make(http.Header),
		Body:      new(bytes.Buffer),
	}}
}

func (r *recorder) Flush() {
	r.flushes++
	r.ResponseRecorder.Flush()
}

type fancyRecorder struct{ *recorder }

func (r *fancyRecorder) Hijack() (net.Conn, *bufio.ReadWriter, error) {
	return nil, nil, errors.New("no socket in bounded protocol probe")
}

func (r *fancyRecorder) ReadFrom(src io.Reader) (int64, error) {
	return io.Copy(r.ResponseRecorder, src)
}

type http2Recorder struct{ *recorder }

func (r *http2Recorder) Push(string, *http.PushOptions) error {
	return errors.New("push action outside frozen alphabet")
}

type carrier struct {
	Name       string   `json:"name"`
	ProtoMajor int      `json:"proto_major"`
	Alphabet   []string `json:"alphabet"`
}

func carriers() []carrier {
	ordinary := []string{"H200", "H204", "H418", "W0", "W1", "F"}
	fancy := append(append([]string{}, ordinary...), "R0", "R1")
	return []carrier{
		{Name: "http1_flusher", ProtoMajor: 1, Alphabet: ordinary},
		{Name: "http1_fancy_readerfrom", ProtoMajor: 1, Alphabet: fancy},
		{Name: "http2_flusher_pusher", ProtoMajor: 2, Alphabet: ordinary},
	}
}

func newCarrier(c carrier) (http.ResponseWriter, *recorder) {
	r := newRecorder()
	switch c.Name {
	case "http1_flusher":
		return r, r
	case "http1_fancy_readerfrom":
		return &fancyRecorder{r}, r
	case "http2_flusher_pusher":
		return &http2Recorder{r}, r
	default:
		panic("unfrozen carrier")
	}
}

type observation struct {
	Status         int    `json:"wrapper_status"`
	BytesWritten   int    `json:"wrapper_bytes_written"`
	DownstreamCode int    `json:"downstream_code"`
	DownstreamBody string `json:"downstream_body"`
	Flushes        int    `json:"flushes"`
}

type traceObserver interface {
	Status() int
	BytesWritten() int
}

// Independent synthetic controls, deliberately not using go-chi internals.
// The good variant forwards output effects while preserving status and bytes.
// Each bad variant violates one single reference-observable invariant.
type toyWriter struct {
	http.ResponseWriter
	status int
	bytes int
	sent bool
	mode string
}

func (t *toyWriter) Status() int { return t.status }
func (t *toyWriter) BytesWritten() int { return t.bytes }
func (t *toyWriter) WriteHeader(code int) {
	if !t.sent {
		t.sent = true
		t.status = code
		t.ResponseWriter.WriteHeader(code)
	}
}
func (t *toyWriter) Write(b []byte) (int, error) {
	if !t.sent {
		t.WriteHeader(http.StatusOK)
	}
	n, err := t.ResponseWriter.Write(b)
	t.bytes += n
	return n, err
}
func (t *toyWriter) Flush() {
	if !t.sent {
		if t.mode == "toy_bad_flush" {
			t.sent = true
		} else {
			t.WriteHeader(http.StatusOK)
		}
	}
	t.ResponseWriter.(http.Flusher).Flush()
}
func (t *toyWriter) ReadFrom(r io.Reader) (int64, error) {
	if t.mode == "toy_bad_empty_readerfrom" {
		payload, err := io.ReadAll(r)
		if err != nil {
			return 0, err
		}
		if len(payload) == 0 && !t.sent {
			t.WriteHeader(http.StatusOK)
		}
		return io.Copy(t, bytes.NewReader(payload))
	}
	return io.Copy(t, r)
}

func apply(w http.ResponseWriter, op string) error {
	switch op {
	case "H200":
		w.WriteHeader(200)
	case "H204":
		w.WriteHeader(204)
	case "H418":
		w.WriteHeader(418)
	case "W0":
		_, err := w.Write([]byte{})
		return err
	case "W1":
		_, err := w.Write([]byte("x"))
		return err
	case "F":
		f, ok := w.(http.Flusher)
		if !ok {
			return errors.New("required Flusher interface absent")
		}
		f.Flush()
	case "R0", "R1":
		r, ok := w.(io.ReaderFrom)
		if !ok {
			return errors.New("required ReaderFrom interface absent")
		}
		payload := ""
		if op == "R1" {
			payload = "x"
		}
		_, err := r.ReadFrom(strings.NewReader(payload))
		return err
	default:
		return fmt.Errorf("unfrozen action %q", op)
	}
	return nil
}

func execute(c carrier, trace []string, wrapped, negativeControl bool, mode string) (observation, error) {
	base, r := newCarrier(c)
	w := base
	if wrapped {
		if mode == "native" {
			w = middleware.NewWrapResponseWriter(base, c.ProtoMajor)
		} else {
			w = &toyWriter{ResponseWriter: base, mode: mode}
		}
	}
	for _, op := range trace {
		if err := apply(w, op); err != nil {
			return observation{}, err
		}
	}
	o := observation{
		Status: -1, BytesWritten: -1, DownstreamCode: r.Code,
		DownstreamBody: r.Body.String(), Flushes: r.flushes,
	}
	if wrapped {
		wrappedWriter, ok := w.(traceObserver)
		if !ok {
			return observation{}, errors.New("constructor did not return declared wrapper")
		}
		o.Status = wrappedWriter.Status()
		o.BytesWritten = wrappedWriter.BytesWritten()
		// A deliberately broken *observer*, separate from native code, must be
		// detected by this verifier. Never interpret it as a source defect.
		if negativeControl && len(trace) > 0 && trace[0] == "F" {
			o.Status = -999
		}
	}
	return o, nil
}

func enumerate(alphabet []string, maxLen int) [][]string {
	all := [][]string{}
	var walk func([]string, int)
	walk = func(prefix []string, remaining int) {
		all = append(all, append([]string{}, prefix...))
		if remaining == 0 {
			return
		}
		for _, op := range alphabet {
			walk(append(append([]string{}, prefix...), op), remaining-1)
		}
	}
	walk(nil, maxLen)
	return all
}

func signature(c carrier, prefix []string, suffixes [][]string, wrapped, negativeControl bool, mode string) (string, []observation, error) {
	observations := make([]observation, 0, len(suffixes))
	for _, suffix := range suffixes {
		trace := append(append([]string{}, prefix...), suffix...)
		o, err := execute(c, trace, wrapped, negativeControl, mode)
		if err != nil {
			return "", nil, fmt.Errorf("trace %v: %w", trace, err)
		}
		observations = append(observations, o)
	}
	encoded, err := json.Marshal(observations)
	return string(encoded), observations, err
}

type witness struct {
	FirstTrace     []string      `json:"first_trace"`
	SecondTrace    []string      `json:"second_trace"`
	ReferenceFirst observation   `json:"reference_first"`
	ReferenceOther observation   `json:"reference_second"`
	WrapperFirst   observation   `json:"wrapper_first"`
	WrapperOther   observation   `json:"wrapper_second"`
}

type familyResult struct {
	Carrier         string    `json:"carrier"`
	Prefixes        int       `json:"prefixes"`
	ReferenceClasses int      `json:"reference_classes"`
	ViolatingClasses int      `json:"violating_classes"`
	Witnesses       []witness `json:"witnesses"`
	DirectTraceCount int      `json:"direct_trace_count"`
	DirectMismatches int      `json:"direct_mismatches"`
	DirectFirstMismatch []string `json:"direct_first_mismatch"`
}

type row struct {
	Prefix    []string
	Subject   string
	Reference []observation
	Wrapped   []observation
}

// The deliberately simpler full-reference oracle baseline uses the same
// actions and source compilation but does not learn quotient classes or
// compare two different histories. Its expected wrapper values are fixed
// directly by the declared HTTP writer contract and its fresh recorder.
func directBaseline(c carrier, mode string) (int, int, []string, error) {
	traces := enumerate(c.Alphabet, 3)
	mismatches := 0
	var first []string
	for _, trace := range traces {
		r, err := execute(c, trace, false, false, mode)
		if err != nil {return len(traces),mismatches,first,err}
		w, err := execute(c, trace, true, false, mode)
		if err != nil {return len(traces),mismatches,first,err}
		if w.Status != r.DownstreamCode ||
			w.BytesWritten != len(r.DownstreamBody) ||
			w.DownstreamCode != r.DownstreamCode ||
			w.DownstreamBody != r.DownstreamBody ||
			w.Flushes != r.Flushes {
			mismatches++
			if first == nil {first=append([]string{},trace...)}
		}
	}
	return len(traces),mismatches,first,nil
}

func check(c carrier, negativeControl bool, mode string) (familyResult, error) {
	// All prefixes of length <= 2, all continuations of length <= 1;
	// the longest native trace has three actions. This is a bounded
	// future-relative quotient, not unbounded trace equivalence.
	prefixes := enumerate(c.Alphabet, 2)
	suffixes := enumerate(c.Alphabet, 1)
	groups := make(map[string]row)
	violating := make(map[string]bool)
	result := familyResult{Carrier: c.Name, Prefixes: len(prefixes), Witnesses: []witness{}}
	for _, prefix := range prefixes {
		refKey, refObs, err := signature(c, prefix, suffixes, false, false, mode)
		if err != nil {
			return result, fmt.Errorf("reference: %w", err)
		}
		subjectKey, subjectObs, err := signature(c, prefix, suffixes, true, negativeControl, mode)
		if err != nil {
			return result, fmt.Errorf("native wrapper: %w", err)
		}
		old, exists := groups[refKey]
		if !exists {
			groups[refKey] = row{Prefix: prefix, Subject: subjectKey, Reference: refObs, Wrapped: subjectObs}
			continue
		}
		if old.Subject != subjectKey && !violating[refKey] {
			violating[refKey] = true
			if len(result.Witnesses) < 10 {
				result.Witnesses = append(result.Witnesses, witness{
					FirstTrace: old.Prefix, SecondTrace: prefix,
					ReferenceFirst: old.Reference[0], ReferenceOther: refObs[0],
					WrapperFirst: old.Wrapped[0], WrapperOther: subjectObs[0],
				})
			}
		}
	}
	result.ReferenceClasses = len(groups)
	result.ViolatingClasses = len(violating)
	if !negativeControl {
		count,mismatches,first,err := directBaseline(c,mode)
		if err != nil {return result,fmt.Errorf("direct baseline: %w",err)}
		result.DirectTraceCount=count
		result.DirectMismatches=mismatches
		result.DirectFirstMismatch=first
	}
	return result, nil
}

func main() {
	output := flag.String("out", "", "JSON result path")
	negativeControl := flag.Bool("inject-bad-observer", false, "test checker sensitivity, never a native claim")
	mode := flag.String("wrapper-mode", "native", "native|toy_good|toy_bad_flush|toy_bad_empty_readerfrom")
	flag.Parse()
	if *output == "" {
		fmt.Fprintln(os.Stderr, "--out required")
		os.Exit(2)
	}
	if *mode != "native" && *mode != "toy_good" && *mode != "toy_bad_flush" && *mode != "toy_bad_empty_readerfrom" {
		fmt.Fprintln(os.Stderr, "unrecognized predeclared wrapper mode")
		os.Exit(2)
	}
	results := []familyResult{}
	total := 0
	for _, c := range carriers() {
		r, err := check(c, *negativeControl, *mode)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(3)
		}
		results = append(results, r)
		total += r.ViolatingClasses
		fmt.Printf("CARRIER=%s PREFIXES=%d CLASSES=%d VIOLATIONS=%d DIRECT_MISMATCHES=%d/%d FIRST_DIRECT=%v\n", c.Name, r.Prefixes, r.ReferenceClasses, r.ViolatingClasses,r.DirectMismatches,r.DirectTraceCount,r.DirectFirstMismatch)
		for _, w := range r.Witnesses {
			fmt.Printf("WITNESS %s %v ~ %v REF %d/%d WRAPPER %d/%d\n", c.Name, w.FirstTrace, w.SecondTrace, w.ReferenceFirst.DownstreamCode, w.ReferenceOther.DownstreamCode, w.WrapperFirst.Status, w.WrapperOther.Status)
		}
	}
	status := "WARRANTED_BOUNDED_NO_QUOTIENT_VIOLATIONS"
	if total > 0 {
		status = "CANDIDATE_NATIVE_TRACE_QUOTIENT_COUNTEREXAMPLE"
	}
	if *negativeControl {
		status = "INJECTED_OBSERVER_NEGATIVE_CONTROL_ONLY"
	}
	result := struct {
		Schema    string         `json:"schema"`
		Status    string         `json:"status"`
		Injected  bool           `json:"injected_observer"`
		Mode      string         `json:"wrapper_mode"`
		Total     int            `json:"total_violating_classes"`
		Families  []familyResult `json:"families"`
		Boundary  string         `json:"boundary"`
	}{
		Schema: "mgcheck.http-writer-protocol-future-quotient.v1",
		Status: status, Injected: *negativeControl, Mode: *mode,
		Total: total, Families: results,
		Boundary: "human-declared actions; native pinned module; prefix<=2 suffix<=1; no autonomous grammar invention or global correctness claim",
	}
	encoded, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		panic(err)
	}
	if err := os.WriteFile(*output, append(encoded, '\n'), 0644); err != nil {
		panic(err)
	}
}
