# Worldlab development

- This project targets Isaac Sim 6.1.0.0; use `.venv/bin/python` for runtime.
- Use `.venv-tools/bin/python` for asset conversion and CPU tests. Do not add
  standalone `usd-core` to the Isaac Sim runtime environment.
- Preserve original `World/` assets. Generated assets belong in `generated/`;
  diagnostic outputs, logs and acceptance reports belong in `outputs/`.
- Keep each original asset untouched. Normalize each input format into a verified
  shared scene coordinate system, then author common placement on the scene parent.
  Do not reuse Kitchen rotation/height for SPZ, GLB or Blender USD without alignment QA.
- Use static triangle-mesh collisions for room shells and stairs. Whole-room convex
  hulls incorrectly fill interiors. Do not add hidden fallback floors to hide holes.
  Dynamic objects/door leaves need separately designed rigid bodies and colliders.
- `inspect_source.py` produces CPU point diagnostics, not Isaac Sim renders.
- Only claim runtime validation after checking real 6.1 images and physics reports.
- Do not upgrade the sibling SIM/IsaacLab environments or resume paused training.
- Run the narrow tests with `.venv-tools/bin/python -m pytest tests -q` and perform
  a runtime capture after changing scene composition or the viewer.

## Multi-scene design and official skills

- Read `docs/multi_scene_design.md` and `configs/scene_catalog.json` before extending
  importers. The catalog indexes executable `configs/scenes/<id>.json`; pending transforms must not
  silently become identity transforms or Kitchen defaults.
- Keep mesh GLB hierarchy, UVs, textures and material bindings for appearance.
  `assets.load_mesh().to_mesh()` is a collider helper, not a visual importer.
- Blender files are editable sources; invoke Blender in a separate process.
  Do not install bpy or conversion-only USD packages into the runtime environment.
- A hallway's lowest point may be a downstairs step. Anchor its main landing using
  an explicit reference, not the minimum bounding-box Z.
- Read relevant NVIDIA skills on demand under
  `.venv/lib/python3.12/site-packages/isaacsim/skills/<name>/SKILL.md`:
  `usd-composition-architecture` for layer structure, `usd-pipeline` for asset
  measurement/placement, `isaac-sim-rendering` for render checks,
  `physics-simulation` for physics and `isaac-sim-validator` for static checks.
  `isaac-sim-assets` concerns asset-root access, not format conversion.
- Use `source scripts/skills_env.sh` when an official helper needs its environment
  contract. This is a pip installation: run runtime scripts with `.venv/bin/python`,
  not an assumed installation-root `python.sh`. Never execute source-tree-only
  helpers blindly. Skills must be read; their presence does not imply invocation.
- Record skill paths/versions and actual commands/results in acceptance reports.
  Static skill validation does not replace per-scene GPU and contact evidence.

- New-scene entry points: `run_scene.sh --scene <id>` and
  `.venv-tools/bin/python scripts/build_scene.py --scene <id>`.
  See `docs/scene_usage.md` and `docs/scene_acceptance_20261014.md`.
- Never overwrite a completed acceptance run. Use a new output folder and keep
  source/scene/runtime-code hashes with each report. Distinguish GPU RGB rendering
  from the current CPU PhysX contact acceptance backend.
