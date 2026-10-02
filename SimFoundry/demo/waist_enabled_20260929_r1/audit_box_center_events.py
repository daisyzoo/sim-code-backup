"""Original full recovery command/measurement/capture audit with verified paths.
Only the original straight-waypoint construction is replaced by an independent
piecewise-plan check. All original measured bounds, loads,240ticks and capture
mathematics are retained. No candidate controller imports.
"""
from pathlib import Path
import ast,copy
import numpy as np
from audit_unloaded_wrist_prior_live import near
from audit_box_center_plan import PlanAudit

class EventAudit(PlanAudit):
 pass

_source=Path(__file__).with_name('audit_recontact_pose_events.py');_tree=ast.parse(_source.read_text());_class=next(n for n in _tree.body if isinstance(n,ast.ClassDef) and n.name=='EventAudit');_f=copy.deepcopy(next(n for n in _class.body if isinstance(n,ast.FunctionDef) and n.name=='verify'));_old=copy.deepcopy(_f)
_blocks=[n for n in ast.walk(_f) if isinstance(n,ast.If) and ast.unparse(n.test)=='not self.active'];assert len(_blocks)==1;_block=_blocks[0];_index=next(i for i,n in enumerate(_block.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='count');_removed=copy.deepcopy(_block.body[_index:_index+3]);assert ast.unparse(_removed[1]).startswith('expected = np.array(') and ast.unparse(_removed[2])=="near(created['waypoints'], expected, 1e-10)"
_block.body[_index:_index+3]=ast.parse('expected=self.verified_waypoints(created,q,scene,step)').body;_new=copy.deepcopy(_f);_block.body[_index:_index+1]=_removed;assert ast.dump(_f)==ast.dump(_old)
_ns=dict(np=np,near=near);exec(compile(ast.fix_missing_locations(ast.Module(body=[_new],type_ignores=[])),str(Path(__file__)),'exec'),_ns);EventAudit.verify=_ns['verify']
# Rotation is referenced during per-step scene-motion checks in the original.
from scipy.spatial.transform import Rotation
_ns['Rotation']=Rotation
