#!/usr/bin/env python3
"""Zero-start paired pilot. Raw diagnostics are quarantined; never auto-train."""
from __future__ import annotations
import argparse
import json
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument('--out-dir', required=True)
parser.add_argument('--waist-pilot-contract', type=Path, help='Exact verified fresh waist pilot contract; diagnostic files remain excluded.')
parser.add_argument('--role', choices=('diagnostic', 'pilot'), default='diagnostic')
parser.add_argument('--layout-start', type=int, default=0)
parser.add_argument('--spatial-pilot-contract', type=Path, help='Exact reviewed geometry/settings for fresh pilot only; diagnostic files remain excluded.')
parser.add_argument('--diagnostic-layout-json', help='Explicit reviewed geometry proposal; diagnostic only, never training-ready.')
parser.add_argument('--layouts', type=int, default=1)
parser.add_argument('--wait-episodes', type=int, default=0)
parser.add_argument('--wait-layout-start', type=int, default=10000)
parser.add_argument('--steps', type=int, default=160, help='Push frames, including final stable hold [15 Hz].')
parser.add_argument('--idle', action='store_true')
parser.add_argument('--wait-steps', type=int, default=70)
parser.add_argument('--motion-protocol', choices=('waist_locked_v1', 'waist_yaw_enabled_v1'), default='waist_locked_v1')
parser.add_argument('--waist-limit-rad', type=float, default=.20, help='Provisional diagnostic working bound, not a verified deployment range.')
parser.add_argument('--waist-wait-tolerance-rad', type=float, default=.01)
parser.add_argument('--expert-frontal-strict-descent', action='store_true', help='Diagnostic: require5mm XY error before descending from tip_cross.')
parser.add_argument('--trace-control-jacobian-every', type=int, default=0, help='Read-only diagnostic world point Jacobian sampling interval;0 disables.')
parser.add_argument('--expert-frontal-rear-y-offset-m', type=float, default=0., help='Diagnostic off-center rear contact opposite sorting direction;0..4cm, requires Y tracking.')
parser.add_argument('--expert-frontal-rear-object-frame', action='store_true', help='Diagnostic rearY contact lever in actual object coordinates; requires tip route and positive rear offset.')
parser.add_argument('--trace-hand-contact-forces', action='store_true', help='Read-only solved hand contacts including table; requires solved force tracing.')
parser.add_argument('--expert-frontal-press-z', type=float, default=.810, help='Diagnostic rear contact palm height; default.810, range.800..850m.')
parser.add_argument('--expert-frontal-top-guarded-descent', action='store_true', help='Diagnostic top descent1.5mm/frame only while XY error<8mm; retreat on contact tracking loss.')
parser.add_argument('--expert-frontal-top-continuous-drag', action='store_true', help='Diagnostic continuous3mm/frame top drag with lost-contact lift/reacquire; requires guarded descent.')
parser.add_argument('--expert-frontal-top-cross-admittance', action='store_true', help='Diagnostic reduce worldX hand-on-target force around latched X with gain0.8mm/N, step0.5mm, total10mm; requires push-X hold.')
parser.add_argument('--expert-frontal-top-hold-push-x', action='store_true', help='Diagnostic latch worldX reference on entering each top push; requires edge guard. Keeps approach bias at latch, stops following subsequent object X/yaw drift.')
parser.add_argument('--expert-frontal-top-hand-obstacle-guard-m', type=float, default=0., help='Diagnostic conservative whole-hand/other-core face-axis gap guard0..10mm; lift and shift next top contact inward in10mm increments, max30mm. Requires core forward-margin route.')
parser.add_argument('--expert-frontal-top-edge-guard-m', type=float, default=0., help='Lift on force-weighted forward contact margin below threshold, or tilt above0.03rad; requires forward-margin route.')
parser.add_argument('--expert-frontal-top-recovery-clearance-m', type=float, default=0., help='After first recovery only, top transit above current target top/obstacle center+30mm by40..80mm; requires edge guard.')
parser.add_argument('--trace-arm-contact-forces', action='store_true', help='Read-only solved contacts involving any shoulder/elbow/wrist link.')
parser.add_argument('--expert-frontal-top-forward-margin-m', type=float, default=0., help='Diagnostic closest top contact satisfying real XY10mm inset and requested worldY forward travel margin, at most40mm; requires core corner route.')
parser.add_argument('--expert-frontal-top-support-hysteresis-m', type=float, default=0., help='Diagnostic real support vertex height hysteresis, max0.5mm; requires collision-core route. Zero preserves exact min vertex.')
parser.add_argument('--expert-frontal-top-collision-core', action='store_true', help='Diagnostic top corner planned from measured live USD collision core, checked against spawn dimensions; visual geometry unchanged.')
parser.add_argument('--expert-frontal-top-approach-compensation', action='store_true', help='Diagnostic unloaded approach XY integral max10mm, slew0.5mm/frame, and3mm nominal alignment; requires visible corner.')
parser.add_argument('--expert-frontal-top-visible-corner', action='store_true', help='Diagnostic10mm inset latched top corner plus soft waist preference for50percent projected bbox coverage; original camera unchanged.')
parser.add_argument('--expert-frontal-top-load-n', type=float, default=3., help='Diagnostic top vertical load target0.5..5N; default3N, requires top route if changed.')
parser.add_argument('--expert-frontal-top-inset-fraction', type=float, default=None, help='Diagnostic inset as fraction of selected half-width:1=center; omitted keeps20mm front inset.')
parser.add_argument('--expert-frontal-top-drag-step-m', type=float, default=.003, help='Diagnostic continuous top drag advance1..12mm/frame; default3mm.')
parser.add_argument('--expert-front-recovery-hysteresis-m', type=float, default=0., help='Diagnostic front recovery hysteresis0..1mm. Initial/resume nominal clearance unchanged; recovery threshold remains>=11mm and original10mm emergency guard remains.')
parser.add_argument('--expert-front-contact-inset-fraction', type=float, default=None, help='Diagnostic optional front-route contact inset fraction0.5..1; non-front contact unchanged.')
parser.add_argument('--expert-top-tilt-recontact-rad', type=float, default=0., help='Diagnostic independent top tilt withdrawal threshold0..0.10rad, zero disabled; original0.20rad pose gate unchanged.')
parser.add_argument('--expert-top-object-relative-lead-m', type=float, default=0., help='Diagnostic calibrated top desired XY lead in metres;0 disables, .012..030. Original guards and3mm slew retained; no claim of realized contact lead.')
parser.add_argument('--expert-top-contact-center-calibration', action='store_true', help='Diagnostic initial load-centroid measurement, lift and recenter before top pushing.')
parser.add_argument('--expert-top-contact-normal-hold', action='store_true', help='Diagnostic top routes: latch hand-local world-up on first press, preserve tilt through recontacts while world yaw remains free. Original guards keep precedence.')
parser.add_argument('--expert-terminal-joint-hold', action='store_true', help='Diagnostic only: after confirmed released/clear/unloaded tracking, repeat prior11D joint target; revoke on guard or lost conditions.')
parser.add_argument('--expert-initial-top-route', action='store_true', help='Diagnostic only: far direct long transfers start with measured-support top approach; full live clearance guards retained.')
parser.add_argument('--expert-top-confirmed-release', action='store_true', help='Diagnostic guarded top route: release after ten measured frames satisfy original target position/stability conditions; all original safety/quality gates retained.')
parser.add_argument('--expert-front-recontact-z', type=float, default=.91, help='Diagnostic front route only: recovery travel height after lost contact; initial approach remains0.91m. Bound0.84..0.91m, original guards retained.')
parser.add_argument('--expert-front-object-relative-lead', action='store_true', help='Diagnostic front route: latch contact reference offset per acquisition and bound desired XY lead relative to observed object, retaining3mm slew and original guards.')
parser.add_argument('--expert-front-confirm-nominal-clearance', action='store_true', help='Diagnostic: three consecutive observed nominal-clearance frames may resume lateral motion; immediate nominal+0.5mm path and emergency guards remain.')
parser.add_argument('--expert-front-recover-clearance', action='store_true', help='Diagnostic restore front gap below nominal, resume at nominal+0.5mm, hold currentY during corrections; emergency guards unchanged.')
parser.add_argument('--expert-top-nearer-far-contact', action='store_true', help='Diagnostic projected top contact: use20mm front inset for initial targetX>=0.48m, retain configured center for near objects; aims to reduce reach/waist demand.')
parser.add_argument('--expert-top-hold-established-x', action='store_true', help='Diagnostic non-front projected top drag: preserve first established top command X across recontacts instead of following object X drift.')
parser.add_argument('--expert-front-clearance-m', type=float, default=.02, help='Diagnostic front route planned object clearance12..30mm;10mm emergency parcel guard and5mm table guard remain fixed.')
parser.add_argument('--expert-top-alignment-tolerance-m', type=float, default=.008, help='Diagnostic projected-support XY approach tolerance3..12mm; default8mm, no change to task/data quality gates or force confirmation.')
parser.add_argument('--expert-top-projected-support', action='store_true', help='Diagnostic continuous virtual support-plane reference, exact normal-height/tangent-center Jacobian; real lowest vertices still observed.')
parser.add_argument('--expert-front-top-route', action='store_true', help='Diagnostic shortest eligible front top route with live parcel/table/hand guards; rear/direct routes otherwise unchanged.')
parser.add_argument('--expert-frontal-top-recontact', action='store_true', help='Diagnostic whole-hand supporting-point top contact with bounded3N load control after rear clearance.')
parser.add_argument('--expert-frontal-contact-pad', action='store_true', help='Diagnostic measured-contact nearest STL vertex instead of max-X fingertip; requires tip route.')
parser.add_argument('--expert-frontal-tip-recontact', action='store_true', help='Diagnostic actual distal-mesh-point side recontact; rear controller unchanged.')
parser.add_argument('--expert-frontal-load-n', type=float, default=0., help='Diagnostic sweep-only signed Z admittance: lower at most25mm to recover measured target load.')
parser.add_argument('--expert-frontal-sweep-lead-y', type=float, default=.04, help='Diagnostic target-relative Y sweep lead0..6cm; tracked sweep only.')
parser.add_argument('--expert-frontal-track-sweep', action='store_true', help='Diagnostic measured parcelXY sweep servo with bounded3/6mm increments; requires planned sweepX.')
parser.add_argument('--expert-frontal-sweep-x', action='store_true', help='Diagnostic30frame blend to planned flankX after recontact instead of freezing tracking residual.')
parser.add_argument('--expert-frontal-recontact', action='store_true', help='Diagnostic lift and flank recontact after measured rear clearance; requires frontal Y tracking.')
parser.add_argument('--expert-frontal-follow-y', action='store_true', help='Diagnostic rear push follows actual parcel Y with 2mm/frame cap; requires frontal feedback.')
parser.add_argument('--expert-frontal-feedback', action='store_true', help='Diagnostic measured rear endpoint with bounded palm tracking lead; requires frontal bypass.')
parser.add_argument('--expert-frontal-bypass', action='store_true', help='Diagnostic blocked-route frontal push to measured rear clearance, then lateral sweep; requires320frames.')
parser.add_argument('--expert-contact-load-n', type=float, default=0., help='Diagnostic vertical admittance using previous solved hand-target force; target.5..5N, zero disables.')
parser.add_argument('--expert-far-exit-y', type=float, default=0., help='Diagnostic far-target lateral endpoint (.30-.34), near targets retain expert-exit-y; requires curved path and goal release.')
parser.add_argument('--expert-goal-release', action='store_true', help='Diagnostic: lift active hand at measured object goal, keep measured palm XY.')
parser.add_argument('--trace-viewer-every', type=int, default=0, help='Diagnostic third-person JPEG every N pre-action frames; never policy input.')
parser.add_argument('--expert-far-sweep-retreat-m', type=float, default=0., help='Diagnostic curved sweep: late contact X retreats toward torso, at most .10m; zero disables.')
parser.add_argument('--expert-rear-bypass-m', type=float, default=0., help='Diagnostic: move target rearward before lateral sweep; physically measured transition.')
parser.add_argument('--bounded-coupled-ik', action='store_true', help='Solve waist and arms inside joint/step bounds instead of post-solve clipping.')
parser.add_argument('--inactive-retract-m', type=float, default=0., help='Diagnostic coordinated inactive palm target: back d, outward .8d.')
parser.add_argument('--waist-coordinated-expert', action='store_true', help='Quarantined coupled palm IK diagnostic.')
parser.add_argument('--extended-waist-diagnostic', action='store_true', help='Explicit expert/probe-only diagnostic work range up to1.0rad after reach evidence; not training/deployment approval.')
parser.add_argument('--waist-probe-amplitude-rad', type=float, default=0., help='Diagnostic explicit empty-probe amplitude; zero preserves0.8*waist limit.')
parser.add_argument('--waist-probe', action='store_true', help='Diagnostic empty-table sinusoidal yaw; intentionally not a valid wait demonstration.')
parser.add_argument('--policy-port', type=int, default=0, help='Nonzero selects PI0.5 evaluation, never demonstration collection.')
parser.add_argument('--policy-host', default='127.0.0.1')
parser.add_argument('--eval-seed', type=int, default=0)
parser.add_argument('--environment-seed', type=int, default=None, help='Explicit environment creation and per-episode reset RNG seed; separate from layout appearance seed and policy inference seed. Does not guarantee bitwise GPU physics.')
parser.add_argument('--policy-max-action-step', type=float, default=0.,
                    help='Diagnostic model-target slew cap [rad/step], 0 disables; raw predictions are retained.')
parser.add_argument('--horizon', type=int, default=10)
parser.add_argument('--prompt-variant', choices=('short', 'unified_ablation'), default='short')
parser.add_argument('--wait-force-n', type=float, default=0., help='Diagnostic only: world-X physical force pulse on left hand, frames20-25 [N].')
parser.add_argument('--wait-force-start', type=int, default=20, help='Physical wait-pulse start, 5 or20.')
parser.add_argument('--recovery-pilot-contract', type=Path, help='Reviewed exact settings permit fresh forced pilot collection; diagnostics remain quarantined.')
parser.add_argument('--push-force-n', type=float, default=0., help='Diagnostic active-hand world-X force at frames5-10 during lift, no parcel force.')
parser.add_argument('--push-force-axis', choices=('x','negative_x','z'), default='x', help='Diagnostic force direction; pilot contracts remain positiveX only.')
parser.add_argument('--push-force-start', type=int, default=5, help='Diagnostic pulse start; pilot contracts remain frame5 only.')
parser.add_argument('--wait-force-side', choices=('left','right','both'), default='left', help='Diagnostic physical force target; each selected hand receives wait-force-n.')
parser.add_argument('--settled-contact', action='store_true', help='Diagnostic expert: settle near contact height before sweeping.')
parser.add_argument('--expert-staging-z', type=float, default=1.0, help='Diagnostic approach palm height [m]; historical default1.0.')
parser.add_argument('--expert-front-reposition', type=float, default=0., help='Diagnostic component-only frontward palm travel for near opposite-side targets.')
parser.add_argument('--expert-front-reposition-hold-yz', action='store_true', help='Diagnostic: retain measured palm Y/Z during retreat and hold.')
parser.add_argument('--expert-front-reposition-measured-start', action='store_true', help='Diagnostic: anchor retreat X at measured palm on phase entry.')
parser.add_argument('--bounded-servo-memory', action='store_true', help='Diagnostic bounded accumulated IK targets; max .10rad lead over measured q.')
parser.add_argument('--finger-heading-weight', type=float, default=0., help='Diagnostic soft world-X finger heading constraint; 0 disables.')
parser.add_argument('--expert-max-contact-x', type=float, default=0., help='Diagnostic cap on palm contact X, 0 keeps parcel-center X.')
parser.add_argument('--expert-contact-confirmed-sweep', action='store_true', help='Diagnostic: after measurable force transfer, sweep from measured contact pose.')
parser.add_argument('--expert-object-feedback-lead', type=float, default=0., help='Diagnostic far-object closed-loop Y lead; 0 disables, m.')
parser.add_argument('--expert-far-contact-offset', type=float, default=0., help='Diagnostic distance rule: override lateral offset for targets X>=.48m, 0 disables.')
parser.add_argument('--expert-contact-offset', type=float, default=-.13, help='Diagnostic signed pre-contact lateral offset [m].')
parser.add_argument('--expert-crossed-contact-offset', type=float, default=0., help='Diagnostic opposite-side target approach offset; zero retains distance rule.')
parser.add_argument('--expert-exit-y', type=float, default=.30, help='Diagnostic absolute lateral palm endpoint [m]; default unchanged.')
parser.add_argument('--recover-contact-height', action='store_true', help='Diagnostic expert: pause lateral sweep while palm is too high, then resume after physical height recovery.')
parser.add_argument('--trace-contacts', action='store_true', help='Diagnostic Newton contact pairs.')
parser.add_argument('--trace-solved-contact-forces', action='store_true', help='Diagnostic read-only last-tick solved MuJoCo forces; no solver refresh.')
parser.add_argument('--trace-episode-contacts', action='store_true', help='Diagnostic read-only last-physics-tick contact buffer after each control action; no force measurement.')
parser.add_argument('--newton-contacts', action='store_true', help='Diagnostic collision-pipeline comparison.')
parser.add_argument('--layout-x-offset', type=float, default=0., help='Diagnostic reachability offset [m].')
AppLauncher.add_app_launcher_args(parser)
from dataclasses import dataclass
from pathlib import Path
from copy import deepcopy
import hashlib
from simfoundry.data.waist_pilot_protocol import validate_waist_contract, semantic_settings

@dataclass(frozen=True)
class WaistPilotAdmission:
    contract_sha256: str
    contract_path: Path
    push_layouts: dict
    wait_layouts: dict

    def layout(self, identifier, *, wait=False):
        entries = self.wait_layouts if wait else self.push_layouts
        if identifier not in entries:
            raise ValueError('Layout outside exact admitted collection schedule')
        return deepcopy(entries[identifier])

def prepare_waist_pilot(settings, collector_path):
    path = settings.get('waist_pilot_contract')
    if not path:
        return None
    if settings.get('role') != 'pilot' or settings.get('motion_protocol') != 'waist_yaw_enabled_v1':
        raise ValueError('Waist contract only permits explicit fresh waist pilot')
    if any((settings.get(k) for k in ('spatial_pilot_contract', 'recovery_pilot_contract', 'diagnostic_layout_json'))):
        raise ValueError('Cannot combine waist contract with another layout/admission source')
    if settings.get('policy_port') or settings.get('idle') or settings.get('waist_probe'):
        raise ValueError('Cannot admit policy/idle/probe as expert pilot')
    contract, digest = validate_waist_contract(path)
    if semantic_settings(settings) != contract.get('prelaunch_collector_settings'):
        raise ValueError('Fresh prelaunch settings differ from exact waist contract')
    actual = hashlib.sha256(Path(collector_path).read_bytes()).hexdigest()
    if actual != contract['pilot_collector_sha256']:
        raise ValueError('Fresh collector differs from exact contract source')

    def schedule(start_key, count_key, registered):
        count = settings.get(count_key)
        start = settings.get(start_key)
        if type(count) is not int or count < 0 or type(start) is not int or (start < 0):
            raise ValueError('Invalid explicit collection schedule')
        registered = {d['layout_id']: d for d in registered}
        requested = range(start, start + count)
        if not set(requested) <= set(registered):
            raise ValueError('Scheduled layout not registered in contract')
        return {identifier: deepcopy(registered[identifier]) for identifier in requested}
    pushes = schedule('layout_start', 'layouts', contract['layouts'])
    waits = schedule('wait_layout_start', 'wait_episodes', contract['wait_layouts'])
    if not pushes and (not waits):
        raise ValueError('Empty fresh collection schedule')
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
        raise ValueError('Waist contract changed during validation')
    return WaistPilotAdmission(digest, Path(path).resolve(), pushes, waits)

def finalize_waist_pilot(admission, settings, collector_path):
    """After AppLauncher mutates args, verify resolved settings before env/data."""
    if admission is None:
        return
    contract, digest = validate_waist_contract(admission.contract_path, settings=settings)
    if digest != admission.contract_sha256:
        raise ValueError('Waist contract changed during launcher initialization')
    if hashlib.sha256(Path(collector_path).read_bytes()).hexdigest() != contract['pilot_collector_sha256']:
        raise ValueError('Fresh collector changed during launcher initialization')

args = parser.parse_args()
try:
    waist_admission = prepare_waist_pilot(vars(args), Path(__file__).resolve())
except (ValueError, OSError, KeyError) as exc:
    parser.error(str(exc))
diagnostic_or_waist_pilot = args.role == 'diagnostic' or waist_admission is not None
waist_contract_hash = waist_admission.contract_sha256 if waist_admission else None
if args.expert_top_object_relative_lead_m and not (.012 <= args.expert_top_object_relative_lead_m <= .030 and args.expert_top_contact_center_calibration and not args.expert_front_object_relative_lead):
    parser.error('Bounded top lead requires calibrated contact reference, .012..030m and no competing front lead')
if args.expert_top_contact_center_calibration and not (diagnostic_or_waist_pilot and args.expert_top_contact_normal_hold and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag and not args.expert_frontal_top_visible_corner and not args.expert_frontal_top_approach_compensation and not args.expert_frontal_top_recovery_clearance_m and not args.policy_port and not args.idle):
    parser.error('Contact center calibration requires normal-held projected guarded top diagnostic, no corner/approach/recovery-height alternatives')
if args.expert_top_contact_normal_hold and not (diagnostic_or_waist_pilot and args.expert_frontal_top_recontact and args.waist_coordinated_expert and args.bounded_coupled_ik and args.trace_solved_contact_forces and not args.policy_port and not args.idle):
    parser.error('Front contact normal hold requires traced bounded coordinated top diagnostic expert')
if args.expert_terminal_joint_hold and not (diagnostic_or_waist_pilot and args.waist_coordinated_expert and args.bounded_coupled_ik and args.trace_solved_contact_forces and not args.policy_port and not args.idle):
    parser.error('Terminal joint hold requires coordinated bounded force-traced diagnostic expert')
if args.expert_top_nearer_far_contact and (not args.expert_top_projected_support or args.expert_frontal_top_inset_fraction != 1.):
    parser.error('Geometry-selected nearer far contact requires projected diagnostic with configured center fraction1')
if not 0 <= args.expert_front_recovery_hysteresis_m <= .001 or (args.expert_front_recovery_hysteresis_m and not args.expert_front_recover_clearance):
    parser.error('Front hysteresis0..1mm requires explicit clearance recovery')
if args.expert_front_contact_inset_fraction is not None and (not .5<=args.expert_front_contact_inset_fraction<=1 or not args.expert_front_top_route or not args.expert_top_projected_support or not diagnostic_or_waist_pilot):
    parser.error('Front contact fraction requires diagnostic projected front route and0.5..1 bound')
if not 0<=args.expert_top_tilt_recontact_rad<=.10 or (args.expert_top_tilt_recontact_rad and not (diagnostic_or_waist_pilot and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag)):
    parser.error('Tilt recovery requires diagnostic projected guarded continuous top route and0..0.10rad')
if args.expert_initial_top_route and not (diagnostic_or_waist_pilot and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag):
    parser.error('Initial top route requires projected guarded continuous diagnostic')
if args.expert_top_confirmed_release and not (diagnostic_or_waist_pilot and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag):
    parser.error('Confirmed top release requires explicit projected guarded continuous diagnostic route')
if not .84 <= args.expert_front_recontact_z <= .91:
    parser.error('Front recontact Z must be0.84..0.91m')
if args.expert_front_recontact_z != .91 and not (args.expert_front_top_route and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag):
    parser.error('Short front recontact requires projected, guarded, continuous front diagnostic')
if args.expert_front_object_relative_lead and not (args.expert_front_top_route and args.expert_top_projected_support):
    parser.error('Object-relative front lead requires explicit front route and projected support diagnostic')
if args.expert_front_confirm_nominal_clearance and not args.expert_front_recover_clearance:
    parser.error('Nominal clearance confirmation requires explicit front recovery diagnostic')
if args.expert_front_recover_clearance and not args.expert_front_top_route:
    parser.error('Front clearance recovery requires explicit diagnostic front route')
if args.expert_top_hold_established_x and (not args.expert_top_projected_support or not args.expert_frontal_top_continuous_drag or args.expert_frontal_top_hold_push_x or args.expert_frontal_top_cross_admittance):
    parser.error('Established X hold requires projected continuous diagnostic, without legacy X/admittance modes')
if not .012 <= args.expert_front_clearance_m <= .03 or (args.expert_front_clearance_m != .02 and not args.expert_front_top_route):
    parser.error('Nondefault front clearance requires front route, range12..30mm')
if not .003 <= args.expert_top_alignment_tolerance_m <= .012 or (args.expert_top_alignment_tolerance_m != .008 and not args.expert_top_projected_support):
    parser.error('Nondefault top alignment tolerance requires projected diagnostic, range3..12mm')
if args.expert_top_projected_support and (not diagnostic_or_waist_pilot or args.policy_port or not args.expert_frontal_top_recontact or not args.bounded_coupled_ik or not args.waist_coordinated_expert or args.expert_frontal_top_support_hysteresis_m or args.expert_frontal_top_visible_corner):
    parser.error('Projected support requires isolated coordinated bounded top diagnostic, no hysteresis/corner combination')
if args.expert_front_top_route and (not diagnostic_or_waist_pilot or args.policy_port or not args.expert_frontal_top_continuous_drag or not args.trace_solved_contact_forces or not args.bounded_coupled_ik or args.expert_frontal_top_visible_corner or args.expert_frontal_top_collision_core or args.expert_frontal_top_hand_obstacle_guard_m):
    parser.error('Front top route requires isolated baseline top continuous-drag diagnostic with bounded IK/force trace; advanced corner/core guards cannot be combined')
if args.environment_seed is not None and not 0 <= args.environment_seed < 2**31:
    parser.error('Environment seed must be a nonnegative signed32-bit integer')
if args.extended_waist_diagnostic and (not diagnostic_or_waist_pilot or args.motion_protocol != 'waist_yaw_enabled_v1' or args.policy_port):
    parser.error('Extended waist work range is only for isolated expert/probe diagnostics')
if args.wait_steps < 50 or not 0 < args.waist_wait_tolerance_rad <= args.waist_limit_rad <= (1.0 if args.extended_waist_diagnostic or waist_admission is not None else .80):
    parser.error('Invalid diagnostic waist bounds or wait duration')
if args.waist_probe_amplitude_rad and (not args.waist_probe or not 0 < args.waist_probe_amplitude_rad <= args.waist_limit_rad-.01 or 6.283185307179586*args.waist_probe_amplitude_rad/(args.wait_steps-1) > .08):
    parser.error('Probe amplitude requires probe, >=.01rad tracking reserve, and <=.08rad command increment bound')
if args.motion_protocol != 'waist_locked_v1' and not diagnostic_or_waist_pilot:
    parser.error('Waist-enabled data remain diagnostic until coordinated expert and full-chain review pass')
if args.expert_rear_bypass_m and (not args.bounded_coupled_ik or not .12 <= args.expert_rear_bypass_m <= .20 or args.steps < 240):
    parser.error('Rear bypass requires bounded coupled expert, .12-.20m travel, and >=240 diagnostic frames')
if args.trace_viewer_every and (not diagnostic_or_waist_pilot or not 1 <= args.trace_viewer_every <= 30):
    parser.error('Viewer snapshots require diagnostic role and frame interval1..30')
if args.expert_frontal_strict_descent and not args.expert_frontal_tip_recontact:
    parser.error('Strict descent requires frontal tip route')
if args.trace_control_jacobian_every and (not diagnostic_or_waist_pilot or not args.waist_coordinated_expert or args.trace_control_jacobian_every < 1):
    parser.error('Jacobian trace requires coordinated diagnostic and positive interval')
if not 0 <= args.expert_frontal_rear_y_offset_m <= .04 or (args.expert_frontal_rear_y_offset_m and not args.expert_frontal_follow_y):
    parser.error('Rear offset requires frontal Y tracking and0..4cm')
if args.expert_frontal_rear_object_frame and (not args.expert_frontal_tip_recontact or args.expert_frontal_rear_y_offset_m<=0):
    parser.error('Object-frame rear contact requires tip route and positive rear offset')
if args.trace_hand_contact_forces and not args.trace_solved_contact_forces:
    parser.error('Hand-force trace requires solved force observer')
if not .800 <= args.expert_frontal_press_z <= .850 or (args.expert_frontal_press_z != .810 and not args.expert_frontal_bypass):
    parser.error('Nondefault rear contact height requires frontal bypass and.800..850m')
if args.expert_frontal_top_cross_admittance and not args.expert_frontal_top_hold_push_x:
    parser.error('Cross-axis admittance requires push X hold')
if args.expert_frontal_top_hold_push_x and not args.expert_frontal_top_edge_guard_m:
    parser.error('Push X hold requires edge guard')
if args.trace_arm_contact_forces and (not args.trace_solved_contact_forces or not diagnostic_or_waist_pilot):
    parser.error('Arm contact force observer requires solved-force diagnostic tracing')
if not 0<=args.expert_frontal_top_hand_obstacle_guard_m<=.01 or (args.expert_frontal_top_hand_obstacle_guard_m and (not args.expert_frontal_top_collision_core or not args.expert_frontal_top_forward_margin_m or not args.expert_frontal_top_edge_guard_m)):
    parser.error('Hand obstacle guard requires core forward-margin and edge-guard route, with0..10mm bound')
if not 0<=args.expert_frontal_top_edge_guard_m<=.02 or (args.expert_frontal_top_edge_guard_m and args.expert_frontal_top_edge_guard_m>=args.expert_frontal_top_forward_margin_m):
    parser.error('Edge guard must be finite0..0.02m and below configured forward margin')
if args.expert_frontal_top_recovery_clearance_m and (not .04<=args.expert_frontal_top_recovery_clearance_m<=.08 or not args.expert_frontal_top_edge_guard_m):
    parser.error('Recovery clearance requires edge guard and finite40..80mm')
if not 0<=args.expert_frontal_top_forward_margin_m<=.04 or (args.expert_frontal_top_forward_margin_m and not args.expert_frontal_top_collision_core):
    parser.error('Forward margin requires core corner route and finite value0..0.04m')
if not 0<=args.expert_frontal_top_support_hysteresis_m<=.0005 or (args.expert_frontal_top_support_hysteresis_m and not args.expert_frontal_top_collision_core):
    parser.error('Support hysteresis requires collision-core route and finite tolerance0..0.0005m')
if args.expert_frontal_top_collision_core and not args.expert_frontal_top_visible_corner:
    parser.error('Collision core contact diagnostic requires visible corner')
if args.expert_frontal_top_approach_compensation and not args.expert_frontal_top_visible_corner:
    parser.error('Top approach compensation requires visible corner')
if args.expert_frontal_top_visible_corner and (not args.expert_frontal_top_continuous_drag or args.expert_frontal_top_inset_fraction is not None):
    parser.error('Visible corner requires continuous guarded top route and excludes inset fraction')
if not .5<=args.expert_frontal_top_load_n<=5 or (args.expert_frontal_top_load_n!=3 and not args.expert_frontal_top_recontact):
    parser.error('Top load requires0.5..5N and top route for nondefault')
if args.expert_frontal_top_inset_fraction is not None and (not 0<args.expert_frontal_top_inset_fraction<=1 or not args.expert_frontal_top_recontact):
    parser.error('Top inset fraction requires top route and0<fraction<=1')
if not .001<=args.expert_frontal_top_drag_step_m<=.012 or (args.expert_frontal_top_drag_step_m!=.003 and not args.expert_frontal_top_continuous_drag):
    parser.error('Nondefault drag advance requires continuous top drag and1..12mm')
if args.expert_frontal_top_continuous_drag and not args.expert_frontal_top_guarded_descent:
    parser.error('Continuous top drag requires guarded top descent')
if args.expert_frontal_top_guarded_descent and not args.expert_frontal_top_recontact:
    parser.error('Guarded top descent requires top contact route')
if args.expert_frontal_top_recontact and (not args.expert_frontal_follow_y or args.expert_frontal_tip_recontact or args.expert_frontal_recontact or args.expert_frontal_load_n or args.expert_frontal_track_sweep):
    parser.error('Top contact requires frontal Y tracking and excludes side/flank/load/sweep variants')
if args.expert_frontal_contact_pad and not args.expert_frontal_tip_recontact:
    parser.error('Contact pad requires frontal tip recontact route')
if args.expert_frontal_tip_recontact and (not args.expert_frontal_follow_y or args.expert_frontal_recontact or args.expert_frontal_load_n or args.expert_frontal_track_sweep):
    parser.error('Tip route requires frontal Y tracking and excludes legacy flank/load/sweep variants')
if args.expert_frontal_load_n and (not args.expert_frontal_track_sweep or args.expert_contact_load_n or not .5 <= args.expert_frontal_load_n <= 5.):
    parser.error('Frontal load servo requires tracked sweep, no separate load controller, .5..5N')
if not 0 <= args.expert_frontal_sweep_lead_y <= .06 or (args.expert_frontal_sweep_lead_y != .04 and not args.expert_frontal_track_sweep):
    parser.error('Frontal lead must be0..6cm, nondefault requires tracked sweep')
if args.expert_frontal_track_sweep and not args.expert_frontal_sweep_x:
    parser.error('Tracked sweep requires planned sweep X')
if args.expert_frontal_sweep_x and not args.expert_frontal_recontact:
    parser.error('Planned sweep X requires frontal recontact')
if args.expert_frontal_recontact and not args.expert_frontal_follow_y:
    parser.error('Frontal recontact requires Y tracking')
if args.expert_frontal_follow_y and not args.expert_frontal_feedback:
    parser.error('Frontal Y tracking requires endpoint feedback')
if args.expert_frontal_feedback and not args.expert_frontal_bypass:
    parser.error('Frontal endpoint feedback requires frontal bypass')
if args.expert_frontal_bypass and (not args.bounded_coupled_ik or not args.trace_solved_contact_forces or args.expert_rear_bypass_m or args.expert_contact_load_n or args.steps < 320):
    parser.error('Frontal bypass requires bounded coordinated diagnostic, solved observer, >=320frames, no legacy bypass or load intervention')
if args.expert_contact_load_n and (not args.bounded_coupled_ik or not args.trace_solved_contact_forces or args.expert_rear_bypass_m or not .5 <= args.expert_contact_load_n <= 5.):
    parser.error('Contact load control requires bounded coordinated diagnostic, solved observer, no rear bypass, and .5..5N')
if args.expert_far_exit_y and (not args.expert_goal_release or not args.expert_far_sweep_retreat_m or args.expert_exit_y != .30 or not .30 <= args.expert_far_exit_y <= .34):
    parser.error('Far endpoint requires curved goal-release diagnostic, base endpoint.30, and far endpoint.30-.34')
if args.expert_goal_release and (not args.bounded_coupled_ik or args.expert_rear_bypass_m or args.expert_object_feedback_lead):
    parser.error('Goal release requires bounded coordinated diagnostic without bypass or Y-feedback')
if args.expert_far_sweep_retreat_m and (not args.bounded_coupled_ik or not 0 < args.expert_far_sweep_retreat_m <= .10 or args.expert_rear_bypass_m or args.expert_object_feedback_lead or args.expert_max_contact_x):
    parser.error('Curved sweep requires bounded coordinated diagnostic, retreat (0,.10], uncapped X, no bypass or object-feedback intervention')
if args.bounded_coupled_ik and not args.waist_coordinated_expert:
    parser.error('Bounded coupled IK requires coordinated expert')
if args.waist_coordinated_expert and args.bounded_servo_memory:
    parser.error('Legacy five-joint servo memory is not implemented in coupled expert')
if args.inactive_retract_m and (not args.waist_coordinated_expert or not 0 < args.inactive_retract_m <= .10):
    parser.error('Inactive retract requires coupled expert and distance in (0,.10] m')
if args.waist_coordinated_expert and (args.motion_protocol != 'waist_yaw_enabled_v1' or args.policy_port or args.idle or args.waist_probe or not diagnostic_or_waist_pilot or args.expert_front_reposition):
    parser.error('Coordinated expert requires enabled diagnostic push protocol without reposition/probe/policy')
if args.waist_probe and (args.motion_protocol != 'waist_yaw_enabled_v1' or args.policy_port or args.layouts or args.wait_episodes != 1 or args.wait_force_n):
    parser.error('Waist probe requires enabled protocol, empty-table expert diagnostic, layouts=0 and wait-episodes=1')
if args.policy_port and (not diagnostic_or_waist_pilot or args.horizon != 10 or args.idle):
    parser.error('Policy evaluation requires diagnostic role, horizon=10 and no idle flag')
if args.policy_max_action_step and (not args.policy_port or not 0 < args.policy_max_action_step <= .08):
    parser.error('Action slew diagnostic requires policy evaluation and a cap in (0, .08]')
if args.recover_contact_height and (not diagnostic_or_waist_pilot or args.policy_port or args.idle):
    parser.error('Contact-height recovery requires diagnostic expert only')
if args.settled_contact and (not diagnostic_or_waist_pilot or args.policy_port or args.idle):
    parser.error('Settled-contact experiment requires diagnostic expert collection')
if args.wait_force_n and ((not diagnostic_or_waist_pilot and not args.recovery_pilot_contract) or args.policy_port or args.idle or args.layouts != 0 or not 0 < args.wait_force_n <= 80):
    parser.error('Wait force requires diagnostic wait-only collection and force in (0,80] N')
if args.push_force_n and ((not diagnostic_or_waist_pilot and not args.recovery_pilot_contract) or args.policy_port or args.idle or args.wait_force_n or args.wait_episodes or not 0 < args.push_force_n <= 80):
    parser.error('Push force requires diagnostic push-only expert and force in (0,80] N')
if args.push_force_axis != 'x' or args.push_force_start != 5:
    if not diagnostic_or_waist_pilot or not args.push_force_n or args.policy_port or not 1 <= args.push_force_start <= args.steps-6:
        parser.error('Alternate push-force profile requires diagnostic expert and a valid six-frame window')
if args.wait_force_start not in (5,20):
    parser.error('Wait pulse start must be5 or20')
if args.trace_solved_contact_forces and not diagnostic_or_waist_pilot:
    parser.error('Solved force tracing is diagnostic only')
if args.trace_episode_contacts and not diagnostic_or_waist_pilot:
    parser.error('Episode contact tracing is diagnostic only')
recovery_contract_hash = None
if args.recovery_pilot_contract:
    if args.role != 'pilot' or args.policy_port or args.idle or not (args.wait_force_n or args.push_force_n):
        parser.error('Recovery contract requires fresh forced pilot expert collection')
    from simfoundry.data.recovery_protocol import validate_contract
    recovery_contract_hash = validate_contract(args.recovery_pilot_contract,
        layouts=range(args.layout_start,args.layout_start+args.layouts),
        waits=range(args.wait_layout_start,args.wait_layout_start+args.wait_episodes),
        push_force=args.push_force_n,wait_force=args.wait_force_n,
        wait_side=args.wait_force_side,wait_start=args.wait_force_start)
if args.diagnostic_layout_json:
    if not diagnostic_or_waist_pilot or args.layouts != 1 or args.wait_episodes or args.layout_x_offset or args.recovery_pilot_contract:
        parser.error('Explicit layouts require one diagnostic pair and no offsets/waits/contracts')
    from simfoundry.data.diverse_layouts import load_diagnostic_layout
    explicit_layout = load_diagnostic_layout(args.diagnostic_layout_json, args.layout_start)

if args.expert_contact_confirmed_sweep and (not diagnostic_or_waist_pilot or args.policy_port or args.idle or not args.expert_object_feedback_lead):
    parser.error('Contact-confirmed sweep requires diagnostic object feedback')
if args.expert_object_feedback_lead and (not diagnostic_or_waist_pilot or args.policy_port or args.idle or not .02 <= args.expert_object_feedback_lead <= .06):
    parser.error('Object feedback requires diagnostic expert and lead .02-.06m')
if args.expert_far_contact_offset and ((not diagnostic_or_waist_pilot and not args.spatial_pilot_contract) or args.policy_port or args.idle or not -.13 <= args.expert_far_contact_offset <= -.04):
    parser.error('Far contact offset requires diagnostic expert and bounded -.13..-.04m offset')
if args.finger_heading_weight and (not diagnostic_or_waist_pilot or args.policy_port or args.idle or not .02 <= args.finger_heading_weight <= .12):
    parser.error('Finger heading requires diagnostic expert and weight .02-.12')
if args.expert_max_contact_x and (not diagnostic_or_waist_pilot or args.policy_port or args.idle or not .42 <= args.expert_max_contact_x <= .50):
    parser.error('Contact-X cap requires diagnostic expert and cap .42-.50m')
if args.bounded_servo_memory and (not diagnostic_or_waist_pilot or args.policy_port or args.idle):
    parser.error('Bounded servo memory is diagnostic expert only')
if args.expert_staging_z != 1.0 or args.expert_contact_offset != -.13:
    if (not diagnostic_or_waist_pilot and not args.spatial_pilot_contract) or args.policy_port or args.idle or not .90 <= args.expert_staging_z <= 1.0 or not -.13 <= args.expert_contact_offset <= -.04:
        parser.error('Alternative approach geometry requires diagnostic expert and bounded geometry')

if args.expert_exit_y != .30:
    if not diagnostic_or_waist_pilot or args.policy_port or args.idle or args.spatial_pilot_contract or not .30 <= args.expert_exit_y <= .34:
        parser.error('Alternate endpoint requires diagnostic expert and .30-.34m endpoint')

if args.expert_crossed_contact_offset and (not diagnostic_or_waist_pilot or args.policy_port or args.idle or args.spatial_pilot_contract or not -.13 <= args.expert_crossed_contact_offset <= -.04):
    parser.error('Crossed approach offset requires diagnostic expert and -.13..-.04m offset')

if args.expert_front_reposition and (not diagnostic_or_waist_pilot or args.policy_port or args.idle or args.spatial_pilot_contract or args.wait_episodes or not .02 <= args.expert_front_reposition <= .04):
    parser.error('Front reposition requires diagnostic push-only expert and .02-.04m travel')

if args.expert_front_reposition_hold_yz and not args.expert_front_reposition_measured_start:
    parser.error('Hold Y/Z requires measured front reposition start')
if args.expert_front_reposition_measured_start and not args.expert_front_reposition:
    parser.error('Measured retreat start requires the diagnostic front reposition primitive')

spatial_contract_hash = None
if args.spatial_pilot_contract:
    if (args.role != 'pilot' or args.layouts != 1 or args.wait_episodes or args.policy_port or args.idle
            or args.diagnostic_layout_json or args.layout_x_offset or args.recovery_pilot_contract
            or args.wait_force_n or args.push_force_n or args.settled_contact or args.recover_contact_height
            or args.bounded_servo_memory or args.finger_heading_weight or args.expert_max_contact_x):
        parser.error('Spatial pilot requires one fresh registered unforced pair and reviewed expert settings only')
    from simfoundry.data.spatial_protocol import validate_spatial_contract
    from simfoundry.data.diverse_layouts import validate_diagnostic_layout
    explicit_layout, spatial_contract_hash = validate_spatial_contract(args.spatial_pilot_contract,
        layout_id=args.layout_start, steps=args.steps, staging_z=args.expert_staging_z,
        contact_offset=args.expert_contact_offset, far_contact_offset=args.expert_far_contact_offset)
    validate_diagnostic_layout(explicit_layout, args.layout_start)

app = AppLauncher(args, enable_cameras=True).app
finalize_waist_pilot(waist_admission, vars(args), Path(__file__).resolve())

import numpy as np
from PIL import Image
import torch
from isaaclab.envs import ManagerBasedRLEnv
from simfoundry.calibration.sorting_station import reset_sorting_parcels, _set_visible, _write_pose, _DECORATIVE_PARCELS, _OFFTABLE_XYZ
from simfoundry.data.paired_sorting import sample_layout, audit_rollout, audit_pair
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS, VLA_SORTING_UNIFIED_PROMPT
from simfoundry.data.pi05_rpc import request as policy_request
from simfoundry.data.schema import TrajectoryEpisode, save_episode
from simfoundry.data.sorting_cartesian_expert import CartesianSweepState, cartesian_sweep_palm
from simfoundry.data.sorting_quality import resolve_hand_indices, palm_xyz, parcel_xyz
from simfoundry.robots.g1_assets import G1_U1_23DOF_JOINT_NAMES
from simfoundry.isaac_envs.registry import resolve_scene_env
from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np, U1_JOINT_LIMIT_LO, U1_JOINT_LIMIT_HI
from simfoundry.scene_bridge.labels import sync_shipping_labels


def snap(env, robot, hands):
    return {'box': parcel_xyz(env, 'parcel_box'), 'mailer': parcel_xyz(env, 'mailer'),
            'palm_left': palm_xyz(robot, hands['left']), 'palm_right': palm_xyz(robot, hands['right'])}



def read_episode_contact_buffer(action_step):
    """Read existing collision candidates; never refresh/mutate solver contacts.

    Sampled after the control step; buffer reflects the last physics collision
    query, not every substep or solved contact impulse. Candidate presence alone
    is not proof of a load-bearing contact.
    """
    from isaaclab_newton.physics.newton_manager import NewtonManager
    contacts = NewtonManager.get_contacts()
    if contacts is None:
        raise RuntimeError('No Newton contact buffer available for diagnostic')
    model = NewtonManager.get_model()
    count = int(contacts.rigid_contact_count.numpy()[0])
    shape0 = contacts.rigid_contact_shape0.numpy()
    shape1 = contacts.rigid_contact_shape1.numpy()
    if count > len(shape0) or count > len(shape1):
        raise RuntimeError('Contact buffer overflow; diagnostic incomplete')
    pairs = {}
    for a,b in zip(shape0[:count],shape1[:count]):
        if a < 0 or b < 0:
            continue
        labels = tuple(sorted((model.shape_label[int(a)],model.shape_label[int(b)])))
        if not any('/parcel_box/' in x or '/mailer/' in x for x in labels):
            continue
        pairs[labels] = pairs.get(labels,0) + 1
    return {'after_action_step':action_step,'total_contact_candidates':count,
            'target_pairs':[{'shapes':list(k),'candidate_points':v} for k,v in sorted(pairs.items())]}


def collect(env, spec, layout, task_id, root, default):
    robot = env.scene['robot']
    hands = resolve_hand_indices(robot)
    zero = torch.zeros((1, 23), device=env.device)
    rng = np.random.default_rng(layout['seed'])
    if args.environment_seed is None:
        env.reset()
    else:
        env.reset(seed=args.environment_seed)
    if args.wait_force_n or args.push_force_n:
        robot.permanent_wrench_composer.reset()
    reset_sorting_parcels(env, task_id=task_id, single_parcel=False, rng=rng,
                         box_xyz=tuple(layout['box_xyz']) if task_id != 'wait_no_package' else None,
                         mailer_xyz=tuple(layout['mailer_xyz']) if task_id != 'wait_no_package' else None,
                         box_yaw=layout.get('box_yaw', 0.), mailer_yaw=layout.get('mailer_yaw', 0.))
    # Hidden rigid bodies still collide. Give each one its own offstage spot
    # rather than stacking them at a common position and producing impulses.
    hidden = list(_DECORATIVE_PARCELS)
    if task_id == 'wait_no_package':
        hidden += ['parcel_box', 'mailer']
    for index, name in enumerate(hidden):
        _set_visible(env, name, False)
        _write_pose(env, name, (5.0 + index, 5.0, .3))
    reset_trace = []
    print('RESET_REQUEST', layout, 'ACTUAL', snap(env, robot, hands), flush=True)
    for warmup_step in range(60):
        env.step(zero)
        sync_shipping_labels(env)
        if args.trace_contacts and warmup_step in (0, 1, 5, 15, 30, 59):
            from isaaclab_newton.physics.newton_manager import NewtonManager
            contacts = NewtonManager.get_contacts()
            NewtonManager._solver.update_contacts(contacts, NewtonManager.get_state_0())
            model = NewtonManager.get_model()
            n = int(contacts.rigid_contact_count.numpy()[0])
            a, b = contacts.rigid_contact_shape0.numpy()[:n], contacts.rigid_contact_shape1.numpy()[:n]
            pairs = sorted(set(tuple(sorted((model.shape_label[int(x)], model.shape_label[int(y)])))
                               for x, y in zip(a, b) if x >= 0 and y >= 0
                               and any(tag in model.shape_label[int(x)] or tag in model.shape_label[int(y)]
                                       for tag in ('/parcel_box/', '/mailer/'))))
            geometry = []
            if warmup_step == 0:
                for idx, label in enumerate(model.shape_label):
                    if any(tag in label for tag in ('/table/', '/table_edge_wear/', '/parcel_box/', '/mailer/')):
                        body = int(model.shape_body.numpy()[idx])
                        geometry.append({'label': label, 'type': int(model.shape_type.numpy()[idx]),
                            'scale': model.shape_scale.numpy()[idx].tolist(),
                            'local': model.shape_transform.numpy()[idx].tolist(),
                            'body_pose': NewtonManager.get_state_0().body_q.numpy()[body].tolist() if body >= 0 else None})
            row = {'step': warmup_step, 'pose': snap(env, robot, hands), 'contacts': pairs,
                   'geometry': geometry, 'normals': contacts.rigid_contact_normal.numpy()[:n].tolist()}
            reset_trace.append(row)
            print('RESET_CONTACTS', json.dumps(row), flush=True)
    # Reset real physical joint state after scene settling, before capture.
    # No data values are relabeled. Rendering and observations read this state.
    ordered_ids = [robot.joint_names.index(n) for n in G1_U1_23DOF_JOINT_NAMES]
    actual_default = robot.data.default_joint_pos.torch[0, ordered_ids].cpu().numpy()
    if not np.allclose(actual_default, default, atol=1e-6):
        raise RuntimeError('Action offset baseline differs from configured robot default')
    q0 = torch.tensor(default[None], device=env.device)
    robot.write_joint_position_to_sim_index(position=q0, joint_ids=ordered_ids)
    robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q0), joint_ids=ordered_ids)
    env.scene.write_data_to_sim()
    env.sim.forward()
    for _ in range(3):
        env.sim.render()
        env.scene.update(0.0)
    obs = env.observation_manager.compute()
    initial = snap(env, robot, hands)
    initial_quats = {key: env.scene[name].data.root_quat_w.torch[0].detach().cpu().numpy().copy()
                     for key, name in [('box', 'parcel_box'), ('mailer', 'mailer')]}
    side = 'right' if task_id == 'push_box_to_bin' else 'left'
    target = initial['box' if side == 'right' else 'mailer']
    contact_bias = min(0., args.expert_max_contact_x-target[0]) if args.expert_max_contact_x else 0.
    from simfoundry.data.diverse_layouts import contact_offset_for_approach
    effective_offset = contact_offset_for_approach(target[0], target[1], -1 if side == 'right' else 1, args.expert_contact_offset, args.expert_far_contact_offset, args.expert_crossed_contact_offset)
    from simfoundry.data.reach_sweep import sweep_exit_y
    effective_exit_y = sweep_exit_y(target[0], args.expert_exit_y, args.expert_far_exit_y)
    expert = CartesianSweepState(side, target[0], target[1], exit_y=effective_exit_y, contact_x_bias=contact_bias,
                                 contact_palm_z=.840 if side == "left" else .845,
                                 staging_palm_z=args.expert_staging_z, contact_side_offset=effective_offset,
                                 object_feedback_lead=args.expert_object_feedback_lead if target[0] >= .48 else 0.,
                                 contact_confirmed_sweep=args.expert_contact_confirmed_sweep and target[0] >= .48,
                                 far_sweep_retreat_m=args.expert_far_sweep_retreat_m, goal_release=args.expert_goal_release,
                                 finger_heading_weight=args.finger_heading_weight, bounded_servo_memory=args.bounded_servo_memory,
                                 settled_contact=args.settled_contact, recover_contact_height=args.recover_contact_height)
    if args.expert_front_reposition and target[0] < .43 and (-1 if side == 'right' else 1)*target[1] < -.03:
        expert.front_reposition_distance = args.expert_front_reposition
        expert.front_reposition_measured_start = args.expert_front_reposition_measured_start
        expert.front_reposition_hold_yz = args.expert_front_reposition_hold_yz
    parcel_orientations = {'box': [], 'mailer': []}
    horizon = args.wait_steps if args.idle or task_id == 'wait_no_package' else args.steps
    rgbs, qs, acts = [], [], []
    trace = {key: [] for key in initial}
    previous = np.zeros(23, dtype=np.float32)
    top_contact_normal_anchor = None
    contact_center_calibration = None
    contact_center_log = []
    bounded_top_lead = None
    if args.expert_top_object_relative_lead_m and task_id != 'wait_no_package':
        from simfoundry.data.bounded_top_lead import BoundedTopLead
        bounded_top_lead = BoundedTopLead(args.expert_top_object_relative_lead_m)
    if args.expert_top_contact_center_calibration and task_id != 'wait_no_package':
        from simfoundry.data.contact_center_calibration import ContactCenterCalibration
        from simfoundry.data.top_contact_bypass import support_mesh
        contact_center_calibration = ContactCenterCalibration(support_mesh()[side])
    terminal_hold = None
    terminal_hold_log = []
    terminal_other_max_xy = 0.
    if args.expert_terminal_joint_hold and task_id != 'wait_no_package':
        from simfoundry.data.terminal_joint_hold import TerminalJointHold
        from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease
        terminal_hold = TerminalJointHold()
        terminal_goal = ConfirmedPositionRelease(target[1], -1 if side=='right' else 1)
    prompt = PAIRED_SORTING_PROMPTS[task_id]
    if args.policy_port and args.prompt_variant == 'unified_ablation':
        prompt = VLA_SORTING_UNIFIED_PROMPT
    chunk, cursor = None, 0
    infer_log = []
    raw_policy_actions = []
    expert_control = []
    coordination_log = []
    viewer_log = []
    bypass_log = []
    bypass_completed = False
    bypass_target_x = target[0] + args.expert_rear_bypass_m
    obstacle_x = initial['mailer' if side == 'right' else 'box'][0]
    bypass_clearance_x = obstacle_x + .145 + .02
    inactive_anchor = {side: list(initial['palm_' + side]) for side in ('left', 'right')}
    if args.inactive_retract_m:
        inactive = 'left' if side == 'right' else 'right'
        inactive_anchor[inactive][0] -= args.inactive_retract_m
        inactive_anchor[inactive][1] += (.8 if inactive == 'left' else -.8) * args.inactive_retract_m
    previous_top_support = None
    frontal_state = None
    frontal_plan = None
    frontal_log = []
    front_route_selected = False
    initial_top_selected = False
    if args.expert_frontal_bypass and task_id != 'wait_no_package':
        from simfoundry.data.frontal_bypass import frontal_bypass_plan, FrontalBypassState
        target_key = 'box' if side == 'right' else 'mailer'
        obstacle_key = 'mailer' if side == 'right' else 'box'
        target_size = (.14,.09,.045) if side == 'right' else (.15,.145,.04)
        obstacle_size = (.15,.145,.04) if side == 'right' else (.14,.09,.045)
        frontal_plan = frontal_bypass_plan(target, initial[obstacle_key], target_size[:2], obstacle_size[:2],
                                          layout[target_key+'_yaw'], layout[obstacle_key+'_yaw'], -1 if side=='right' else 1)
        if args.expert_front_top_route and frontal_plan['required']:
            from simfoundry.data.front_top_route import select_front_route
            target_actor = 'parcel_box' if side == 'right' else 'mailer'
            other_actor = 'mailer' if side == 'right' else 'parcel_box'
            tq = env.scene[target_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
            oq = env.scene[other_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
            chosen, candidates = select_front_route(target, initial[obstacle_key], target_size, obstacle_size, tq, oq, -1 if side=='right' else 1, margin=args.expert_front_clearance_m)
            front_route_selected = chosen is not None
            frontal_plan['front_route_candidates'] = candidates
            frontal_plan['front_route_selected'] = front_route_selected
        if args.expert_initial_top_route and not frontal_plan['required']:
            from simfoundry.data.initial_top_route_candidate import initial_top_route_candidate
            target_actor = 'parcel_box' if side == 'right' else 'mailer'
            other_actor = 'mailer' if side == 'right' else 'parcel_box'
            tq = env.scene[target_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
            oq = env.scene[other_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
            proposal = initial_top_route_candidate(target,initial[obstacle_key],target_size,obstacle_size,tq,oq,-1 if side=='right' else 1)
            initial_top_selected = proposal['proposed']
            frontal_plan['initial_top_proposal'] = proposal
        frontal_plan['initial_top_selected'] = initial_top_selected
        if frontal_plan['required'] or initial_top_selected:
            frontal_state = FrontalBypassState(frontal_plan, staging_z=args.expert_staging_z, press_z=args.expert_frontal_press_z, feedback_rear_endpoint=args.expert_frontal_feedback, follow_target_y=args.expert_frontal_follow_y, rear_contact_y_offset_m=args.expert_frontal_rear_y_offset_m, rear_contact_object_frame=args.expert_frontal_rear_object_frame, recontact_after_rear=args.expert_frontal_recontact, planned_sweep_x=args.expert_frontal_sweep_x, tracked_sweep=args.expert_frontal_track_sweep, sweep_lead_y=args.expert_frontal_sweep_lead_y)
            frontal_plan['feedback_rear_endpoint'] = args.expert_frontal_feedback
            frontal_plan['rear_press_z'] = args.expert_frontal_press_z
            frontal_plan['follow_target_y'] = args.expert_frontal_follow_y
            frontal_plan['rear_contact_y_offset_m'] = args.expert_frontal_rear_y_offset_m
            frontal_plan['rear_contact_object_frame'] = args.expert_frontal_rear_object_frame
            frontal_plan['recontact_after_rear'] = args.expert_frontal_recontact
            frontal_plan['planned_sweep_x'] = args.expert_frontal_sweep_x
            frontal_plan['tracked_sweep'] = args.expert_frontal_track_sweep
            frontal_plan['sweep_lead_y'] = args.expert_frontal_sweep_lead_y
            frontal_plan['sweep_contact_load_n'] = args.expert_frontal_load_n
            frontal_plan['load_min_bias_m'] = -.025 if args.expert_frontal_load_n else 0.
            if args.expert_frontal_tip_recontact:
                from simfoundry.data.fingertip_bypass import FingertipBypassState, distal_mesh_vertex
                frontal_state = FingertipBypassState(frontal_state,side,tuple(target_size),use_contact_pad=args.expert_frontal_contact_pad,strict_descent=args.expert_frontal_strict_descent)
                frontal_plan['fingertip_recontact'] = dict(local_mesh_vertex=frontal_state.control_vertex(),contact_pad=args.expert_frontal_contact_pad,strict_descent=args.expert_frontal_strict_descent,surface_x_inset_m=.015,surface_z_inset_m=.003,side_penetration_command_m=.004)
            if args.expert_frontal_top_recontact:
                from simfoundry.data.top_contact_bypass import TopContactBypassState, support_mesh
                support_mesh()
                contact_size = tuple(target_size)
                contact_geometry = None
                obstacle_contact_geometry = None
                if args.expert_frontal_top_collision_core:
                    from isaaclab.sim.utils.stage import get_current_stage
                    from simfoundry.data.parcel_collision_geometry import read_parcel_collision_geometry
                    contact_actor = 'parcel_box' if side == 'right' else 'mailer'
                    contact_geometry = read_parcel_collision_geometry(
                        get_current_stage(), '/World/envs/env_0/' + contact_actor,
                        expected_size=env.scene[contact_actor].cfg.spawn.size)
                    contact_geometry['visual_size_xyz'] = list(target_size)
                    contact_size = tuple(contact_geometry['collision_core_size_xyz'])
                    if args.expert_frontal_top_hand_obstacle_guard_m:
                        other_actor = 'mailer' if side == 'right' else 'parcel_box'
                        obstacle_contact_geometry = read_parcel_collision_geometry(
                            get_current_stage(), '/World/envs/env_0/' + other_actor, expected_size=env.scene[other_actor].cfg.spawn.size)
                effective_top_fraction = args.expert_frontal_top_inset_fraction
                if args.expert_top_nearer_far_contact and target[0] >= .48:
                    effective_top_fraction = None
                if front_route_selected and args.expert_front_contact_inset_fraction is not None:
                    effective_top_fraction = args.expert_front_contact_inset_fraction
                frontal_plan['contact_stability_candidate'] = dict(front_contact_inset_fraction=args.expert_front_contact_inset_fraction,applied_front_override=bool(front_route_selected and args.expert_front_contact_inset_fraction is not None),tilt_recontact_rad=args.expert_top_tilt_recontact_rad,original_pose_max_tilt_rad=.20)
                frontal_plan['confirmed_terminal_release'] = dict(enabled=args.expert_top_confirmed_release,zone_y_m=.20,min_progress_m=.15,consecutive_frames=10,max_endpoint_xy_m=.01,keeps_original_release=True,guard_precedence=True)
                top_cls, top_extra = TopContactBypassState, {}
                if front_route_selected:
                    from simfoundry.data.front_top_route import FrontTopRouteState
                    top_cls, top_extra = FrontTopRouteState, dict(obstacle_size=tuple(obstacle_size),route_clearance_m=args.expert_front_clearance_m,recover_clearance=args.expert_front_recover_clearance,confirm_nominal_clearance=args.expert_front_confirm_nominal_clearance,object_relative_lead=args.expert_front_object_relative_lead,recontact_travel_z=args.expert_front_recontact_z,recovery_hysteresis_m=args.expert_front_recovery_hysteresis_m)
                    frontal_plan['front_route_live_guards'] = dict(hand_gap_m=.005,parcel_gap_m=.01,non_target_motion_m=.01,table_margin_m=.005,clearance_before_lateral_m=args.expert_front_clearance_m,recover_clearance=args.expert_front_recover_clearance,recovery_resume_extra_m=.0005 if args.expert_front_recover_clearance else None,nominal_clearance_confirmation_frames=3 if args.expert_front_confirm_nominal_clearance else None,object_relative_lead=args.expert_front_object_relative_lead,object_relative_lead_limit_m=.012 if args.expert_front_object_relative_lead else None,recontact_travel_z=args.expert_front_recontact_z,initial_travel_z=.91,recovery_hysteresis_m=args.expert_front_recovery_hysteresis_m,recovery_trigger_clearance_m=args.expert_front_clearance_m-args.expert_front_recovery_hysteresis_m)
                if initial_top_selected:
                    from simfoundry.data.initial_top_route import InitialTopRouteState
                    top_cls, top_extra = InitialTopRouteState, dict(obstacle_size=tuple(obstacle_size))
                    frontal_plan['initial_top_live_guards'] = dict(hand_gap_m=.005,parcel_gap_m=.01,non_target_motion_m=.01,table_margin_m=.005)
                frontal_state = top_cls(frontal_state,side,contact_size,**top_extra,tilt_recontact_rad=args.expert_top_tilt_recontact_rad,confirm_terminal_release=args.expert_top_confirmed_release,hold_established_x=bool(args.expert_top_hold_established_x and not front_route_selected),alignment_tolerance_m=args.expert_top_alignment_tolerance_m,hand_obstacle_guard_m=args.expert_frontal_top_hand_obstacle_guard_m,cross_axis_admittance=args.expert_frontal_top_cross_admittance,hold_push_x=args.expert_frontal_top_hold_push_x,edge_guard_m=args.expert_frontal_top_edge_guard_m,recovery_clearance_m=args.expert_frontal_top_recovery_clearance_m,forward_margin_m=args.expert_frontal_top_forward_margin_m,guarded_descent=args.expert_frontal_top_guarded_descent,continuous_drag=args.expert_frontal_top_continuous_drag,drag_step_m=args.expert_frontal_top_drag_step_m,front_inset_fraction=effective_top_fraction,corner_contact=args.expert_frontal_top_visible_corner,approach_compensation=args.expert_frontal_top_approach_compensation)
                frontal_state.load.desired_n=args.expert_frontal_top_load_n
                frontal_plan['bounded_top_object_lead'] = dict(enabled=bool(args.expert_top_object_relative_lead_m),desired_axis_lead_m=args.expert_top_object_relative_lead_m,requires_calibrated_reference=True,original_guard_priority=True,scope='Desired waypoint bound; slew lag after abrupt object motion is logged, not assumed bounded realized contact.')
                frontal_plan['contact_center_calibration'] = dict(enabled=args.expert_top_contact_center_calibration,required_loaded_press_samples=3,max_local_scatter_m=.001,max_tangent_reference_shift_m=.08,calibrated_top_fraction=1.,lift_before_recenter=True,guards_take_precedence=True)
                frontal_plan['top_recontact'] = dict(nearer_far_contact=args.expert_top_nearer_far_contact,nearer_far_x_threshold_m=.48,effective_top_fraction=effective_top_fraction,hold_established_x=bool(args.expert_top_hold_established_x and not front_route_selected),alignment_tolerance_m=args.expert_top_alignment_tolerance_m,hand_obstacle_guard_m=args.expert_frontal_top_hand_obstacle_guard_m,obstacle_contact_geometry=obstacle_contact_geometry,hand_guard_recontact_shift_step_m=.01,hand_guard_recontact_shift_max_m=.03,cross_axis_admittance=args.expert_frontal_top_cross_admittance,cross_axis_limits=dict(gain_m_per_n=.0008,max_step_m=.0005,max_bias_m=.01) if args.expert_frontal_top_cross_admittance else None,hold_push_x=args.expert_frontal_top_hold_push_x,edge_guard_m=args.expert_frontal_top_edge_guard_m,edge_guard_tilt_rad=.03 if args.expert_frontal_top_edge_guard_m else None,recovery_clearance_m=args.expert_frontal_top_recovery_clearance_m,forward_margin_m=args.expert_frontal_top_forward_margin_m,support_hysteresis_m=args.expert_frontal_top_support_hysteresis_m,support_reference_scope='Actual hull vertex, may be above true supporting plane by configured hysteresis; whole-hand footprint not certified',contact_geometry=contact_geometry,contact_size_xyz=list(contact_size),collision_core=args.expert_frontal_top_collision_core,approach_compensation=args.expert_frontal_top_approach_compensation,visible_corner=args.expert_frontal_top_visible_corner,corner_inset_m=.01 if args.expert_frontal_top_visible_corner else None,drag_step_m=args.expert_frontal_top_drag_step_m,continuous_drag=args.expert_frontal_top_continuous_drag,guarded_descent=args.expert_frontal_top_guarded_descent,mesh_support_normal='actual parcel top normal',surface_front_inset_m=.02 if effective_top_fraction is None and not args.expert_frontal_top_visible_corner else None,surface_front_inset_fraction=effective_top_fraction,desired_vertical_load_n=args.expert_frontal_top_load_n,load_bias_min_m=-.006,approach_clearance_m=.002,side_lead_m=.012)
            inactive = 'left' if side == 'right' else 'right'
            inactive_anchor[inactive][1] += .08 if inactive == 'left' else -.08
            frontal_plan['inactive_anchor_override'] = dict(side=inactive, xyz=list(inactive_anchor[inactive]), reason='Separate inactive palm from frontal cross waypoint')
    force_log = []
    episode_contacts = []
    solved_contact_forces = []
    load_control_log = []
    load_control = None
    if args.expert_contact_load_n or args.expert_frontal_load_n:
        from simfoundry.data.contact_load_control import ContactLoadControl
        load_control = ContactLoadControl(args.expert_frontal_load_n or args.expert_contact_load_n, min_bias_m=-.025 if args.expert_frontal_load_n else 0.)
    if args.policy_port:
        policy_request(args.policy_host, args.policy_port, {'cmd': 'reset_seed', 'seed': args.eval_seed})
    for step in range(horizon):
        action = np.zeros(23, dtype=np.float32)
        active_control_offset = None
        if args.policy_port:
            if chunk is None or cursor >= min(args.horizon, len(chunk)):
                state = obs['policy'][0].detach().cpu().numpy()[[*range(13,23), 12]]
                image = obs['rgb'][0].detach().cpu().numpy()
                if image.shape[0] in (3,4):
                    image = image[:3].transpose(1,2,0)
                reply = policy_request(args.policy_host, args.policy_port,
                    {'cmd': 'infer', 'image': image, 'state': state, 'task': prompt})
                chunk = np.asarray(reply['actions'], dtype=np.float32)
                if chunk.ndim != 2 or chunk.shape[1] != 11 or len(chunk) < 1 or not np.isfinite(chunk).all():
                    raise ValueError('Invalid policy action chunk')
                cursor = 0
                infer_log.append({'step': step, 'state': state.tolist(), 'prompt': prompt,
                                  'actions': chunk.tolist(), 'infer_ms': reply.get('infer_ms')})
            action[[*range(13,23), 12]] = chunk[cursor]
            cursor += 1
            raw_policy_actions.append((default + action).copy())
            if args.policy_max_action_step:
                action = np.clip(action, previous - args.policy_max_action_step,
                                 previous + args.policy_max_action_step)
        elif step > 0 and not args.idle and task_id != 'wait_no_package':
            projected_support_context = None
            observed_y = parcel_xyz(env, 'parcel_box' if side == 'right' else 'mailer')[1] if (expert.object_feedback_lead or expert.goal_release) else None
            if frontal_state is None:
                cartesian_sweep_palm(robot, hands, action, state=expert, step=step-1, default_q=default, observed_parcel_y=observed_y)
            else:
                from simfoundry.data.frontal_bypass import extent_x_from_quat
                target_actor = 'parcel_box' if side=='right' else 'mailer'
                obstacle_actor = 'mailer' if side=='right' else 'parcel_box'
                target_quat = env.scene[target_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
                obstacle_quat = env.scene[obstacle_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
                point_kwargs = {}
                support_selection = None
                if args.expert_frontal_tip_recontact:
                    from simfoundry.data.fingertip_bypass import distal_mesh_vertex
                    from simfoundry.data.waist_coordination import hand_point_xyz
                    point_kwargs = dict(tip=hand_point_xyz(robot,hands[side],frontal_state.control_vertex()),quat=target_quat)
                if args.expert_frontal_top_recontact:
                    from simfoundry.data.top_contact_bypass import support_vertex
                    from simfoundry.data.waist_coordination import hand_point_xyz
                    from simfoundry.data.contact_load_control import hand_target_vertical_load
                    hand_quat = robot.data.body_quat_w.torch[0,hands[side]].detach().cpu().numpy().tolist()
                    if args.expert_frontal_top_support_hysteresis_m:
                        from simfoundry.data.support_vertex_hysteresis import support_vertex_with_hysteresis
                        offset, support_selection = support_vertex_with_hysteresis(side,hand_quat,target_quat,previous_top_support,args.expert_frontal_top_support_hysteresis_m)
                        previous_top_support = offset
                    else:
                        offset = support_vertex(side,hand_quat,target_quat)
                    load_n = hand_target_vertical_load(solved_contact_forces[-1] if solved_contact_forces else None,side,target_actor)
                    physical_support_offset = tuple(offset)
                    physical_support_xyz = hand_point_xyz(robot,hands[side],physical_support_offset)
                    if args.expert_top_projected_support and (front_route_selected or initial_top_selected or frontal_state.top_mode is not None):
                        from simfoundry.data.projected_support_reference import projected_support_reference
                        from simfoundry.data.top_contact_bypass import support_mesh, rotation_xyzw
                        reference = projected_support_reference(support_mesh()[side], rotation_xyzw(hand_quat), np.asarray(rotation_xyzw(target_quat))[:,2], center_local=contact_center_calibration.center_local if contact_center_calibration is not None else None)
                        projected_support_context = {k: v.tolist() for k,v in reference.items() if k in ('reference_local','center_local','lowest_vertex_local','world_normal')}
                        offset = tuple(reference['reference_local'])
                    point_kwargs = dict(tip=hand_point_xyz(robot,hands[side],offset),quat=target_quat,control_offset_local=offset,load_n=load_n)
                    if args.expert_frontal_top_hand_obstacle_guard_m:
                        from simfoundry.data.hand_obstacle_clearance import hand_face_separation
                        hand_xyz=robot.data.body_pos_w.torch[0,hands[side]].detach().cpu().numpy().tolist()
                        point_kwargs['hand_obstacle_gap_m']=hand_face_separation(side).gap(
                            hand_xyz,hand_quat,parcel_xyz(env,obstacle_actor),obstacle_quat,obstacle_contact_geometry['collision_core_size_xyz'])
                    if front_route_selected or initial_top_selected:
                        from simfoundry.data.hand_obstacle_clearance import hand_face_separation
                        hand_xyz=robot.data.body_pos_w.torch[0,hands[side]].detach().cpu().numpy().tolist()
                        point_kwargs['hand_obstacle_gap_m']=hand_face_separation(side).gap(
                            hand_xyz,hand_quat,parcel_xyz(env,obstacle_actor),obstacle_quat,obstacle_size)
                        point_kwargs['obstacle_quat']=obstacle_quat
                    if args.expert_frontal_top_edge_guard_m:
                        from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
                        point_kwargs['loaded_contact'] = loaded_forward_margin(solved_contact_forces[-1] if solved_contact_forces else None,side,target_actor,parcel_xyz(env,target_actor),target_quat,frontal_state.size,-1 if side=='right' else 1)
                center_measurement = None
                if contact_center_calibration is not None:
                    from simfoundry.data.top_contact_bypass import rotation_xyzw
                    center_measurement = contact_center_calibration.observe(
                        solved_contact_forces[-1] if solved_contact_forces else None,step=step,
                        mode=frontal_state.top_mode,side=side,actor=target_actor,
                        hand_xyz=robot.data.body_pos_w.torch[0,hands[side]].detach().cpu().numpy(),
                        hand_rotation=np.asarray(rotation_xyzw(hand_quat)),object_xyz=parcel_xyz(env,target_actor),
                        object_normal=np.asarray(rotation_xyzw(target_quat))[:,2])
                    center_measurement['mode_before_update'] = frontal_state.top_mode
                waypoint = frontal_state.update(palm_xyz(robot,hands[side]),parcel_xyz(env,target_actor),parcel_xyz(env,obstacle_actor),
                                                extent_x_from_quat(target_size,target_quat),extent_x_from_quat(obstacle_size,obstacle_quat),**point_kwargs)
                if contact_center_calibration is not None and projected_support_context is not None:
                    from simfoundry.data.contact_center_calibration import apply_contact_center_step
                    waypoint,reference,center_transition=apply_contact_center_step(
                        frontal_state,waypoint,contact_center_calibration,center_measurement,
                        vertices=support_mesh()[side],hand_xyz=robot.data.body_pos_w.torch[0,hands[side]].detach().cpu().numpy(),
                        hand_rotation=np.asarray(rotation_xyzw(hand_quat)),object_xyz=parcel_xyz(env,target_actor),
                        object_quat=target_quat,reference=reference)
                    projected_support_context={k:v.tolist() for k,v in reference.items() if k in ('reference_local','center_local','lowest_vertex_local','world_normal')}
                    point_kwargs['control_offset_local']=tuple(reference['reference_local'])
                    contact_center_log.append(dict(step=step,**center_measurement,**center_transition,
                        calibrated_after=contact_center_calibration.center_local is not None,mode=waypoint['mode'],
                        reference_center_local=reference['center_local'].tolist()))
                if bounded_top_lead is not None:
                    from simfoundry.data.bounded_top_lead import route_goal
                    bounded_goal = route_goal(frontal_state,waypoint)
                    if bounded_goal is None or contact_center_calibration.center_local is None:
                        bounded_top_lead.previous = None
                    else:
                        lead_record = bounded_top_lead.update(waypoint['mode'],parcel_xyz(env,target_actor)[:2],bounded_goal,waypoint['observed_support_xyz'][:2],step_m=frontal_state.drag_step_m)
                        waypoint['target_xyz'] = (*lead_record['command_xy'],waypoint['target_xyz'][2])
                        frontal_state.command = waypoint['target_xyz']
                        waypoint['bounded_top_object_lead'] = dict(lead_record,goal_xy=bounded_goal)
                if args.expert_frontal_top_recontact:
                    waypoint['observed_support_offset_local'] = point_kwargs['control_offset_local']
                    waypoint['physical_support_offset_local'] = physical_support_offset
                    waypoint['observed_physical_support_xyz'] = physical_support_xyz
                    if projected_support_context is not None:
                        waypoint['projected_support_reference'] = projected_support_context
                        waypoint['support_reference_scope'] = ('Virtual plane reference: calibrated initial contact tangent center and exact lowest normal height; current physical COP not guaranteed.' if contact_center_calibration is not None and contact_center_calibration.center_local is not None else 'Virtual plane reference: tangential fixed hull center and exact lowest normal height; not a mesh contact point. Physical lowest vertex observed separately.')

                if support_selection is not None:
                    waypoint['support_selection'] = support_selection
                active_control_offset = waypoint.get('control_offset_local')
                expert.last_target_xyz = waypoint['target_xyz']
                expert.mode,expert.mode_step = waypoint['mode'],frontal_state.mode_step
                frontal_log.append(dict(step=step,**waypoint))
            if args.expert_rear_bypass_m and expert.mode == 'sweep' and not bypass_completed:
                observed_target = parcel_xyz(env, 'parcel_box' if side == 'right' else 'mailer')
                if observed_target[0] >= bypass_clearance_x:
                    bypass_completed = True
                    expert.parcel_x = float(observed_target[0])
                    expert.parcel_y = float(observed_target[1])
                    measured = palm_xyz(robot, hands[side])
                    direction = -1 if side == 'right' else 1
                    expert.contact_side_offset = direction * (measured[1] - observed_target[1])
                    expert.mode_step = 0
                    expert.last_target_xyz = (expert.parcel_x, measured[1], expert.contact_palm_z)
                else:
                    expert.mode_step = 0
                    direction = -1 if side == 'right' else 1
                    expert.last_target_xyz = (bypass_target_x, expert.parcel_y + direction * expert.contact_side_offset, expert.contact_palm_z)
                bypass_log.append(dict(step=step,completed=bypass_completed,observed_target=list(observed_target),clearance_x=bypass_clearance_x,palm_target=expert.last_target_xyz))
            if load_control is not None:
                from simfoundry.data.contact_load_control import hand_target_vertical_load
                previous_force = solved_contact_forces[-1] if solved_contact_forces else None
                load_n = hand_target_vertical_load(previous_force, side, 'parcel_box' if side == 'right' else 'mailer')
                load_active = expert.mode == 'bypass_sweep' if args.expert_frontal_load_n else expert.mode in ('press','sweep','engaged_sweep','hold')
                adjustment = load_control.update(load_n, load_active)
                tx,ty,tz = expert.last_target_xyz
                expert.last_target_xyz = (tx,ty,tz+adjustment['applied_z_bias_m'])
                load_control_log.append(dict(step=step,base_target_xyz=[tx,ty,tz],adjusted_target_xyz=list(expert.last_target_xyz), **adjustment))
            waist_preference = None
            if args.expert_frontal_top_visible_corner and frontal_state is not None and expert.mode.startswith('top_'):
                from simfoundry.data.top_contact_visibility import visible_waist_preference
                camera = env.scene['d435i'].data
                k = camera.intrinsic_matrices.torch[0].detach().cpu().numpy()
                h,w = camera.output['rgb'].torch.shape[1:3]
                visibility = visible_waist_preference(parcel_xyz(env,target_actor),target_quat,target_size,
                    (float(k[0,0]),float(k[1,1]),float(k[0,2]),float(k[1,2])),int(w),int(h),
                    float(obs['policy'][0,12]),args.waist_limit_rad-min(.02,.1*args.waist_limit_rad))
                waist_preference = visibility['preferred_waist_rad']
                frontal_log[-1]['visibility_preference'] = visibility
            active_normal_anchor = None
            if args.expert_top_contact_normal_hold and frontal_plan is not None:
                if top_contact_normal_anchor is None and expert.mode in ('top_press','top_push'):
                    from simfoundry.data.top_contact_bypass import rotation_xyzw
                    actual_hand_rotation = np.asarray(rotation_xyzw(robot.data.body_quat_w.torch[0,hands[side]].detach().cpu().numpy()))
                    top_contact_normal_anchor = (actual_hand_rotation.T@np.array([0.,0.,1.])).tolist()
                if top_contact_normal_anchor is not None and expert.mode in ('top_lift','top_cross','top_descend','top_press','top_push'):
                    active_normal_anchor = top_contact_normal_anchor
            if args.waist_coordinated_expert:
                from simfoundry.data.waist_coordination import coordinated_step
                coordination_log.append(dict(step=step, **coordinated_step(robot, hands, action, state=expert, anchor=inactive_anchor, default=default, waist_limit=args.waist_limit_rad, bounded=args.bounded_coupled_ik, active_point_offset=active_control_offset, active_support_reference=projected_support_context if active_control_offset is not None else None, waist_preference=waist_preference, active_normal_anchor_local=active_normal_anchor, trace_jacobian=bool(args.trace_control_jacobian_every and step % args.trace_control_jacobian_every == 0))))
            if terminal_hold is not None:
                from simfoundry.data.top_contact_bypass import support_mesh, rotation_xyzw
                from simfoundry.data.contact_load_control import hand_target_vertical_load
                target_key = 'box' if side=='right' else 'mailer'
                other_key = 'mailer' if side=='right' else 'box'
                target_actor = 'parcel_box' if side=='right' else 'mailer'
                observed = snap(env,robot,hands)
                terminal_other_max_xy = max(terminal_other_max_xy,float(np.linalg.norm(np.asarray(observed[other_key])[:2]-np.asarray(initial[other_key])[:2])))
                highest_object = max(observed[key][2]+float(np.abs(np.asarray(rotation_xyzw(env.scene[actor].data.root_quat_w.torch[0].detach().cpu().numpy()))[2])@np.asarray(size)/2) for key,actor,size in [('box','parcel_box',(.14,.09,.045)),('mailer','mailer',(.15,.145,.04))])
                hand_bottoms = []
                for hand_side in ('left','right'):
                    hand_index = hands[hand_side]
                    hp = robot.data.body_pos_w.torch[0,hand_index].detach().cpu().numpy()
                    hr = np.asarray(rotation_xyzw(robot.data.body_quat_w.torch[0,hand_index].detach().cpu().numpy()))
                    hand_bottoms.append(float((np.asarray(support_mesh()[hand_side])@hr.T+hp)[:,2].min()))
                coordinate = coordination_log[-1]
                inactive_side = 'left' if side=='right' else 'right'
                current_upper = robot.data.joint_pos.torch[0,ordered_ids[12:23]].detach().cpu().numpy()
                readings = dict(mode=expert.mode,target_confirmed=bool(terminal_goal.observe(observed[target_key])),hand_clearance_m=min(hand_bottoms)-highest_object,load_n=float(hand_target_vertical_load(solved_contact_forces[-1] if solved_contact_forces else None,side,target_actor)),active_error_m=float(np.max(np.abs(np.asarray(coordinate['control_point_positions'][side])-expert.last_target_xyz))),inactive_error_m=float(np.max(np.abs(np.asarray(coordinate['palm_positions'][inactive_side])-coordinate['inactive_anchor']))),other_max_xy_m=terminal_other_max_xy,current_upper_q=current_upper.tolist(),previous_upper_command=(previous[12:23]+default[12:23]).tolist())
                held_command = terminal_hold.observe(**readings)
                if held_command is not None:
                    action[12:23] = np.asarray(held_command)-default[12:23]
                    coordinate['unexecuted_solver_waist_target_rad'] = coordinate['waist_target_rad']
                    coordinate['waist_target_rad'] = float(held_command[0])
                coordinate['terminal_joint_hold'] = held_command is not None
                terminal_hold_log.append(dict(step=step,**readings,consecutive_ready=terminal_hold.consecutive,held=held_command is not None,output_upper_command=(action[12:23]+default[12:23]).tolist()))
            # The legacy expert instantly parks the inactive arm. Ramp every
            # joint target so the zero-pose start never creates a discontinuity.
            action = np.clip(action, previous - .055, previous + .055)
        action = np.clip(default + action, U1_JOINT_LIMIT_LO, U1_JOINT_LIMIT_HI) - default
        if args.motion_protocol == 'waist_locked_v1':
            action[12] = 0.
        else:
            if args.waist_probe:
                # Small smooth physical joint command; no state/parcel writes.
                action[12] = (args.waist_probe_amplitude_rad or .8 * args.waist_limit_rad) * np.sin(2*np.pi*step/(horizon-1))
            action[12] = np.clip(action[12], -args.waist_limit_rad, args.waist_limit_rad)
        action = action.astype(np.float32)
        previous = action.copy()
        sample = snap(env, robot, hands)
        if not args.policy_port:
            expert_control.append({'step': step, 'mode': expert.mode, 'mode_step': expert.mode_step,
                                   'settle_count': expert.contact_settle_count, 'height_paused': expert.sweep_height_paused, 'height_settle_count': expert.sweep_height_settle_count, 'sweep_pause_frames': expert.sweep_pause_frames, 'target_xyz': expert.last_target_xyz, 'feedback_target_y': expert.feedback_target_y, 'front_reposition_start_x': expert.front_reposition_start_x, 'front_reposition_start_yz': expert.front_reposition_start_yz})
        for key, actor in [('box', 'parcel_box'), ('mailer', 'mailer')]:
            parcel_orientations[key].append(env.scene[actor].data.root_quat_w.torch[0].detach().cpu().numpy().copy())
        for key in trace:
            trace[key].append(sample[key])
        rgb = obs['rgb'][0].detach().cpu().numpy()
        if rgb.shape[-1] in (3, 4):
            rgb = rgb[..., :3].transpose(2, 0, 1)
        rgb = rgb[:3]
        if rgb.dtype != np.uint8:
            rgb = np.clip(rgb * (255 if rgb.max() <= 1.5 else 1), 0, 255).astype(np.uint8)
        if step % 30 == 0:
            progress = {'layout_id': layout['layout_id'], 'task': task_id, 'step': step,
                        'expert_mode': expert.mode, 'pose': sample}
            (root / 'progress.json').write_text(json.dumps(progress, indent=2))
            Image.fromarray(rgb.transpose(1, 2, 0)).save(root / 'progress.jpg')
            print('PROGRESS', json.dumps(progress), flush=True)
        if args.trace_viewer_every and step % args.trace_viewer_every == 0:
            viewer = env.scene['viewer_cam'].data.output['rgb'].torch[0].detach().cpu().numpy()[..., :3]
            if viewer.dtype != np.uint8:
                viewer = np.clip(viewer*(255 if viewer.max() <= 1.5 else 1),0,255).astype(np.uint8)
            viewer_dir = root / f"viewer_layout_{layout['layout_id']}_{task_id}"
            viewer_dir.mkdir(exist_ok=True)
            Image.fromarray(viewer).save(viewer_dir / f'pre_{step:04d}.jpg', quality=86)
            camera = env.scene['d435i'].data
            viewer_log.append(dict(pre_action_step=step, image=str(viewer_dir / f'pre_{step:04d}.jpg'), policy_camera_position_world=camera.pos_w.torch[0].detach().cpu().numpy().tolist(), policy_camera_quat_ros_xyzw=camera.quat_w_ros.torch[0].detach().cpu().numpy().tolist(), policy_camera_intrinsics=camera.intrinsic_matrices.torch[0].detach().cpu().numpy().tolist()))
        rgbs.append(rgb)
        qs.append(obs['policy'][0].detach().cpu().numpy().copy())
        acts.append(default + action)
        if args.wait_force_n or args.push_force_n:
            force_start = args.push_force_start if args.push_force_n else args.wait_force_start
            force_amplitude = args.push_force_n or args.wait_force_n
            force_value = force_amplitude * float(np.sin(np.pi * (step-force_start+1) / 7)) if force_start <= step <= force_start+5 else 0.
            force_axis = args.push_force_axis if args.push_force_n else 'x'
            force_vector = ([0.,0.,force_value] if force_axis == 'z' else [-force_value if force_axis == 'negative_x' else force_value,0.,0.])
            robot.permanent_wrench_composer.reset()
            force_sides = (side,) if args.push_force_n else (('left','right') if args.wait_force_side == 'both' else (args.wait_force_side,))
            force_ids = [hands[side] for side in force_sides]
            if force_value:
                force = torch.tensor([[force_vector] * len(force_ids)], dtype=torch.float32, device=env.device)
                robot.permanent_wrench_composer.set_forces_and_torques_index(forces=force, body_ids=force_ids, is_global=True)
            force_log.append({'step':step,'bodies':[side+'_hand' for side in force_sides], 'body_indices':force_ids,'force_per_body_world_N':force_vector})
        obs, _, terminated, truncated, _ = env.step(torch.tensor(action[None], device=env.device))
        if args.trace_episode_contacts:
            contact_record = read_episode_contact_buffer(step)
            contact_record['post_action_pose'] = snap(env, robot, hands)
            episode_contacts.append(contact_record)
        if args.trace_solved_contact_forces:
            from simfoundry.data.solved_contact_trace import read_solved_contact_forces
            force_record = read_solved_contact_forces(step, include_hand_contacts=args.trace_hand_contact_forces,include_arm_contacts=args.trace_arm_contact_forces)
            force_record['post_action_pose'] = snap(env, robot, hands)
            solved_contact_forces.append(force_record)
        sync_shipping_labels(env)
        if bool(terminated[0] or truncated[0]):
            break
    if args.wait_force_n or args.push_force_n:
        robot.permanent_wrench_composer.reset()
    episode = TrajectoryEpisode(rgb=np.stack(rgbs), q=np.stack(qs), action=np.stack(acts),
        instruction=prompt, scene_id=spec.scene_id, task_id=task_id,
        embodiment_id=spec.embodiment_id, joint_names=spec.joint_names,
        collect_meta={'environment_seed': args.environment_seed, 'expert_rear_bypass_m': args.expert_rear_bypass_m, 'bounded_coupled_ik': args.bounded_coupled_ik, 'inactive_retract_m': args.inactive_retract_m, 'waist_coordinated_expert': args.waist_coordinated_expert, 'motion_protocol': args.motion_protocol, 'waist_limit_rad': args.waist_limit_rad, 'extended_waist_diagnostic': args.extended_waist_diagnostic, 'waist_wait_tolerance_rad': args.waist_wait_tolerance_rad, 'waist_probe': args.waist_probe, 'waist_probe_amplitude_rad': args.waist_probe_amplitude_rad or .8*args.waist_limit_rad, 'layout': layout, 'layout_id': layout['layout_id'], 'zero_upper_body': True,
                      'box_xyz': initial['box'], 'mailer_xyz': initial['mailer'],
                      'box_quat_xyzw': initial_quats['box'].tolist(), 'mailer_quat_xyzw': initial_quats['mailer'].tolist(),
                      'push_assist': False, 'assist_frames': 0, 'expert': 'pi05_h10' if args.policy_port else 'paired_zero_cartesian',
                      'idle_diagnostic': args.idle, 'collection_role': args.role, 'exit_y': expert.exit_y, 'contact_x_bias': expert.contact_x_bias, 'contact_palm_z': expert.contact_palm_z,
                      'staging_palm_z': expert.staging_palm_z, 'contact_side_offset': expert.contact_side_offset, 'bounded_servo_memory': expert.bounded_servo_memory, 'frontal_bypass_plan': frontal_plan, 'frontal_bypass_requested': args.expert_frontal_bypass, 'contact_load_target_n': args.expert_contact_load_n, 'far_exit_y': args.expert_far_exit_y, 'goal_release': args.expert_goal_release, 'far_sweep_retreat_m': args.expert_far_sweep_retreat_m, 'max_contact_x': args.expert_max_contact_x, 'far_contact_offset': args.expert_far_contact_offset, 'base_contact_offset': args.expert_contact_offset, 'front_reposition_distance': expert.front_reposition_distance, 'front_reposition_measured_start': expert.front_reposition_measured_start, 'front_reposition_hold_yz': expert.front_reposition_hold_yz, 'crossed_contact_offset': args.expert_crossed_contact_offset, 'object_feedback_lead': expert.object_feedback_lead, 'contact_confirmed_sweep': expert.contact_confirmed_sweep, 'finger_heading_weight': args.finger_heading_weight,
                      'collision_pipeline': 'newton' if args.newton_contacts else 'mujoco',
                      'policy_action_step_cap': args.policy_max_action_step, 'settled_contact': args.settled_contact, 'recover_contact_height': args.recover_contact_height, 'wait_force_n': args.wait_force_n, 'wait_force_side': args.wait_force_side, 'push_force_n': args.push_force_n, 'push_force_axis': args.push_force_axis, 'push_force_start': args.push_force_start, 'wait_force_start': args.wait_force_start, 'waist_pilot_contract_sha256': waist_contract_hash, 'spatial_pilot_contract_sha256': spatial_contract_hash, 'recovery_contract_sha256': recovery_contract_hash})
    report = audit_rollout(task_id, episode.q, episode.action, trace, idle=args.idle, require_zero_action=not bool(args.policy_port), motion_protocol=args.motion_protocol, waist_limit_rad=args.waist_limit_rad, waist_wait_tolerance_rad=args.waist_wait_tolerance_rad)
    if args.waist_probe:
        report['reasons'].append('diagnostic waist probe is not a wait demonstration')
    if task_id != 'wait_no_package':
        for key in ('box', 'mailer'):
            drift = float(np.linalg.norm(np.asarray(initial[key])[:2] - np.asarray(layout[key + '_xyz'])[:2]))
            report['metrics'][key + '_reset_drift_m'] = drift
            if key + '_yaw' in layout:
                yaw = layout[key + '_yaw']
                requested_quat = np.array([0., 0., np.sin(yaw/2), np.cos(yaw/2)])
                angle_error = float(2*np.arccos(np.clip(abs(np.dot(requested_quat, initial_quats[key])), 0., 1.)))
                report['metrics'][key + '_reset_angle_error_rad'] = angle_error
                if angle_error > .03:
                    report['reasons'].append(f'{key} orientation drift during reset/settling')
            if drift > .015:
                report['reasons'].append(f'{key} moved {drift:.4f} m during reset/settling')
        report['passed'] = not report['reasons']
    rgb_means = episode.rgb.mean(axis=(1, 2, 3))
    frame_changes = [float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())
                     for a, b in zip(episode.rgb[:-1], episode.rgb[1:])]
    report['metrics']['min_frame_rgb_mean'] = float(rgb_means.min())
    report['metrics']['max_frame_rgb_change'] = max(frame_changes, default=0.)
    if float(rgb_means.min()) < 255 * .12:
        report['reasons'].append('one or more RGB frames too dark')
    if max(frame_changes, default=0.) > 40:
        report['reasons'].append('large RGB discontinuity: inspect rendering/reset')
    report['passed'] = not report['reasons']
    report['expert_end_mode'] = expert.mode
    report['frames'] = len(qs)
    folder = root / f"layout_{layout['layout_id']:04d}_{task_id}"
    folder.mkdir()
    # Raw failures and candidates stay outside training dataset directories.
    save_episode(episode, folder / 'raw.npz')
    np.savez_compressed(folder / 'trace.npz', **trace)
    np.savez_compressed(folder / 'parcel_orientation.npz', **{k: np.asarray(v) for k,v in parcel_orientations.items()})
    (folder / 'expert_control.json').write_text(json.dumps(expert_control, indent=2))
    if args.wait_force_n or args.push_force_n:
        (folder / 'external_force.json').write_text(json.dumps(force_log, indent=2))
    if args.policy_port:
        (folder / 'policy_inferences.json').write_text(json.dumps(infer_log))
        requested = np.asarray(raw_policy_actions)
        np.savez_compressed(folder / 'policy_raw_actions.npz', action=requested)
        report['metrics']['raw_policy_max_action_step_rad'] = float(np.abs(np.diff(requested[:,12:], axis=0)).max())
        report['metrics']['policy_modified_frames'] = int(np.any(np.abs(requested[:,12:] - episode.action[:,12:]) > 1e-6, axis=1).sum())
        report['metrics']['max_policy_action_modification_rad'] = float(np.abs(requested[:,12:] - episode.action[:,12:]).max())
    if bypass_log:
        (folder / 'bypass.json').write_text(json.dumps(bypass_log, indent=2))
    if frontal_plan is not None:
        (folder / 'frontal_bypass.json').write_text(json.dumps(dict(plan=frontal_plan,rows=frontal_log,training_ready=False),indent=2))
    if load_control_log:
        (folder / 'contact_load_control.json').write_text(json.dumps(load_control_log,indent=2))
    if viewer_log:
        (folder / 'viewer_observer.json').write_text(json.dumps(dict(role='diagnostic third-person observer; never policy input', frames=viewer_log, actual_visual_review='pending'),indent=2))
    if contact_center_log:
        (folder / 'contact_center_calibration.json').write_text(json.dumps(dict(rows=contact_center_log,training_ready=False),indent=2))
    if terminal_hold_log:
        (folder / 'terminal_joint_hold.json').write_text(json.dumps(dict(rows=terminal_hold_log,training_ready=False),indent=2))
    if coordination_log:
        (folder / 'coordination.json').write_text(json.dumps(coordination_log, indent=2))
    (folder / 'reset_contacts.json').write_text(json.dumps(reset_trace, indent=2))
    if args.trace_episode_contacts:
        (folder / 'episode_contacts.json').write_text(json.dumps({'sampling':'read-only last physics collision buffer after control action; not all substeps, not forces/impulses','rows':episode_contacts},indent=2))
    if args.trace_solved_contact_forces:
        (folder / 'solved_contact_forces.json').write_text(json.dumps({'sampling':'last physics tick after control action; solved force, not integrated impulse; separate output arrays; no solver refresh', 'rows':solved_contact_forces},indent=2))
    (folder / 'quality.json').write_text(json.dumps(report, indent=2))
    frames = np.linspace(0, len(rgbs)-1, 12).astype(int)
    sheet = Image.new('RGB', (640*4, 480*3))
    for i, t in enumerate(frames):
        sheet.paste(Image.fromarray(rgbs[t].transpose(1, 2, 0)), ((i%4)*640, (i//4)*480))
    sheet.save(folder / 'contact_sheet.jpg')
    print(json.dumps({'layout': layout['layout_id'], 'task': task_id, **report}), flush=True)
    return episode, report


def main():
    root = Path(args.out_dir)
    root.mkdir(parents=True, exist_ok=False)
    (root / 'STATUS.json').write_text(json.dumps({'training_ready': False, 'status': 'collecting_diagnostics'}))
    if waist_admission is not None:
        contract_bytes = waist_admission.contract_path.read_bytes()
        if hashlib.sha256(contract_bytes).hexdigest() != waist_contract_hash:
            raise ValueError('Waist contract changed before output snapshot')
        (root/'waist_pilot_contract.json').write_bytes(contract_bytes)
    if args.spatial_pilot_contract:
        (root/'spatial_pilot_contract.json').write_bytes(args.spatial_pilot_contract.read_bytes())
    if args.recovery_pilot_contract:
        (root/'recovery_pilot_contract.json').write_bytes(args.recovery_pilot_contract.read_bytes())
    if args.diagnostic_layout_json:
        (root/'explicit_layout.json').write_bytes(Path(args.diagnostic_layout_json).read_bytes())
    paths = [ROOT / 'simfoundry/calibration/sorting_station.py', ROOT / 'simfoundry/data/spatial_protocol.py', ROOT / 'simfoundry/data/diverse_layouts.py', ROOT / 'simfoundry/data/recovery_protocol.py', Path(__file__).resolve(), ROOT / 'simfoundry/data/paired_sorting.py', ROOT / 'simfoundry/robots/g1_assets.py', ROOT / 'simfoundry/data/sorting_cartesian_expert.py']
    paths.extend([ROOT / 'simfoundry/data/waist_coordination.py', ROOT / 'simfoundry/data/bounded_ik.py', ROOT / 'simfoundry/data/reach_sweep.py', ROOT / 'simfoundry/data/contact_load_control.py', ROOT / 'simfoundry/data/frontal_bypass.py', ROOT / 'simfoundry/data/fingertip_bypass.py', ROOT / 'simfoundry/data/solved_contact_trace.py', ROOT / 'simfoundry/data/top_contact_bypass.py', ROOT / 'simfoundry/data/top_contact_visibility.py', ROOT / 'assets/robots/g1_hand_support_vertices.json'])
    paths.extend([ROOT / 'simfoundry/data/projected_support_reference.py', ROOT / 'simfoundry/data/front_clearance_progress.py'])
    paths.extend([ROOT / 'simfoundry/data/front_top_route.py', ROOT / 'simfoundry/data/tabletop_route_candidates.py'])
    paths.append(ROOT / 'simfoundry/data/waist_pilot_protocol.py')
    paths.append(ROOT / 'simfoundry/data/object_relative_push.py')
    paths.append(ROOT / 'simfoundry/data/terminal_joint_hold.py')
    paths.append(ROOT / 'simfoundry/data/contact_normal_constraint.py')
    paths.append(ROOT / 'simfoundry/data/contact_center_calibration.py')
    paths.append(ROOT / 'simfoundry/data/bounded_top_lead.py')
    paths.append(ROOT / 'simfoundry/data/confirmed_position_release.py')
    paths.extend([ROOT / 'simfoundry/data/initial_top_route.py', ROOT / 'simfoundry/data/initial_top_route_candidate.py'])
    paths.extend([ROOT / 'simfoundry/data/hand_obstacle_clearance.py', ROOT / 'simfoundry/data/cross_axis_admittance.py', ROOT / 'simfoundry/data/top_contact_load_geometry.py', ROOT / 'simfoundry/data/top_push_contact_geometry.py', ROOT / 'simfoundry/data/support_vertex_hysteresis.py', ROOT / 'simfoundry/data/parcel_collision_geometry.py', ROOT / 'simfoundry/scene_bridge/isaac_cfg.py', ROOT / 'scenes/sorting_station_g1_23/twin/layout.json'])
    for path in paths:
        snapshot = root / 'source_snapshot' / path.relative_to(ROOT)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(path.read_bytes())
    (root / 'provenance.json').write_text(json.dumps({
        'args': vars(args), 'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'physics': 'Newton MJWarp (existing scene backend)', 'training_ready': False,
    }, indent=2, default=str))
    spec = resolve_scene_env('sorting_station_g1_23')
    default = u1_sorting_default_qpos_np(zero_upper_body=True)
    cfg = spec.env_cfg_cls()
    cfg.scene.num_envs = 1
    if args.environment_seed is not None:
        cfg.seed = args.environment_seed
    cfg.sim.device = args.device
    # Keep existing <=320-frame behavior; long diagnostics need room for the
    # 60-step warmup and recorded horizon without auto-reset/truncation.
    configured_step_dt = float(cfg.sim.dt) * int(cfg.decimation)
    cfg.episode_length_s = max(40., (max(args.steps, args.wait_steps) + 90) * configured_step_dt)
    (root / 'runtime_budget.json').write_text(json.dumps(dict(
        requested_push_frames=args.steps, requested_wait_frames=args.wait_steps,
        configured_step_dt_s=configured_step_dt, warmup_frames=60,
        environment_timeout_s=cfg.episode_length_s, training_ready=False), indent=2))
    if args.newton_contacts:
        cfg.sim.physics.default.solver_cfg.use_mujoco_contacts = False
    cfg.scene.robot.init_state.joint_pos = dict(zip(G1_U1_23DOF_JOINT_NAMES, default.tolist()))
    env = None
    results = []
    try:
        env = ManagerBasedRLEnv(cfg=cfg)
        if args.environment_seed is not None and env.cfg.seed != args.environment_seed:
            raise RuntimeError('Environment seed differs from explicitly requested value')
        (root/'runtime_randomization.json').write_text(json.dumps(dict(
            requested_environment_seed=args.environment_seed, configured_environment_seed=env.cfg.seed,
            reset_environment_seed_each_episode=args.environment_seed is not None,
            layout_seed_scope='Independent numpy RNG for parcel reset/appearance',
            policy_inference_seed=args.eval_seed if args.policy_port else None,
            bitwise_physics_determinism_verified=False, training_ready=False), indent=2))
        for i in range(args.layout_start, args.layout_start + args.layouts):
            layout = waist_admission.layout(i) if waist_admission is not None else (dict(explicit_layout) if (args.diagnostic_layout_json or args.spatial_pilot_contract) else sample_layout(i))
            for key in ('box_xyz', 'mailer_xyz'):
                layout[key][0] += args.layout_x_offset
            episodes, reports = [], []
            for task_id in ('push_box_to_bin', 'nudge_mailer_to_bin'):
                ep, report = collect(env, spec, layout, task_id, root, default)
                episodes.append(ep)
                reports.append(report)
            prompts = ({key: VLA_SORTING_UNIFIED_PROMPT for key in PAIRED_SORTING_PROMPTS}
                       if args.policy_port and args.prompt_variant == 'unified_ablation' else PAIRED_SORTING_PROMPTS)
            pair = audit_pair(*episodes, prompts=prompts)
            results.append({'layout': layout, 'episodes': reports, 'pair': pair})
            (root / 'manifest.json').write_text(json.dumps(results, indent=2))
            if not args.policy_port and (not pair['passed'] or not all(r['passed'] for r in reports)):
                raise RuntimeError('Quality gate failed. Stop; no retries or training export. See manifest.json.')
        for i in range(args.wait_episodes):
            layout = waist_admission.layout(args.wait_layout_start+i,wait=True) if waist_admission is not None else sample_layout(args.wait_layout_start+i)
            _, report = collect(env, spec, layout, 'wait_no_package', root, default)
            results.append({'layout': layout, 'episodes': [report]})
            (root / 'manifest.json').write_text(json.dumps(results, indent=2))
            if not args.policy_port and not report['passed']:
                raise RuntimeError('Wait quality gate failed.')
        (root / 'STATUS.json').write_text(json.dumps({'training_ready': False, 'status': 'evaluation_complete' if args.policy_port else 'numeric_pass_visual_review_pending'}))
    except Exception as exc:
        (root / 'STATUS.json').write_text(json.dumps({'training_ready': False, 'status': 'blocked_quality_or_runtime', 'error': str(exc)}))
        raise
    finally:
        if env is not None:
            env.close()
        app.close()

if __name__ == '__main__':
    main()
