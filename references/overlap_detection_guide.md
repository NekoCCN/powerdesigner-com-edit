# PowerDesigner Overlap Detection & Collision Resolution Guide (重叠检查与自动规避规范)

In automated PowerDesigner modeling, visual overlaps fall into three distinct failure modes:
1. **Activation Bar Collisions (激活条重合)**: Multiple synchronous or recursive calls on the same lifeline sharing the exact same X coordinate, collapsing into an unreadable solid block.
2. **Symbol Bounding Box Intersections (图元/文字重合)**: Use cases, actors, classes, or combined fragments intersecting each other or text labels clipping over connecting lines.
3. **Draft / Stray Note Contamination (草稿文字压盖与残留)**: Lingering development status notes (e.g. `（实现中，待整链验收）`, `管理员兼有教学管理权限...`) cluttering submission-grade diagrams.

This reference provides the formal algorithms and automated audit checks to detect and resolve all three.

---

## 1. Geometric Collision Detection (AABB)

Every symbol in PowerDesigner possesses a logical bounding box defined by:
- Center or top-left position: $(X, Y)$
- Dimensions: $\text{Width } W, \text{Height } H$

### Axis-Aligned Bounding Box (AABB) Formula:
For symbol $A$ and symbol $B$ with a clearance buffer $\delta$:
$$\text{Left}_A = X_A - \frac{W_A}{2} - \delta, \quad \text{Right}_A = X_A + \frac{W_A}{2} + \delta$$
$$\text{Bottom}_A = Y_A - \frac{H_A}{2} - \delta, \quad \text{Top}_A = Y_A + \frac{H_A}{2} + \delta$$

Two symbols collide if and only if:
$$\text{Right}_A > \text{Left}_B \land \text{Left}_A < \text{Right}_B \land \text{Top}_A > \text{Bottom}_B \land \text{Bottom}_A < \text{Top}_B$$

### Auto-Resolution (自动避让排布):
When an overlap is detected between $A$ and $B$:
- For vertical layouts (Use Cases, Class trees): Shift $B$ downward:
  $$Y_B \leftarrow Y_A - \frac{H_A + H_B}{2} - \delta_{\text{safe}}$$
- For horizontal layouts (Lifelines, System Boundaries): Shift $B$ rightward:
  $$X_B \leftarrow X_A + \frac{W_A + W_B}{2} + \delta_{\text{safe}}$$

---

## 2. Activation Bar Overlap Auditing (时序图激活条检测)

### Overlap Condition:
Given two activation intervals on the same lifeline $L$:
$$\text{Bar}_1 = [Y_{\text{start}, 1}, Y_{\text{end}, 1}, \text{depth}_1], \quad \text{Bar}_2 = [Y_{\text{start}, 2}, Y_{\text{end}, 2}, \text{depth}_2]$$

A collision defect exists if:
$$[Y_{\text{start}, 1}, Y_{\text{end}, 1}] \cap [Y_{\text{start}, 2}, Y_{\text{end}, 2}] \neq \emptyset \quad \text{and} \quad \text{depth}_1 = \text{depth}_2$$

### Verification Rule:
- **0 Overlaps Guarantee**: When intervals overlap in time/Y, their horizontal depths must satisfy:
  $$\text{depth}_2 \ge \text{depth}_1 + 1$$
  and horizontal position must shift by $\Delta X = \text{depth} \times 120$ units.

---

## 3. Automated Diagram Audit Checklist

Before exporting any diagram to PNG or submitting to a course/enterprise report:

| Check Item | Acceptance Criteria | Auto-Fix Method |
|---|---|---|
| **Symbol Intersections** | 0 overlapping pairs among all diagram symbols ($\delta \ge 150$) | `CollisionDetector.auto_resolve_overlaps()` |
| **Activation Bar Overlaps** | 0 same-depth intersecting activation bars | Call-stack auto-nesting offset formula |
| **Label-Line Clearances** | Message/link labels must not touch arrowheads or lifelines | $Y_{\text{offset}} = +120$ above message line |
| **Draft / Stray Annotations** | 0 keywords (`实现中`, `待验收`, `兼有教学管理`, `计划图等同`) | `CollisionDetector.strip_draft_notes()` |
| **Canvas Margins** | No huge blank margins exceeding 15% of diagram dimension | PIL bounding-box auto-crop with 25px padding |
| **Printable Page Fit** | Export width $\le 5.5$ inches for 16-开 (B5) reports | High-DPI scaling down to safe page width |
