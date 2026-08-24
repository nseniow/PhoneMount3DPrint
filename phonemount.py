import cadquery as cq

# Base block dimensions (mm)
base_length = 78
base_depth = 12.75
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
window_width = 67
window_top_margin = 0
window_bottom_margin = 30

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

# --- Thicken the back wall to fit bolt heads ---
back_extra_thickness = 3          # added onto the existing 3mm wall_thickness
total_back_thickness = wall_thickness + back_extra_thickness   # 10mm total

back_wall_extension = (
    cq.Workplane("XY")
    .workplane(offset=wall_z_bottom)
    .center(0, -(outer_depth / 2 + back_extra_thickness / 2))
    .rect(outer_length, back_extra_thickness)
    .extrude(wall_total_height)
)

phone_mount = phone_mount.union(back_wall_extension)

# --- Bolt holes: 6mm through-hole + 11.5mm counterbore for the head ---
bolt_hole_diameter = 6
bolt_head_diameter = 11.5
bolt_head_depth = 3.5

bolt_spacing = 25
bolt_z = wall_z_bottom + wall_total_height * 0.85

inner_back_y = -inner_depth / 2   # inner face, facing the phone cavity
bolt_positions = [-bolt_spacing, bolt_spacing]

bolt_cutters = []
for x in bolt_positions:
    # 6mm hole, all the way through the thickened back wall
    through_hole = cq.Solid.makeCylinder(
        bolt_hole_diameter / 2,
        total_back_thickness,
        cq.Vector(x, inner_back_y, bolt_z),
        cq.Vector(0, -1, 0)
    )
    # 11.5mm counterbore, recessed into the inner (phone-facing) side only
    counterbore = cq.Solid.makeCylinder(
        bolt_head_diameter / 2,
        bolt_head_depth,
        cq.Vector(x, inner_back_y, bolt_z),
        cq.Vector(0, -1, 0)
    )
    bolt_cutters.append(through_hole)
    bolt_cutters.append(counterbore)

bolt_cutter_shape = cq.Workplane("XY").newObject(bolt_cutters)

result = phone_mount.cut(bolt_cutter_shape)

cq.exporters.export(result, "phonemount.stl")