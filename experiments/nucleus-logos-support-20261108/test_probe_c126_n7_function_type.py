"""The C126 source-native trace parser must reject unqualified observations."""

import unittest

from probe_c126_n7_function_type import (
    parse_traces, summarize_owner_traces, parse_app_edges, parse_arg_obligations,
    parse_conversion_stages, parse_inner_arg_edges, parse_c133_stages,
    parse_c134_owner_traces, parse_c135_trials, parse_c136_routes,
    parse_c137_worklist, parse_c138_deferred_route, parse_c139_value_comparison,
    parse_c140_rhs_exposure, parse_c141_cache_provenance,
)


class C126TraceTests(unittest.TestCase):
    def test_exact_source_site_and_two_budget_outcomes(self):
        sample = (
            "NUCLEUS_C126_N7_HEAD:application=8835:function=8805:argument=8834:"
            "before=65000:after=64000:context=0:pi_head=false:type_proven=false:"
            "type=Unknown\n"
            "NUCLEUS_C126_N7_HEAD:application=8835:function=8805:argument=8834:"
            "before=14000000:after=13900000:context=0:pi_head=true:type_proven=true:"
            "type=Proven\n"
        ).encode()
        result = parse_traces(sample)
        self.assertEqual(len(result), 2)
        self.assertEqual([row["pi_head"] for row in result], [False, True])
        self.assertEqual([row["charged"] for row in result], [1000, 100000])

    def test_wrong_source_site_is_rejected(self):
        invalid = (
            "NUCLEUS_C126_N7_HEAD:application=8835:function=8806:argument=8834:"
            "before=100:after=50:context=0:pi_head=false:type_proven=false:type=Unknown\n"
        ).encode()
        with self.assertRaises(AssertionError):
            parse_traces(invalid)

    def test_owner_summary_keeps_resource_counters_separate_from_typing(self):
        sample = (
            "NUCLEUS_C97_OWNER:start=1000:spent=300:major_work=200:loops=45:"
            "unique_node_env=20:repeat_node_env=5:unique_head_pending=15:repeat_head_pending=3\n"
            "NUCLEUS_C97_OWNER:start=2000:spent=100:major_work=80:loops=12:"
            "unique_node_env=10:repeat_node_env=2:unique_head_pending=8:repeat_head_pending=1\n"
            "NUCLEUS_NESTED_REPLAY_FAILURE:depth=2:head=NameId(147):major=Unknown\n"
        ).encode()
        summary = summarize_owner_traces(sample)
        self.assertEqual(summary["c97_total_spent"], 400)
        self.assertEqual(summary["c97_max_spent"], 300)
        self.assertEqual(summary["c97_repeated_node_env"], 7)
        self.assertEqual(summary["c97_repeated_head_pending"], 4)
        self.assertEqual(summary["counts"]["NUCLEUS_NESTED_REPLAY_FAILURE"], 1)

    def test_app_chain_cannot_invent_or_change_a_source_edge(self):
        source = {8805: {"fn": 8753, "arg": 8804}}
        valid = ("NUCLEUS_C129_APP_EDGE:app=8805:fun=8753:arg=8804:"
                 "before=65500:after=65400:context=0:pi_head=false:type_proven=false\n")
        result = parse_app_edges(valid.encode(), source)
        self.assertEqual(result[0]["charged"], 100)
        self.assertEqual(result[0]["app"], 8805)
        with self.assertRaises(AssertionError):
            parse_app_edges(valid.replace("arg=8804", "arg=8803").encode(), source)

    def test_app_argument_obligation_must_match_source_and_charge(self):
        sample = ("NUCLEUS_C130_APP_ARG:app=8805:fun=8753:arg=8804:"
                  "before=65500:after=65260:context=0:state=UNKNOWN:"
                  "judgment=Unknown { residual: ResidualId(\"unresolved-qualified-recursor-heads\") }\n")
        result = parse_arg_obligations(sample.encode(),
                                       {8805: {"fn": 8753, "arg": 8804}})
        self.assertEqual(result[0]["charged"], 240)
        self.assertEqual(result[0]["state"], "UNKNOWN")
        with self.assertRaises(AssertionError):
            parse_arg_obligations(sample.replace("fun=8753", "fun=8752").encode(),
                                  {8805: {"fn": 8753, "arg": 8804}})

    def test_c131_argument_inference_and_conversion_are_independent_stages(self):
        sample = (
            "NUCLEUS_C131_ARG_INFER:expr=8804:context=0:frame=11:before=65534:"
            "after=65332:state=PROVEN:inferred=Proven { value: Term(Closure(...)) }:"
            "expected=Term(Closure(...))\n"
            "NUCLEUS_C131_ARG_CONVERT:expr=8804:context=0:frame=11:fuel=65332:"
            "state=UNKNOWN:judgment=Unknown { residual: unresolved-qualified-recursor-heads }\n"
        ).encode()
        stages = parse_conversion_stages(sample, {8805: {"fn": 8753, "arg": 8804}})
        self.assertEqual([row["stage"] for row in stages], ["infer", "convert"])
        self.assertEqual([row["state"] for row in stages], ["PROVEN", "UNKNOWN"])
        self.assertEqual(stages[0]["charged"], 202)
        self.assertEqual(stages[1]["fuel"], 65332)
        with self.assertRaises(AssertionError):
            parse_conversion_stages(sample.replace(b"expr=8804", b"expr=8803"),
                                    {8805: {"fn": 8753, "arg": 8804}})

    def test_c131_inference_unknown_does_not_fabricate_conversion(self):
        sample = (
            "NUCLEUS_C131_ARG_INFER:expr=8804:context=0:frame=11:before=65534:"
            "after=65332:state=UNKNOWN:inferred=Unknown { residual: type-head }:"
            "expected=Term(Closure(...))\n"
        ).encode()
        stages = parse_conversion_stages(sample, {8805: {"fn": 8753, "arg": 8804}})
        self.assertEqual(len(stages), 1)
        self.assertEqual(stages[0]["stage"], "infer")
        self.assertEqual(stages[0]["state"], "UNKNOWN")

    def test_c132_inner_argument_edges_are_source_checked(self):
        source = {8753: {"fn": 8750, "arg": 8752},
                  8804: {"fn": 8753, "arg": 8803}}
        sample = (
            "NUCLEUS_C132_APP_ARG:app=8753:fun=8750:arg=8752:context=0:"
            "before=65500:after=65470:state=PROVEN:judgment=Proven { value: () }\n"
            "NUCLEUS_C132_APP_ARG:app=8804:fun=8753:arg=8803:context=0:"
            "before=65470:after=65280:state=UNKNOWN:judgment=Unknown { residual: x }\n"
        ).encode()
        result = parse_inner_arg_edges(sample, source)
        self.assertEqual([item["app"] for item in result], [8753, 8804])
        self.assertEqual([item["state"] for item in result], ["PROVEN", "UNKNOWN"])
        with self.assertRaises(AssertionError):
            parse_inner_arg_edges(sample.replace(b"arg=8803", b"arg=8802"), source)

    def test_c133_exact_inner_arg_inference_before_conversion(self):
        source = {8803: {"fn": 8802, "arg": 1477}}
        sample = (
            "NUCLEUS_C133_ARG_INFER:expr=1477:context=0:frame=0:before=65282:"
            "after=65281:state=PROVEN:inferred=Proven { value: Term(Closure(...)) }:"
            "expected=Term(Closure(...))\n"
            "NUCLEUS_C133_ARG_CONVERT:expr=1477:context=0:frame=0:fuel=65281:"
            "state=UNKNOWN:judgment=Unknown { residual: unresolved-qualified-recursor-heads }\n"
        ).encode()
        rows = parse_c133_stages(sample, source)
        self.assertEqual([r["state"] for r in rows], ["PROVEN", "UNKNOWN"])
        self.assertEqual(rows[0]["charged"], 1)
        self.assertEqual(rows[1]["stage"], "convert")
        with self.assertRaises(AssertionError):
            parse_c133_stages(sample.replace(b"expr=1477", b"expr=1478"), source)

    def test_c134_recursor_obligation_has_exact_captured_owner(self):
        sample = (
            "NUCLEUS_C134_RECURSOR:budget=64000:depth=0:left_spine=5:"
            "right_spine=4:left=Const(NameId(40)):right=Const(NameId(41))\n"
            "NUCLEUS_C134_OWNER:actual=110:actual_env=66182:expected=1:"
            "expected_env=66180:budget=65264:outcome=UNKNOWN\n"
        ).encode()
        rows = parse_c134_owner_traces(sample)
        self.assertEqual(rows["owner"][0]["outcome"], "UNKNOWN")
        self.assertEqual(rows["recursor"][0]["left_spine"], 5)
        with self.assertRaises(AssertionError):
            parse_c134_owner_traces(sample.replace(b"actual_env=66182", b"actual_env=66181"))

    def test_c135_recursor_trial_preserves_reserved_budget_and_result(self):
        sample = (
            'NUCLEUS_C135_RECURSOR_TRIAL:side=right:probe=32625:'
            'remaining_after_reservation=32625:outcome=UNKNOWN:'
            'obstruction=ResidualId("recursor-unresolved")\n'
            'NUCLEUS_C135_RECURSOR_TRIAL:side=right:probe=7077752:'
            'remaining_after_reservation=7077752:outcome=PROVEN:obstruction=\n'
        ).encode()
        rows = parse_c135_trials(sample)
        self.assertEqual([r['outcome'] for r in rows], ['UNKNOWN', 'PROVEN'])
        self.assertEqual([r['probe'] for r in rows], [32625, 7077752])
        with self.assertRaises(AssertionError):
            parse_c135_trials(sample.replace(b'side=right', b'side=left', 1))

    def test_c136_only_exact_owner_route_stages(self):
        sample = (
            'NUCLEUS_C136_ROUTE:event=pop:remaining=65264\n'
            'NUCLEUS_C136_ROUTE:event=cheap-exposure-attempted:remaining=65250\n'
            'NUCLEUS_C136_ROUTE:event=cheap-comparison-proven:remaining=14155000\n'
        ).encode()
        rows = parse_c136_routes(sample)
        self.assertEqual([r['event'] for r in rows],
                         ['pop', 'cheap-exposure-attempted', 'cheap-comparison-proven'])
        with self.assertRaises(AssertionError):
            parse_c136_routes(sample.replace(b'event=pop', b'event=made-up', 1))

    def test_c137_worklist_keeps_source_closures_and_frames_distinct(self):
        sample = (
            'NUCLEUS_C137_WORK:pop=0:remaining=65264:depth=0:pending=0:'
            'left=Expr110@Env66182@Levels[]:right=Expr1@Env66180@Levels[]\n'
            'NUCLEUS_C137_WORK:pop=1:remaining=65260:depth=1:pending=2:'
            'left=Expr42@Env90@Levels[]:right=Expr55@Env91@Levels[]\n'
        ).encode()
        rows = parse_c137_worklist(sample)
        self.assertEqual([r['pop'] for r in rows], [0, 1])
        self.assertEqual(rows[1]['pending'], 2)
        self.assertEqual(rows[0]['left'], 'Expr110@Env66182@Levels[]')
        with self.assertRaises(AssertionError):
            parse_c137_worklist(sample.replace(b'Env66182', b'Env66181', 1))

    def test_c138_only_second_deferred_obligation_with_explicit_outcome(self):
        sample = (
            'NUCLEUS_C138_DEFERRED:event=pop:remaining=65255\n'
            'NUCLEUS_C138_DEFERRED:event=cheap-exposure-attempted:remaining=65254\n'
            'NUCLEUS_C138_DEFERRED:event=cheap-exposure-status:'
            'remaining=65254:left=PROVEN:right=UNKNOWN\n'
            'NUCLEUS_C138_DEFERRED:event=cheap-exposure-unknown:remaining=65254\n'
        ).encode()
        route = parse_c138_deferred_route(sample)
        self.assertEqual([r['event'] for r in route],
                         ['pop', 'cheap-exposure-attempted',
                          'cheap-exposure-status', 'cheap-exposure-unknown'])
        self.assertEqual(route[2]['right'], 'UNKNOWN')
        with self.assertRaises(AssertionError):
            parse_c138_deferred_route(sample.replace(b'event=pop', b'event=bogus', 1))
        with self.assertRaises(AssertionError):
            parse_c138_deferred_route(sample.replace(b'right=UNKNOWN', b'right=FALSE', 1))

    def test_c139_preserves_exposed_value_kinds_and_checked_head_outcomes(self):
        sample = (
            'NUCLEUS_C139_COMPARE:stage=enter:budget=65250:depth=0:'
            'left=NeutralConst169L0A0:right=NeutralConst147L1A5\n'
            'NUCLEUS_C139_COMPARE:stage=neutral-head-UNKNOWN:budget=65250:depth=0:'
            'left=NeutralConst169L0A0:right=NeutralConst147L1A5\n'
            'NUCLEUS_C139_COMPARE:stage=recursor-trial-UNKNOWN:budget=32625:depth=0:'
            'left=NeutralConst169L0A0:right=NeutralConst147L1A5\n'
        ).encode()
        rows = parse_c139_value_comparison(sample)
        self.assertEqual([r['stage'] for r in rows],
                         ['enter', 'neutral-head-UNKNOWN', 'recursor-trial-UNKNOWN'])
        self.assertEqual(rows[0]['right'], 'NeutralConst147L1A5')
        with self.assertRaises(AssertionError):
            parse_c139_value_comparison(sample.replace(b'budget=65250', b'budget=0', 1))
        with self.assertRaises(AssertionError):
            parse_c139_value_comparison(sample.replace(b'neutral-head-UNKNOWN', b'neutral-head-MAYBE'))

    def test_c140_exact_rhs_demand_work_retains_counter_boundaries(self):
        good = ('NUCLEUS_C140_RHS:source=8799:env=0:budget=65250:'
                'outcome=PROVEN:head=Const147:arity=5:steps=520:'
                'recursor_calls=3:key_work=1024\n').encode()
        rows = parse_c140_rhs_exposure(good)
        self.assertEqual(rows[0]['steps'], 520)
        self.assertEqual(rows[0]['head'], 'Const147')
        with self.assertRaises(AssertionError):
            parse_c140_rhs_exposure(good.replace(b'source=8799', b'source=8798'))
        with self.assertRaises(AssertionError):
            parse_c140_rhs_exposure(good.replace(b'recursor_calls=3', b'recursor_calls=-1'))

    def test_c141_cache_receipt_requires_exact_qualified_key(self):
        good = (
            'NUCLEUS_C141_CACHE:event=lookup-miss:source=8799:env=0:'
            'levels=0:authority=21:transparency=Reducible:pending=0:'
            'preserve=true:digest=123:scope=false:budget=12000:'
            'head=None:published=false\n'
            'NUCLEUS_C141_CACHE:event=publication:source=8799:env=0:'
            'levels=0:authority=21:transparency=Reducible:pending=0:'
            'preserve=true:digest=123:scope=false:budget=12000:'
            'head=Const169A0:published=true\n'
            'NUCLEUS_C141_CACHE:event=lookup-hit:source=8799:env=0:'
            'levels=0:authority=21:transparency=Reducible:pending=0:'
            'preserve=true:digest=123:scope=true:budget=14155490:'
            'head=Const169A0:published=true\n'
        ).encode()
        rows = parse_c141_cache_provenance(good)
        self.assertEqual([r['event'] for r in rows],
                         ['lookup-miss', 'publication', 'lookup-hit'])
        self.assertEqual(len({r['digest'] for r in rows}), 1)
        self.assertEqual(rows[-1]['scope'], True)
        self.assertEqual(rows[-1]['head'], 'Const169A0')
        for old, new in ((b'source=8799', b'source=8798'),
                         (b'pending=0', b'pending=1'),
                         (b'preserve=true', b'preserve=false'),
                         (b'levels=0', b'levels=1'),
                         (b'published=true', b'published=maybe')):
            with self.subTest(field=old):
                with self.assertRaises(AssertionError):
                    parse_c141_cache_provenance(good.replace(old, new, 1))


if __name__ == "__main__":
    unittest.main()
