#!/usr/bin/env python3
"""Loopback-only frozen trajectory replay, not a trained policy or data exporter."""
import argparse,hashlib,json,pickle,socket,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI

def exact(conn,n):
    result=bytearray()
    while len(result)<n:
        chunk=conn.recv(n-len(result))
        if not chunk:raise ConnectionError('Incomplete request')
        result.extend(chunk)
    return bytes(result)

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--port',type=int,default=0);a=p.parse_args()
    manifest=json.loads(a.manifest.read_text());actions={};hashes={}
    for task,row in manifest['tasks'].items():
        if task not in ('push_box_to_bin','nudge_mailer_to_bin'):raise ValueError('Only paired push replay supported')
        path=Path(row['path']);digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=row['sha256']:raise ValueError('Replay source hash mismatch')
        with np.load(path,allow_pickle=False) as z:act=z['action'].copy()
        if act.shape!=(160,23) or not np.isfinite(act).all():raise ValueError('Invalid replay actions')
        if np.abs(act[0,12:]).max()>=1e-4 or np.abs(act[:,12]).max()>=1e-6:raise ValueError('Replay violates zero start/waist')
        if np.abs(np.diff(act[:,12:],axis=0)).max()>.080001:raise ValueError('Abrupt replay source')
        if np.any(act<np.asarray(U1_JOINT_LIMIT_LO)-1e-6) or np.any(act>np.asarray(U1_JOINT_LIMIT_HI)+1e-6):raise ValueError('Out-of-limit replay source')
        prompt=PAIRED_SORTING_PROMPTS[task];actions[prompt]=act[:,[*range(13,23),12]];hashes[prompt]=digest
    if len(actions)!=2:raise ValueError('Manifest must supply both tasks, including explicitly labelled companion controls if needed')
    a.out.mkdir(parents=True,exist_ok=False);cursor=0;active=None;stop=False
    with socket.socket() as server:
        server.bind(('127.0.0.1',a.port));server.listen(2)
        (a.out/'READY.json').write_text(json.dumps(dict(port=server.getsockname()[1],manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest(),purpose='frozen replay, not learned policy',training_ready=False)))
        while not stop:
            conn,_=server.accept()
            with conn:
                conn.settimeout(90)
                try:
                    length=struct.unpack('!I',exact(conn,4))[0]
                    if length>32*1024**2:raise ValueError('Request too large')
                    request=pickle.loads(exact(conn,length));cmd=request.get('cmd')
                    if cmd=='ping':reply=dict(ok=True,cmd='pong')
                    elif cmd=='reset_seed':cursor=0;active=None;reply=dict(ok=True,seed=request.get('seed'))
                    elif cmd=='shutdown':stop=True;reply=dict(ok=True,cmd='bye')
                    elif cmd=='infer':
                        task=request.get('task');state=np.asarray(request['state'])
                        if task not in actions or (active is not None and active!=task):raise ValueError('Unexpected or changed task')
                        if state.shape!=(11,) or not np.isfinite(state).all():raise ValueError('Invalid state')
                        if cursor==0 and np.abs(state).max()>=1e-4:raise ValueError('Replay must start from zero state')
                        if cursor>=160:raise ValueError('Replay exhausted; explicit reset required')
                        begin=cursor;chunk=actions[task][begin:begin+10].copy();cursor+=len(chunk);active=task
                        reply=dict(ok=True,actions=chunk,infer_ms=0.,replay_source_sha256=hashes[task],replay_start=begin)
                        with (a.out/'REQUESTS.jsonl').open('a') as f:f.write(json.dumps(dict(task=task,start=begin,stop=cursor,sha256=hashes[task]))+'\n')
                    else:raise ValueError('Unknown command')
                except Exception as exc:reply=dict(ok=False,error=type(exc).__name__+': '+str(exc))
                data=pickle.dumps(reply,protocol=pickle.HIGHEST_PROTOCOL);conn.sendall(struct.pack('!I',len(data))+data)

if __name__=='__main__':main()
