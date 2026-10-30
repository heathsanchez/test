// Independent native verifier for source-adaptive cache probe records.
// It invokes the *same pinned library* via reflection, not the typed driver
// used to create the record. This validates trace observations, not semantics.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"reflect"
	"time"
)

type Grammar struct {
	Schema string `json:"schema"`
	Status string `json:"status"`
	HasClock bool `json:"has_clock"`
	WriteMethod string `json:"write_method"`
	ReadMethod string `json:"read_method"`
}

type Case struct {
	Name string `json:"name"`
	Actions []string `json:"actions"`
	Before bool `json:"before"`
	After bool `json:"after"`
	BeforeValue interface{} `json:"before_value"`
	AfterValue interface{} `json:"after_value"`
}

type Report struct {
	Schema string `json:"schema"`
	SourceSHA string `json:"source_sha"`
	GeneratedOperator string `json:"generated_operator"`
	Boundary string `json:"boundary"`
	Cases []Case `json:"cases"`
}

type expected struct { expiry time.Duration; wait bool }

func expectations() map[string]expected {
	return map[string]expected{
		"B0_api_only_short": {80*time.Millisecond,false},
		"candidate_ast_clock_derived": {80*time.Millisecond,true},
		"negative_no_expiry": {-1,false},
		"negative_no_expiry_elapsed": {-1,true},
		"negative_no_elapse": {80*time.Millisecond,false},
		"B1_manual_time_aware_direct": {80*time.Millisecond,true},
	}
}

func replay(g Grammar, e expected) (Case,error) {
	obj:=reflect.ValueOf(construct())
	set:=obj.MethodByName(g.WriteMethod)
	get:=obj.MethodByName(g.ReadMethod)
	if !set.IsValid() || !get.IsValid() {return Case{},fmt.Errorf("missing native method")}
	set.Call([]reflect.Value{reflect.ValueOf("k"),reflect.ValueOf("v"),reflect.ValueOf(e.expiry)})
	first:=get.Call([]reflect.Value{reflect.ValueOf("k")})
	if len(first)!=2 {return Case{},fmt.Errorf("read arity changed")}
	if e.wait {time.Sleep(300*time.Millisecond)}
	second:=get.Call([]reflect.Value{reflect.ValueOf("k")})
	actions:=[]string{"WRITE(k,v,expiry)","READ(k)"}
	if e.wait {actions=append(actions,"ELAPSE(300ms)")}
	actions=append(actions,"READ(k)")
	return Case{Actions:actions,Before:first[1].Bool(),After:second[1].Bool(),BeforeValue:first[0].Interface(),AfterValue:second[0].Interface()},nil
}

func require(ok bool, message string){if !ok {fmt.Fprintln(os.Stderr,"REPLAY_REJECTED_"+message);os.Exit(1)}}

func main(){
	manifest:=flag.String("manifest","","source grammar JSON")
	reportPath:=flag.String("report","","typed native observations JSON")
	sha:=flag.String("expect-sha","","exact pinned source SHA")
	flag.Parse()
	var g Grammar
	buf,err:=os.ReadFile(*manifest);if err!=nil{panic(err)}
	if err:=json.Unmarshal(buf,&g);err!=nil{panic(err)}
	require(g.Schema=="mathgraph.g3.source-adaptive-grammar.v1" && g.Status=="CANDIDATE_SIGNATURE_BRIDGE" && g.HasClock,"GRAMMAR")
	var r Report
	buf,err=os.ReadFile(*reportPath);if err!=nil{panic(err)}
	if err:=json.Unmarshal(buf,&r);err!=nil{panic(err)}
	require(r.Schema=="mathgraph.g3.native-cache-grammar-probe.v1","SCHEMA")
	require(*sha!="" && r.SourceSHA==*sha,"SOURCE_SHA")
	require(r.GeneratedOperator=="ELAPSE" && r.Boundary=="SOURCE_ADAPTIVE_BUT_PREPROGRAMMED_TEMPLATE","OPERATOR_BOUNDARY")
	e:=expectations()
	require(len(r.Cases)==len(e),"CASE_COUNT")
	seen:=map[string]bool{}
	actuals:=map[string]Case{}
	for _,c:=range r.Cases {
		config,exists:=e[c.Name]
		require(exists && !seen[c.Name],"CASE_NAME")
		seen[c.Name]=true
		actual,err:=replay(g,config);if err!=nil{panic(err)}
		actual.Name=c.Name
		require(reflect.DeepEqual(c,actual),"OBSERVATION_OR_TRACE_"+c.Name)
		actuals[c.Name]=actual
	}
	// Native behavioral controls. These rules were hypothesized before source.
	b0:=actuals["B0_api_only_short"]
	p:=actuals["candidate_ast_clock_derived"]
	noExpiry:=actuals["negative_no_expiry_elapsed"]
	noWait:=actuals["negative_no_elapse"]
	b1:=actuals["B1_manual_time_aware_direct"]
	require(b0.Before&&b0.After,"BASELINE_IMMEDIATE")
	require(p.Before&&!p.After,"TIME_EXPIRED")
	require(noExpiry.Before&&noExpiry.After,"NONEXPIRING_CONTROL")
	require(noWait.Before&&noWait.After,"ZERO_ELAPSE_CONTROL")
	require(reflect.DeepEqual(p.BeforeValue,b1.BeforeValue)&&reflect.DeepEqual(p.AfterValue,b1.AfterValue)&&p.Before==b1.Before&&p.After==b1.After,"FAIR_B1_PARITY")
	fmt.Printf("SOURCE_NATIVE_REPLAY_ACCEPTED=%d\n",len(seen))
	fmt.Println("API_ONLY_OBSERVATION=present_then_present")
	fmt.Println("AST_CLOCK_ADDED_ELAPSE=present_then_expired")
	fmt.Println("FAIR_TIME_AWARE_DIRECT_BASELINE=TIE")
	fmt.Println("STRICT_G3=UNKNOWN_TEMPLATE_NOT_NEW_OPERATOR_INVENTION")
}
