#!/usr/bin/env python3
"""Round-trip nonempty sequence controls through real native Cyclone DDS RMW."""
import json
import resource
from rclpy.serialization import serialize_message,deserialize_message
from test_msgs.msg import Arrays, BoundedSequences, MultiNested, UnboundedSequences, WStrings, BasicTypes

a=BoundedSequences()
a.bool_values=[True, False]
a.int64_values=[0, -5]
a.string_values=["hello", "earth"]
a.basic_types_values=[BasicTypes()]
b=UnboundedSequences()
b.bool_values=[True, False, True]
b.int64_values=[-100, 100]
b.string_values=["hello", "world"]
b.basic_types_values=[BasicTypes()]
w=WStrings()
w.bounded_sequence_of_wstrings=["a", "世界"]
w.unbounded_sequence_of_wstrings=["hello", "B"]
m=MultiNested()
m.unbounded_sequence_of_arrays=[Arrays()]
m.bounded_sequence_of_arrays=[Arrays()]
samples=[a,b,w,m]
results=[]
for msg in samples:
    data=serialize_message(msg)
    out=deserialize_message(data,type(msg))
    assert out==msg, (type(msg).__name__, repr(out),repr(msg))
    results.append({"type":type(msg).__name__,"length":len(data),"outcome":"accepted"})
    print(json.dumps(results[-1]),flush=True)
print("POPULATED_CONTROLS_PASS",len(samples),
      "maxrss_kib",resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,flush=True)
