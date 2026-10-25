# PowerDesigner Overlap Detection & Collision Resolution Guide

In automated PowerDesigner modeling, visual overlaps usually fall into three failure modes:
1. **Activation Bar Collisions**: Multiple synchronous or recursive calls on the same lifeline share the exact same X coordinate, collapsing into an unreadable solid black rectangle.
2. **Symbol Bounding Box Intersections**: Use cases, actors, classes, or combined fragments intersect each other, or text labels clip over connecting lines.
3. **Draft / Stray Note Contamination**: Lingering development status notes (like "实现中，待整链验收" or "管理员兼有教学管理权限...") cluttering submission-grade diagrams.

This reference provides the algorithms and audit checks to detect and resolve all three.

---

## 1. Geometric Collision Detection (AABB)

Every symbol in PowerDesigner has a logical bounding box defined by:
- Center position: `(X, Y)`
- Dimensions: `Width W, Height H`

### Axis-Aligned Bounding Box (AABB) Check
Given symbol A and symbol B, with a clearance buffer `clearance`:

```text
Left_A   = X_A - W_A / 2
Right_A  = X_A + W_A / 2
Bottom_A = Y_A - H_A / 2
Top_A    = Y_A + H_A / 2
```

We compute horizontal and vertical distances:
- If `Right_A < Left_B`, `dist_x = Left_B - Right_A`
- If `Right_B < Left_A`, `dist_x = Left_A - Right_B`
- Otherwise, they overlap horizontally, so `dist_x = 0`

Similarly for vertical distance `dist_y`:
- If `Top_A < Bottom_B`, `dist_y = Bottom_B - Top_A`
- If `Top_B < Bottom_A`, `dist_y = Bottom_A - Top_B`
- Otherwise, `dist_y = 0`

Two symbols collide if:
`dist_x < clearance and dist_y < clearance` (default `clearance = 150` units).

### Auto-Resolution
When an overlap is detected between symbol A and symbol B:
- **Vertical layouts** (Use Cases, Class trees): Shift B downward:
  `Y_B = Bottom_A - (H_B / 2) - min_spacing`
- **Horizontal layouts** (Lifelines, System Boundaries): Shift B rightward:
  `X_B = Right_A + (W_B / 2) + min_spacing`

---

## 2. Activation Bar Overlap Auditing

### Overlap Condition
Given two activation intervals on the same lifeline:
- `Bar_1 = [Y_start_1, Y_end_1, depth_1]`
- `Bar_2 = [Y_start_2, Y_end_2, depth_2]`

A collision defect exists if their vertical ranges intersect in time/Y and their depths are identical (`depth_1 == depth_2`).

### Resolution Rule
When intervals overlap vertically, their horizontal depths must be incremented:
- `depth_2 = depth_1 + 1`
- Horizontal position shifts by `X_offset = depth * 120` units.

---

## 3. Automated Diagram Audit Checklist

Before exporting any diagram to PNG or submitting to a course/enterprise report:

| Check Item | Acceptance Criteria | Auto-Fix Method |
| :--- | :--- | :--- |
| **Symbol Intersections** | 0 overlapping pairs among all diagram symbols (`clearance >= 150`) | `CollisionDetector.auto_resolve_vertical_overlaps()` |
| **Activation Bar Overlaps** | 0 same-depth intersecting activation bars | Call-stack auto-nesting offset (`X_offset = depth * 120`) |
| **Label-Line Clearances** | Message/link labels must not touch arrowheads or lifelines | `Y_offset = +120` above message line |
| **Draft / Stray Annotations** | 0 unapproved keywords (`实现中`, `待验收`, `计划图等同`) | `CollisionDetector.strip_draft_notes()` |
