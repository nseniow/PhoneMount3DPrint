import cadquery as cq

# Base block dimensions (mm)
base_length = 78
base_depth = 14
base_height = 25

base = (
    cq.Workplane("XY")
    .box(base_length, base_depth, base_height)
)

# Oval slot dimensions (cut from top)
slot_length = 14
slot_width = 9
slot_depth = 18

oval_cutter = (
    cq.Workplane("XY")
    .workplane(offset=base_height / 2)
    .slot2D(slot_length, slot_width, angle=0)
    .extrude(-slot_depth)
)

# Rectangular through-slot dimensions (top to bottom)
rect_length = 9
rect_width = 3

rect_cutter = (
    cq.Workplane("XY")
    .workplane(offset=base_height / 2)
    .rect(rect_length, rect_width)
    .extrude(-base_height)
)

# Rectangular slot cut upward from the bottom
bottom_rect_length = 12
bottom_rect_width = 7
bottom_rect_depth = 6

bottom_rect_cutter = (
    cq.Workplane("XY")
    .workplane(offset=-base_height / 2)
    .rect(bottom_rect_length, bottom_rect_width)
    .extrude(bottom_rect_depth)
)

base_with_slots = base.cut(oval_cutter).cut(rect_cutter).cut(bottom_rect_cutter)

# Wall around the phone
wall_expand = 3
wall_thickness = 3
wall_height_above_top = 90

outer_length = base_length + 2 * wall_expand
outer_depth = base_depth + 2 * wall_expand
inner_length = outer_length - 2 * wall_thickness
inner_depth = outer_depth - 2 * wall_thickness

wall_total_height = base_height + wall_height_above_top
wall_z_bottom = -base_height / 2

wall = (
    cq.Workplane("XY")
    .workplane(offset=wall_z_bottom)
    .rect(outer_length, outer_depth)
    .rect(inner_length, inner_depth)
    .extrude(wall_total_height)
)

phone_mount = base_with_slots.union(wall)

# Window cut into the front wall
window_side_margin = 5
window_top_margin = 0
window_bottom_margin = 40

window_width = outer_length - 2 * window_side_margin
window_height = wall_total_height - window_top_margin - window_bottom_margin
window_center_z = wall_z_bottom + window_bottom_margin + window_height / 2

front_y = -outer_depth / 2

window_cutter = (
    cq.Workplane("XZ")
    .workplane(offset=front_y)
    .center(0, window_center_z)
    .rect(window_width, window_height)
    .extrude(wall_thickness * 2, both=True)
)

phone_mount = phone_mount.cut(window_cutter)

# Pegboard pegs — on the true back face, opposite the window
peg_diameter = 7.25     # updated thickness
peg_length = 25         # updated length
peg_spacing = 25
peg_z = wall_z_bottom + wall_total_height * 0.85   # moved up to ~85%

back_y = -outer_depth / 2
peg_positions = [-peg_spacing, 0, peg_spacing]

peg_solids = [
    cq.Solid.makeCylinder(
        peg_diameter / 2,
        peg_length,
        cq.Vector(x, back_y, peg_z),
        cq.Vector(0, -1, 0)
    )
    for x in peg_positions
]

pegs = cq.Workplane("XY").newObject(peg_solids)

result = phone_mount.union(pegs)

cq.exporters.export(result, "phonemount.stl")