// Source-independent native observation of finite in-process cache behavior.
// The target source supplies methods; the oracle supplies its own witnesses.
package main

import (
	"reflect"
	"os"
)

type Outcome struct {
	Status    string   `json:"status"`
	Steps     []string `json:"steps,omitempty"`
	UsedBuild bool     `json:"used_build"`
	Reason    string   `json:"reason,omitempty"`
}

var errorType = reflect.TypeOf((*error)(nil)).Elem()

func nilable(v reflect.Value) bool {
	switch v.Kind() {
	case reflect.Chan, reflect.Func, reflect.Interface, reflect.Map, reflect.Pointer, reflect.Slice:
		return true
	}
	return false
}

func nilObject(v reflect.Value) bool {
	return !v.IsValid() || (nilable(v) && v.IsNil())
}

func hasMethods(v reflect.Value) bool {
	return v.IsValid() && (v.MethodByName("Set").IsValid() || v.MethodByName("Add").IsValid()) && v.MethodByName("Get").IsValid()
}

func witness(raw string, target reflect.Type) (reflect.Value, bool) {
	v := reflect.ValueOf(raw)
	if v.Type().AssignableTo(target) {
		return v, true
	}
	if v.Type().ConvertibleTo(target) && target.Kind() == reflect.String {
		return v.Convert(target), true
	}
	return reflect.Value{}, false
}

func callSet(v reflect.Value, key, value string) bool {
	if os.Getenv("MG_NO_MUTATOR") == "1" {
		return false
	}
	m := v.MethodByName("Set")
	if !m.IsValid() {
		m = v.MethodByName("Add")
	}
	if !m.IsValid() {
		return false
	}
	t := m.Type()
	if t.NumIn() != 2 && t.NumIn() != 3 {
		return false
	}
	keyArg, ok := witness(key, t.In(0))
	if !ok {
		return false
	}
	valueArg, ok := witness(value, t.In(1))
	if !ok {
		return false
	}
	args := []reflect.Value{keyArg, valueArg}
	if t.NumIn() == 3 && !t.IsVariadic() {
		last := t.In(2)
		if last.PkgPath() != "time" || last.Name() != "Duration" || last.Kind() != reflect.Int64 {
			return false
		}
		args = append(args, reflect.ValueOf(int64(-1)).Convert(last))
	}
	for _, returned := range m.Call(args) {
		if returned.Type().Implements(errorType) && (!nilable(returned) || !returned.IsNil()) {
			return false
		}
	}
	return true
}

func callGet(v reflect.Value, key string) (any, bool, bool) {
	m := v.MethodByName("Get")
	if !m.IsValid() {
		return nil, false, false
	}
	t := m.Type()
	if t.NumIn() < 1 || t.NumIn() > 2 || (t.NumIn() == 2 && !t.IsVariadic()) {
		return nil, false, false
	}
	arg, ok := witness(key, t.In(0))
	if !ok {
		return nil, false, false
	}
	values := m.Call([]reflect.Value{arg})
	if len(values) == 0 || len(values) > 2 {
		return nil, false, false
	}
	found := true
	if nilObject(values[0]) {
		found = false
	}
	if len(values) == 2 {
		second := values[1]
		switch {
		case second.Kind() == reflect.Bool:
			if !second.Bool() {
				found = false
			}
		case second.Type().Implements(errorType):
			if !nilable(second) || !second.IsNil() {
				found = false
			}
		default:
			return nil, false, false
		}
	}
	if !found {
		return nil, false, true
	}
	value := values[0]
	if dereferenced := value.MethodByName("Value"); dereferenced.IsValid() {
		sig := dereferenced.Type()
		if sig.NumIn() == 0 && sig.NumOut() == 1 {
			extracted := dereferenced.Call(nil)[0]
			return extracted.Interface(), true, true
		}
	}
	return value.Interface(), true, true
}

func callDelete(v reflect.Value, key string) bool {
	for _, name := range []string{"Remove", "Delete"} {
		m := v.MethodByName(name)
		if !m.IsValid() || m.Type().NumIn() != 1 {
			continue
		}
		arg, ok := witness(key, m.Type().In(0))
		if !ok {
			continue
		}
		for _, result := range m.Call([]reflect.Value{arg}) {
			if result.Type().Implements(errorType) && (!nilable(result) || !result.IsNil()) {
				return false
			}
		}
		return true
	}
	return false
}

func probe(instance any, allowBuild bool) (out Outcome) {
	out.Status = "UNKNOWN_NATIVE_TRACE"
	defer func() {
		if r := recover(); r != nil {
			out.Status = "UNKNOWN_NATIVE_PANIC"
			out.Reason = "target operation or reflection panicked"
		}
	}()
	v := reflect.ValueOf(instance)
	if nilObject(v) {
		out.Status = "UNKNOWN_NIL_CONSTRUCTOR"
		return
	}
	if !hasMethods(v) {
		if !allowBuild {
			out.Status = "UNKNOWN_NO_OPERATIONAL_REACHABILITY"
			return
		}
		build := v.MethodByName("Build")
		if !build.IsValid() || build.Type().NumIn() != 0 || build.Type().NumOut() != 1 {
			out.Status = "UNKNOWN_NO_OPERATIONAL_REACHABILITY"
			return
		}
		v = build.Call(nil)[0]
		out.UsedBuild = true
		if nilObject(v) || !hasMethods(v) {
			out.Status = "UNKNOWN_NO_OPERATIONAL_REACHABILITY"
			return
		}
	}
	key := "mathgraph-v4-probe-key-3b8e"
	before, found, ok := callGet(v, key)
	if !ok || found || before != nil {
		out.Status = "UNKNOWN_INITIAL_MISS"
		return
	}
	out.Steps = append(out.Steps, "initial_miss")
	if !callSet(v, key, "first") {
		out.Status = "UNKNOWN_SET"
		return
	}
	out.Steps = append(out.Steps, "set")
	value, found, ok := callGet(v, key)
	if !ok || !found || !reflect.DeepEqual(value, "first") {
		out.Status = "UNKNOWN_READBACK_MISMATCH"
		return
	}
	out.Steps = append(out.Steps, "readback")
	if !callSet(v, key, "second") {
		out.Status = "UNKNOWN_SET"
		return
	}
	out.Steps = append(out.Steps, "overwrite")
	value, found, ok = callGet(v, key)
	if !ok || !found || !reflect.DeepEqual(value, "second") {
		out.Status = "UNKNOWN_READBACK_MISMATCH"
		return
	}
	out.Steps = append(out.Steps, "readback_overwrite")
	if !callDelete(v, key) {
		out.Status = "UNKNOWN_DELETE"
		return
	}
	value, found, ok = callGet(v, key)
	if !ok || found || value != nil {
		out.Status = "UNKNOWN_POST_DELETE_MISS"
		return
	}
	out.Steps = append(out.Steps, "post_delete_miss")
	out.Status = "NATIVE_CACHE_TRACE_PASS"
	return
}
