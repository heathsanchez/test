from pathlib import Path

p = Path("rpc/http_test.go")
s = p.read_text()
a = s.index("func TestNewContextWithHeaders(")
b = s.index("\nfunc ", a + 5)
section = s[a:b]
old = '\t\t_, _ = writer.Write([]byte(`{}`))'
new = '''\t\tvar req struct { ID json.RawMessage `json:"id"` }
\t\tif err := json.NewDecoder(request.Body).Decode(&req); err != nil {
\t\t\tt.Errorf("decode request: %v", err)
\t\t\treturn
\t\t}
\t\t_, _ = fmt.Fprintf(writer, `{"jsonrpc":"2.0","id":%s}`, req.ID)'''
assert section.count(old) == 1, "expected exactly one legacy mock"
p.write_text(s[:a] + section.replace(old, new) + s[b:])
