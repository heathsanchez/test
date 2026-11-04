from pathlib import Path
import runpy,json
R=Path(__file__).resolve().parent;g=runpy.run_path(str(R/'hadd-subgoals.py'));g['emit']('left-sum-full',g['aa'][0],g['aa'][4],g['bb'][4],False);g['emit']('right-sum-full',g['aa'][0],g['aa'][5],g['bb'][5],False);(R/'hadd-subgoals-report.json').write_text(json.dumps(g['results'],indent=2))
s=(R/'check-reified.py').read_text().replace("(R/'reified').glob('pair-*')","(R/'hadd-subgoals').glob('*sum-full')").replace("R/'reified-verification.json'","R/'full-context-operands-verification.json'");(R/'check-full-context-operands.py').write_text(s)
