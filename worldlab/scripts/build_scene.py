#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from worldlab.scenes import build_scene
p=argparse.ArgumentParser();p.add_argument('--scene',required=True)
a=p.parse_args();build_scene(a.scene)
