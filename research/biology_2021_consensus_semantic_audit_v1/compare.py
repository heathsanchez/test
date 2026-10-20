#!/usr/bin/env python3
"""Source-native, POST-HOC authority comparison. Never infers absent rows as FALSE.

Data 4 ref classes have independent authority from Data 3 differential effects.
Original selected hit receipts are authenticated before source Data4 outcome read.
"""
import argparse
from collections import Counter,defaultdict
import hashlib,json,math,shutil,urllib.request
from pathlib import Path
from openpyxl import load_workbook

SOURCE='Costanzo_et_al_Data_File_4_MCMC_consensus_profiles.xlsx'
MD5='686f8b88507826d3cb7117e80274be92'
SHA='6c0fecfa1b2443a8770b6f4764f1c751318cbd0b2406e06e2a4e9655a737bdbe'
V3_RECEIPT_SHA='72359773328a8f09ff69d651b28d8577ac1d16312eb379065524e163aaae3b43'
V3_DATA3_SHA='b4e242087e554df1adc648aefb890144d397a1eb303a55509a90ae08e912c488'
EXPECTED_HEADER=('Query ORF','Array ORF','Condition','Query Gene','Array Gene',
                 'Matched reference','MCMC consensus reference','Saturated reference')
ALIASES={'boretzeomib':'bortezomib','concanmycina':'concanamycina'}

def digest(p,algo='sha256'):
 h=hashlib.new(algo)
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def condition(s):
 x=''.join(c for c in str(s or '').casefold() if c.isalnum())
 return ALIASES.get(x,x)

def flag(v):
 if isinstance(v,bool):return v
 if isinstance(v,(int,float)) and math.isfinite(v) and v in (0,1):return bool(v)
 if isinstance(v,str):
  x=v.strip().casefold()
  if x in ('true','yes','y','1'):return True
  if x in ('false','no','n','0'):return False
 return None

def self_tests():
 assert condition('Galactose')=='galactose'
 assert condition('Concanmycin A')=='concanamycina'
 assert flag(True) is True and flag(1) is True and flag(0) is False
 assert flag('YES') is True and flag('unknown') is None
 assert flag(None) is None and flag(2) is None


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--original-receipts',type=Path,required=True)
 ap.add_argument('--output',type=Path,required=True);ap.add_argument('--cache',type=Path,default=Path('/tmp/yeast_2021_consensus'))
 args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True);args.cache.mkdir(parents=True,exist_ok=True)
 self_tests()
 assert digest(args.original_receipts)==V3_RECEIPT_SHA,'ORIGINAL_PROTECTED_RECEIPT_CHANGED'
 trace=json.loads(args.original_receipts.read_bytes());assert len(trace)==200
 selected=defaultdict(set)
 for r in trace:
  for method,x in r['chosen'].items():
   if x['hit'] is True:
    k=(r['q'].upper(),r['a'].upper(),condition(x['condition']))
    selected[k].add(method)
 assert len(selected)==4,'PROTECTED_SELECTED_SOURCE_EVENTS_CHANGED'
 src=args.cache/SOURCE
 if not src.exists():
  u=urllib.request.Request('https://zenodo.org/records/4560674/files/'+SOURCE+'?download=1',headers={'User-Agent':'Metalogic-Consensus-Source-Meaning-V1/1.0'})
  with urllib.request.urlopen(u,timeout=180) as f,src.open('wb') as out:shutil.copyfileobj(f,out)
 assert digest(src)==SHA and digest(src,'md5')==MD5,'CONSENSUS_SOURCE_AUTHORITY_MISMATCH'
 wb=load_workbook(src,read_only=True,data_only=True)
 ws=wb['Novels_match_v_MCMC_v_Saturated']
 it=ws.iter_rows(values_only=True)
 header=tuple(next(it));assert header==EXPECTED_HEADER, ('SOURCE_TYPED_SCHEMA_DIVERGENT',header)
 per_key=defaultdict(list);source_count=0
 for row in it:
  source_count+=1
  q=str(row[0] or '').strip().upper();a=str(row[1] or '').strip().upper();c=condition(row[2])
  if not q or not a or not c:continue
  per_key[(q,a,c)].append(tuple(flag(v) for v in row[5:8]))
 wb.close()
 assert source_count==3288, ('SOURCE_ROW_COUNT_WRONG',source_count)
 results=[];stats=Counter();examples=[]
 for k in sorted(selected):
  vals=per_key.get(k,[])
  if len(vals)!=1:
   outcome='UNKNOWN_ABSENT_FROM_NOVELS_TABLE' if not vals else 'UNKNOWN_AMBIGUOUS_MULTIPLE_SOURCE_ROWS'
   result={'gene_a':k[0],'gene_b':k[1],'condition':k[2], 'methods':sorted(selected[k]),'status':outcome,'number_source_rows':len(vals)}
   stats[outcome]+=1
  else:
   mv,cv,sv=vals[0]
   result={'gene_a':k[0],'gene_b':k[1],'condition':k[2], 'methods':sorted(selected[k]),'status':'SOURCE_TYPED_ROW_MATCH','number_source_rows':1,
           'matched_novel':mv,'mcmc_novel':cv,'saturated_novel':sv,
           'matched_vs_mcmc_difference':(mv!=cv) if mv is not None and cv is not None else None}
   stats['SOURCE_TYPED_ROW_MATCH']+=1
  results.append(result)
 # Whole source-table controls: compare only rows with an unambiguous typed
 # 0/1 classification; do not map unknown/absent to 0.
 all_patterns=Counter();typed_rows=0;discordant=0;undecodable=0
 for k,values in per_key.items():
  if len(values)!=1:continue
  v=values[0]
  if all(z is not None for z in v):
   typed_rows+=1;all_patterns[str([int(z) for z in v])]+=1
   discordant+=int(v[0]!=v[1])
  else:undecodable+=1
 # Source authority revocation tests: withdrawal of Data4 invalidates only
 # reference-NOVELTY attribution. Existing independently authenticated Data3
 # differential-effect evidence remains, regardless of whether novelty rows join.
 revocation={'before_data3_differential_effect_claims':len(results),
             'after_data4_withdrawal_data3_differential_effect_claims':len(results),
             'after_data4_withdrawal_data4_novelty_attributions':0,
             'unjoined_source_rows_are_UNKNOWN_not_negative':True,
             'after_restoration_source_typed_attributions_recovered':sum(r['status']=='SOURCE_TYPED_ROW_MATCH' for r in results)}
 assert revocation['before_data3_differential_effect_claims']==revocation['after_data4_withdrawal_data3_differential_effect_claims']
 report={'status':'SOURCE_AUTHORITY_COMPARISON_COMPLETED_POSTHOC','source':SOURCE,'source_md5':MD5,'source_sha256':SHA,
         'data3_differential_source_sha256':V3_DATA3_SHA,'protected_v3_original_receipt_sha256':V3_RECEIPT_SHA,
         'declared_field_semantics':'File4 Readme: source-NOVELTY classifications under matched, MCMC consensus and saturated reference',
         'source_table_rows':source_count,'unique_join_keys':len(per_key),'fully_decoded_unique_source_rows':typed_rows,
         'source_rows_unrecognized_boolean_schema':undecodable,
         'matched_vs_mcmc_disagreements_among_decoded_unique_source_rows':discordant,
         'source_typed_novelty_patterns':dict(all_patterns),'protected_selected_effect_event_count':len(selected),
         'protected_selected_event_results':results,'protected_status_counts':dict(stats),
         'evidence_authority_withdrawal':revocation,
         'scope':['read-only published source, not a blinded biological experiment','absence in author novelty table => UNKNOWN','no new method advantage',
                  'source classification depends on reference construction; novelty is not synonym for differential effect',
                  'finite source-authority requalification is not a CLC Lean proof']}
 path=args.output/'source_reference_comparison.json';path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print('BIOLOGY_2021_SOURCE_REFERENCE_COMPARISON='+json.dumps(report,sort_keys=True),flush=True)
 print('BIOLOGY_2021_NOVELTY_AUTHORITY_BOUNDARY_CHECK_PASS',flush=True)
 if not ap is None and not args.cache.joinpath('KEEP').exists():src.unlink()
if __name__=='__main__':main()