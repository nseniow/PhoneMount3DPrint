import math
import cadquery as cq

# Base block dimensions (mm)
base_length = 80   # increased for extra buffer around the phone width
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
window_width = 67          # fixed width now, narrower than before
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

# Pegboard hooks — smooth L-shaped pipe: straight in, rounded bend, straight up
peg_diameter = 7.25
peg_straight_length = 10
peg_up_length = 10
bend_radius = 4
peg_spacing = 25
peg_z = wall_z_bottom + wall_total_height * 0.85

back_y = -outer_depth / 2
peg_positions = [-peg_spacing, 0, peg_spacing]


def make_hook_peg(x, back_y, peg_z, straight_len, up_len, radius, r):
    P0 = (back_y, peg_z)
    P1 = (back_y - (straight_len - r), peg_z)
    O = (back_y - (straight_len - r), peg_z + r)
    P2 = (back_y - straight_len, peg_z + r)
    Mu = O[0] + r * math.cos(math.radians(225))
    Mv = O[1] + r * math.sin(math.radians(225))
    M = (Mu, Mv)
    P3 = (P2[0], P2[1] + (up_len - r))

    path = (
        cq.Workplane("YZ", origin=(x, 0, 0))
        .moveTo(*P0)
        .lineTo(*P1)
        .threePointArc(M, P2)
        .lineTo(*P3)
    )

    profile = (
        cq.Workplane("XZ", origin=(x, back_y, peg_z))
        .circle(radius / 2)
    )

    return profile.sweep(path)


peg_shapes = [
    make_hook_peg(x, back_y, peg_z, peg_straight_length, peg_up_length, peg_diameter, bend_radius)
    for x in peg_positions
]

pegs = peg_shapes[0]
for shape in peg_shapes[1:]:
    pegs = pegs.union(shape)

result = phone_mount.union(pegs)

cq.exporters.export(result, "phonemount.stl")