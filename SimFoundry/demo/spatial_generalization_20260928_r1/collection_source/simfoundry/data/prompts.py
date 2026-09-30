"""Language instructions written at collect time (not rewritten later)."""

# Same sentence as real lerobot_v3.0 / PI0.5 closed-loop eval.
VLA_SORTING_UNIFIED_PROMPT = (
    "Sort the package on the table by type. If there is no package on the table, keep both "
    "arms still and wait. If it is a black bag, press and hold the bag down with the left "
    "hand, then push it to the left sorting area. If it is a box, press and hold the box "
    "down with the right hand, then push it to the right sorting area."
)

# Paired-scene experiment authorized on 2026-09-24; preserve through conversion.
PAIRED_SORTING_PROMPTS = {
    "push_box_to_bin": "Push the brown box to the right with your right hand.",
    "nudge_mailer_to_bin": "Push the black bag to the left with your left hand.",
    "wait_no_package": "Keep both arms still and wait.",
}
