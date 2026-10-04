"""Resolve independent audit assets from the guard's already bound source hashes.
Works from an isolated stage without guessing repository depth or trusting logs.
"""
from pathlib import Path
import hashlib
from audit_unloaded_wrist_prior_live import HandModel

def independent_hand_model(guard):
 sources=guard.model.source_sha256
 def one(name):
  matches=[Path(p) for p in sources if Path(p).name==name]
  if len(matches)!=1:raise ValueError('Ambiguous independent hand asset '+name)
  p=matches[0]
  if hashlib.sha256(p.read_bytes()).hexdigest()!=sources[str(p)]:raise ValueError('Changed independent hand asset '+name)
  return p
 return HandModel(one('g1_23dof_rev_1_0_u1_black.urdf'),one('g1_hand_support_vertices.json'))
