from pathlib import Path
import shutil,subprocess,difflib,hashlib,json
R=Path(__file__).resolve().parent;S=R/'retention-fees/metatron-kernel';shutil.copytree(R/'extracted/metatron-kernel',S,dirs_exist_ok=True);subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(R/'trace.patch')],cwd=S,check=True)
p=S/'src/diagnostics.rs';s=p.read_text();s+='''
thread_local!{static PAIR_FEES:Cell<[u64;5]>=const{Cell::new([0;5])};static PAIR_TRIALS:Cell<usize>=const{Cell::new(0)};}
pub(crate)fn capture_fee(cost:usize,growth:bool,paid:bool){if !receiver_target_active(){return}let mut s=PAIR_FEES.get();s[0]+=1;s[1]+=if paid{cost as u64}else{0};s[2]+=u64::from(paid);s[3]+=u64::from(growth);s[4]+=u64::from(!paid);PAIR_FEES.set(s);}
pub(crate)fn capture_fees()->[u64;5]{PAIR_FEES.get()}
pub(crate)fn capture_trial_event(args:std::fmt::Arguments<'_>){if receiver_target_active(){let n=PAIR_TRIALS.get();PAIR_TRIALS.set(n+1);if n<128{eprintln!("PAIR_RETENTION_TRIAL:{args}");}}}
pub(crate)struct ReceiverRetentionSummary(pub bool);impl Drop for ReceiverRetentionSummary{fn drop(&mut self){if self.0{eprintln!("PAIR_RETENTION_SUMMARY:attempts-paidsteps-inserts-growth-unaffordable={:?}:trials={}:diagnostic_only=true:no_semantic_change=true",PAIR_FEES.get(),PAIR_TRIALS.get());}}}
''';p.write_text(s)
p=S/'src/checker.rs';s=p.read_text();needle='''        crate::diagnostics::receiver_target(matches!(&declaration,Declaration::Theorem{name,..} if name.0==26089));''';assert s.count(needle)==1;s=s.replace(needle,needle+'''
        #[cfg(feature="diagnostics")]
        let _capture_fee_summary=crate::diagnostics::ReceiverRetentionSummary(matches!(&declaration,Declaration::Theorem{name,..} if name.0==26089));''');p.write_text(s)
p=S/'src/typecheck.rs';s=p.read_text();needle='''                    if *remaining>=cost { *remaining-=cost; proofs.insert(pair,(a.clone(),b.clone())); }''';assert s.count(needle)==1;s=s.replace(needle,'''                    #[cfg(feature="diagnostics")]
                    crate::diagnostics::capture_fee(cost,proofs.len()==proofs.capacity(),*remaining>=cost);
'''+needle);needle='    pub(crate) fn has_source_opening_proof(&self,body:&Closure,free:FreeId)->bool {';s=s.replace(needle,'''    #[cfg(feature="diagnostics")]
    pub(crate)fn diagnostic_capture_pair_occupancy(&self)->usize{self.source_capture_proofs.borrow().len()}

'''+needle);p.write_text(s)
p=S/'src/convert.rs';s=p.read_text();needle='''            if exact_neutral_source_congruence(checker, left_structure, right_structure, &mut source_work) {''';assert s.count(needle)==1;s=s.replace(needle,'''            #[cfg(feature="diagnostics")]
            let observation=(source_work,checker.diagnostic_capture_pair_occupancy(),crate::diagnostics::capture_fees());
            let exact_proved=exact_neutral_source_congruence(checker,left_structure,right_structure,&mut source_work);
            #[cfg(feature="diagnostics")]
            {let after=crate::diagnostics::capture_fees();let fees=after[1]-observation.2[1];let total=observation.0-source_work;crate::diagnostics::capture_trial_event(format_args!("before={}:after={source_work}:occupied_before={}:occupied_after={}:proved={exact_proved}:fees={fees}:mandatory={}:inserts={}:growth={}:unaffordable={}",observation.0,observation.1,checker.diagnostic_capture_pair_occupancy(),total.saturating_sub(fees as usize),after[2]-observation.2[2],after[3]-observation.2[3],after[4]-observation.2[4]));}
            if exact_proved {''');p.write_text(s)
B=R/'extracted/metatron-kernel';patch=''.join(''.join(difflib.unified_diff((B/rel).read_text().splitlines(True),(S/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))for rel in ['src/checker.rs','src/convert.rs','src/diagnostics.rs','src/typecheck.rs']);(R/'retention-fees.patch').write_text(patch)
s=(R/'run-envelope.py').read_text().replace("D=R/'envelope-replay'","D=R/'retention-fees-replay'").replace("source=R/'envelope/metatron-kernel'","source=R/'retention-fees/metatron-kernel'").replace("x.startswith('ENVELOPE_FEASIBILITY:')","x.startswith('PAIR_RETENTION_')");(R/'run-retention-fees.py').write_text(s);print(json.dumps(dict(patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),diagnostic_only=True,no_semantic_change=True)))
