"""Stage optional geometry contact offset and independent tilt recovery; no live edit."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent;parent=root/'staged_initial_top_release';stage=root/'staged_contact_stability';stage.mkdir(exist_ok=True)
manifest=json.loads((parent/'MANIFEST.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in manifest['source_sha256'].items():assert sha(Path(p))==h,p
for n,h in manifest['candidate_sha256'].items():
 assert sha(parent/n)==h,n
 shutil.copy2(parent/n,stage/n)
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)
p=stage/'top_contact_bypass.py';s=p.read_text()
s=replace(s,'    confirm_terminal_release: bool=False','    tilt_recontact_rad: float=0.\n    confirm_terminal_release: bool=False')
s=replace(s,'        if self.confirm_terminal_release and not (self.guarded_descent and self.continuous_drag):',"        if not math.isfinite(self.tilt_recontact_rad) or not 0<=self.tilt_recontact_rad<=.10:\n            raise ValueError('Tilt recovery threshold must be0..0.10rad')\n        if self.tilt_recontact_rad and not (self.guarded_descent and self.continuous_drag):\n            raise ValueError('Tilt recovery requires guarded continuous top route')\n        if self.confirm_terminal_release and not (self.guarded_descent and self.continuous_drag):")
s=replace(s,'        if position_ready and not guarded_this_step',"        if self.tilt_recontact_rad and self.top_mode in ('top_press','top_push') and tilt>self.tilt_recontact_rad:\n            guarded_this_step=True\n            self._start_recontact(tip,'incipient_tilt_independent')\n        if position_ready and not guarded_this_step")
s=replace(s,'return dict(terminal_position_confirmed=position_ready','return dict(tilt_recontact_threshold_rad=self.tilt_recontact_rad,terminal_position_confirmed=position_ready')
p.write_text(s)
p=stage/'collect_paired_sorting.py';s=p.read_text()
s=replace(s,"parser.add_argument('--expert-initial-top-route'","parser.add_argument('--expert-front-contact-inset-fraction', type=float, default=None, help='Diagnostic optional front-route contact inset fraction0.5..1; non-front contact unchanged.')\nparser.add_argument('--expert-top-tilt-recontact-rad', type=float, default=0., help='Diagnostic independent top tilt withdrawal threshold0..0.10rad, zero disabled; original0.20rad pose gate unchanged.')\nparser.add_argument('--expert-initial-top-route'")
s=replace(s,'\nif args.expert_initial_top_route and not',"\nif args.expert_front_contact_inset_fraction is not None and (not .5<=args.expert_front_contact_inset_fraction<=1 or not args.expert_front_top_route or not args.expert_top_projected_support or args.role!='diagnostic'):\n    parser.error('Front contact fraction requires diagnostic projected front route and0.5..1 bound')\nif not 0<=args.expert_top_tilt_recontact_rad<=.10 or (args.expert_top_tilt_recontact_rad and not (args.role=='diagnostic' and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag)):\n    parser.error('Tilt recovery requires diagnostic projected guarded continuous top route and0..0.10rad')\nif args.expert_initial_top_route and not")
s=replace(s,"                frontal_plan['confirmed_terminal_release']", "                if front_route_selected and args.expert_front_contact_inset_fraction is not None:\n                    effective_top_fraction = args.expert_front_contact_inset_fraction\n                frontal_plan['contact_stability_candidate'] = dict(front_contact_inset_fraction=args.expert_front_contact_inset_fraction,applied_front_override=bool(front_route_selected and args.expert_front_contact_inset_fraction is not None),tilt_recontact_rad=args.expert_top_tilt_recontact_rad,original_pose_max_tilt_rad=.20)\n                frontal_plan['confirmed_terminal_release']")
s=replace(s,'**top_extra,confirm_terminal_release=', '**top_extra,tilt_recontact_rad=args.expert_top_tilt_recontact_rad,confirm_terminal_release=')
p.write_text(s)
manifest['candidate_sha256']={p.name:sha(p) for p in stage.glob('*.py')};manifest['scope']='Isolated diagnostic candidate: optional front-only inset, independent tilt recovery, confirmed release, initial top. Defaults preserve previous behavior. No physical proof.'
(stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
s=(root/'run_staged_initial_top_tests.py').read_text().replace("stage=root/'staged_initial_top_release'","stage=root/'staged_contact_stability'").replace("'test_staged_initial_top']","'test_staged_initial_top','test_staged_contact_stability']")
(root/'run_staged_contact_stability_tests.py').write_text(s)
s=(root/'check_staged_initial_top_factory.py').read_text().replace("stage=root/'staged_initial_top_release'","stage=root/'staged_contact_stability'")
s=s.replace("'--expert-initial-top-route']","'--expert-initial-top-route','--expert-front-contact-inset-fraction','.7','--expert-top-tilt-recontact-rad','.03']",1)
s=s.replace("('missing_guard',", "('bad_fraction',[('.49' if v=='.7' else v) for v in base],False),('bad_tilt',[('.21' if v=='.03' else v) for v in base],False),('nan_tilt',[('nan' if v=='.03' else v) for v in base],False),('missing_guard',")
s=s.replace("  if selected:\n", "  if state is not None and hasattr(state,'tilt_recontact_rad'):\n   assert state.tilt_recontact_rad==.03\n   assert state.front_inset_fraction==(.7 if context['front_route_selected'] else (None if context['target'][0]>=.48 else 1.))\n   row.update(front_route_selected=context['front_route_selected'],effective_fraction=state.front_inset_fraction,tilt_recontact_rad=state.tilt_recontact_rad)\n  if selected:\n")
(root/'check_staged_contact_stability_factory.py').write_text(s)
print(stage)
