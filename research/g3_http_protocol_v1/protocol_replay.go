// Independent native replay checker for bounded HTTP future-quotient witnesses.
// Does not import the searcher or trust its aggregate counts. It only trusts
// source-pinned native Go compilation, an explicit action alphabet and replays.
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
	"reflect"
	"strings"

	"github.com/go-chi/chi/v5/middleware"
)

type observation struct {
	Status int `json:"wrapper_status"`
	Bytes int `json:"wrapper_bytes_written"`
	Code int `json:"downstream_code"`
	Body string `json:"downstream_body"`
	Flushes int `json:"flushes"`
}
type witness struct {
	First []string `json:"first_trace"`
	Second []string `json:"second_trace"`
	RefFirst observation `json:"reference_first"`
	RefSecond observation `json:"reference_second"`
	WrapFirst observation `json:"wrapper_first"`
	WrapSecond observation `json:"wrapper_second"`
}
type family struct {
	Carrier string `json:"carrier"`
	Violations int `json:"violating_classes"`
	Witnesses []witness `json:"witnesses"`
}
type report struct {
	Schema string `json:"schema"`
	Injected bool `json:"injected_observer"`
	Mode string `json:"wrapper_mode"`
	Families []family `json:"families"`
}

type observedRecorder struct {
	*httptest.ResponseRecorder
	flushes int
}
func (r *observedRecorder) Flush() {
	r.flushes++
	r.ResponseRecorder.Flush()
}
type readerTransport struct {*observedRecorder}
func (r *readerTransport) Hijack() (net.Conn, *bufio.ReadWriter, error) {
	return nil, nil, errors.New("bounded replay has no connection")
}
func (r *readerTransport) ReadFrom(src io.Reader) (int64, error) {
	return io.Copy(r.ResponseRecorder, src)
}
type pushTransport struct {*observedRecorder}
func (r *pushTransport) Push(string, *http.PushOptions) error {
	return errors.New("push outside frozen alphabet")
}

func transport(name string) (http.ResponseWriter, *observedRecorder, int, []string, error) {
	r := &observedRecorder{ResponseRecorder: &httptest.ResponseRecorder{
		HeaderMap: make(http.Header), Body: new(bytes.Buffer),
	}}
	actions := []string{"H200", "H204", "H418", "W0", "W1", "F"}
	switch name {
	case "http1_flusher":
		return r, r, 1, actions, nil
	case "http1_fancy_readerfrom":
		return &readerTransport{r}, r, 1, append(actions, "R0", "R1"), nil
	case "http2_flusher_pusher":
		return &pushTransport{r}, r, 2, actions, nil
	}
	return nil, nil, 0, nil, fmt.Errorf("unfrozen carrier: %s", name)
}

func action(w http.ResponseWriter, op string) error {
	switch op {
	case "H200", "H204", "H418":
		code := map[string]int{"H200":200, "H204":204, "H418":418}[op]
		w.WriteHeader(code)
	case "W0", "W1":
		payload := []byte{}
		if op == "W1" { payload = []byte("x") }
		_, err := w.Write(payload)
		return err
	case "F":
		f, ok := w.(http.Flusher)
		if !ok { return errors.New("Flusher missing") }
		f.Flush()
	case "R0", "R1":
		f, ok := w.(io.ReaderFrom)
		if !ok { return errors.New("ReaderFrom missing") }
		input := ""
		if op == "R1" {input = "x"}
		_, err := f.ReadFrom(strings.NewReader(input))
		return err
	default:
		return fmt.Errorf("unfrozen action %s", op)
	}
	return nil
}

func native(name string, trace []string, wrapped bool) (observation, error) {
	downstream, recorder, proto, allowed, err := transport(name)
	if err != nil {return observation{}, err}
	valid := make(map[string]bool, len(allowed))
	for _, op := range allowed {valid[op]=true}
	w := downstream
	if wrapped { w = middleware.NewWrapResponseWriter(w, proto) }
	for _, op := range trace {
		if !valid[op] { return observation{}, fmt.Errorf("invalid action %s in %s",op,name) }
		if err := action(w, op); err != nil {return observation{}, err}
	}
	o := observation{Status:-1,Bytes:-1,Code:recorder.Code,Body:recorder.Body.String(),Flushes:recorder.flushes}
	if wrapped {
		observed, ok := w.(middleware.WrapResponseWriter)
		if !ok {return observation{},errors.New("not a native wrapper")}
		o.Status = observed.Status()
		o.Bytes = observed.BytesWritten()
	}
	return o,nil
}

func withSuffix(prefix, suffix []string) []string {
	result := append([]string{}, prefix...)
	return append(result, suffix...)
}

func checkWitness(name string, w witness) error {
	_, _, _, actions, err := transport(name)
	if err != nil {return err}
	suffixes := [][]string{{}}
	for _, op := range actions {suffixes=append(suffixes,[]string{op})}
	observablyDifferent := false
	for i, suffix := range suffixes {
		first := withSuffix(w.First, suffix)
		second := withSuffix(w.Second, suffix)
		a, err := native(name,first,false)
		if err != nil {return fmt.Errorf("reference first %v: %w",first,err)}
		b, err := native(name,second,false)
		if err != nil {return fmt.Errorf("reference second %v: %w",second,err)}
		if !reflect.DeepEqual(a,b) {
			return fmt.Errorf("FORGED_REFERENCE_EQUIVALENCE: %v vs %v suffix %v",w.First,w.Second,suffix)
		}
		c, err := native(name,first,true)
		if err != nil {return err}
		d, err := native(name,second,true)
		if err != nil {return err}
		if !reflect.DeepEqual(c,d) {observablyDifferent=true}
		if i == 0 && (!reflect.DeepEqual(w.RefFirst,a) || !reflect.DeepEqual(w.RefSecond,b) ||
			!reflect.DeepEqual(w.WrapFirst,c) || !reflect.DeepEqual(w.WrapSecond,d)) {
			return fmt.Errorf("FORGED_RECORDED_SNAPSHOT: %v vs %v",w.First,w.Second)
		}
	}
	if !observablyDifferent {
		return fmt.Errorf("FORGED_DIFFERENCE: subject never separates %v vs %v",w.First,w.Second)
	}
	return nil
}

func main() {
	input := flag.String("input","","generated witness JSON to verify independently")
	flag.Parse()
	if *input == "" {fmt.Fprintln(os.Stderr,"--input required");os.Exit(2)}
	data,err := os.ReadFile(*input)
	if err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)}
	var r report
	if err=json.Unmarshal(data,&r);err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)}
	if r.Schema!="mgcheck.http-writer-protocol-future-quotient.v1" || r.Injected || r.Mode!="native" {
		fmt.Fprintln(os.Stderr,"REFUSE_UNTRUSTED_PROTOCOL_OR_INJECTED_DATA")
		os.Exit(2)
	}
	checked:=0
	for _,f := range r.Families {
		if f.Violations>0 && len(f.Witnesses)==0 {
			fmt.Fprintln(os.Stderr,"violations claimed without witness")
			os.Exit(3)
		}
		for _,w := range f.Witnesses {
			if err:=checkWitness(f.Carrier,w);err!=nil {
				fmt.Fprintln(os.Stderr,err)
				os.Exit(3)
			}
			checked++
		}
	}
	fmt.Printf("INDEPENDENT_NATIVE_REPLAY_VERIFIED=%d\n",checked)
	fmt.Println("BOUNDARY=claimed witnesses only; not exhaustive verification or source pin enforcement")
}
