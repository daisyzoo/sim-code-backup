"""Temporary diagnostic video/dataloader roundtrip; never admits source to training."""
from pathlib import Path
import os,sys,json,hashlib,tempfile,importlib.util
os.environ.update(HF_HUB_OFFLINE='1',OMP_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false')
root=Path(__file__).resolve().parent;sim=root.parents[1]
repo=sim.parent/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src'
sys.path[:0]=[str(sim),str(repo)]
import numpy as np
import torch
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from simfoundry.data.schema import load_episode
torch.set_num_threads(1)
spec=importlib.util.spec_from_file_location('converter',sim/'scripts/prepare_paired_sorting_lerobot.py');converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
records=[];sources=[]
for p in sorted((root/'frontal_top_drag_fast_r1').glob('case_*/layout_*/raw.npz')):
    ep=load_episode(p)
    assert ep.collect_meta['collection_role']=='diagnostic' and ep.collect_meta['motion_protocol']=='waist_yaw_enabled_v1'
    assert np.max(abs(ep.q[0,converter.INDICES]))<1e-4 and np.max(abs(ep.action[0,converter.INDICES]))<1e-4
    sources.append(ep);records.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),frames=len(ep.q)))
features={k:dict(dtype='float32',shape=(11,),names=[converter.JOINT_ORDER]) for k in ('observation.state','action')}
features['observation.images.color_0']=dict(dtype='video',shape=(480,640,3),names=['height','width','channel'])
with tempfile.TemporaryDirectory(prefix='waist_diagnostic_video_') as temp:
    dest=Path(temp)/'dataset'
    ds=LeRobotDataset.create(repo_id='diagnostic/waist_roundtrip_not_for_training',root=dest,fps=15,robot_type='Unitree_G1_23Dof_Arms5_Waist1',features=features,use_videos=True,image_writer_processes=0,image_writer_threads=2)
    for ep in sources:
        for t in range(len(ep.q)):
            ds.add_frame({'observation.state':ep.q[t,converter.INDICES], 'action':ep.action[t,converter.INDICES], 'observation.images.color_0':ep.rgb[t].transpose(1,2,0),'task':ep.instruction})
        ds.save_episode()
    ds.finalize();del ds
    loaded=LeRobotDataset('diagnostic/waist_roundtrip_not_for_training',root=dest,video_backend='pyav',delta_timestamps={'action':[i/15 for i in range(10)]})
    checks=[];offset=0
    for ep in sources:
        for t in [0,1,80,159,310,315,319]:
            item=loaded[offset+t];state=item['observation.state'].numpy();action=item['action'].numpy()
            expected=ep.action[np.minimum(np.arange(t,t+10),len(ep.q)-1)][:,converter.INDICES]
            np.testing.assert_allclose(state,ep.q[t,converter.INDICES],rtol=0,atol=1e-6)
            np.testing.assert_allclose(action,expected,rtol=0,atol=1e-6)
            assert item['task']==ep.instruction
            expected_pad=np.arange(t,t+10)>=len(ep.q)
            np.testing.assert_array_equal(item['action_is_pad'].numpy(),expected_pad)
            rgb=item['observation.images.color_0'].numpy()
            if rgb.shape[-1]==3:rgb=rgb.transpose(2,0,1)
            if rgb.max()<=1.5:rgb=rgb*255
            mae=float(np.abs(rgb.astype(float)-ep.rgb[t]).mean());assert mae<8.,mae
            checks.append(dict(task=ep.task_id,frame=t,image_mae=mae,state_max_error=float(np.max(abs(state-ep.q[t,converter.INDICES]))),h10_max_error=float(np.max(abs(action-expected))),padding_matches=True))
        offset+=len(ep.q)
    # Check every scalar row without repeatedly decoding all 640 video frames.
    import pyarrow.parquet as pq
    import pandas as pd
    table=pd.concat([pq.read_table(p).to_pandas() for p in sorted((dest/'data').glob('chunk-*/file-*.parquet'))],ignore_index=True)
    for i,ep in enumerate(sources):
        rows=table[table.episode_index==i].sort_values('frame_index');assert len(rows)==len(ep.q)
        np.testing.assert_array_equal(rows.frame_index,np.arange(len(ep.q)))
        np.testing.assert_allclose(np.stack(rows['observation.state']),ep.q[:,converter.INDICES],rtol=0,atol=1e-6)
        np.testing.assert_allclose(np.stack(rows.action),ep.action[:,converter.INDICES],rtol=0,atol=1e-6)
        np.testing.assert_allclose(rows.timestamp,np.arange(len(ep.q))/15.,rtol=0,atol=1e-5)
    report=dict(passed=True,training_ready=False,source_records=records,scalar_rows_verified=len(table),horizon=10,video_loader_checks=checks,scope='Temporary diagnostic-only dataset uses same schema, joint mapping and LeRobot add_frame/save/finalize path as production converter. All scalar rows, timestamps and episode boundaries checked; sampled decoded RGB, unchanged prompt, h10 actions and padding checked. Uses failed diagnostic trajectories, bypasses no production admission gate and publishes no training data. Does not certify production admission support, policy prediction or simulator execution.',temporary_dataset_deleted_after_context=True)
(root/'WAIST_VIDEO_LOADER_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('video_loader_checks','source_records')},indent=2))
