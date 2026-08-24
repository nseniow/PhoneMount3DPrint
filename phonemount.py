import cadquery as cq
from cq_warehouse.thread import IsoThread
from cq_warehouse.fastener import HexNut

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

# --- Threaded pegs (replacing the hook design) ---
thread_major_diameter = 6    # M6 - comfortably under the 7.5mm pegboard hole
thread_pitch = 1             # standard M6 coarse pitch
peg_length = 15               # longer, to clear pegboard thickness + a nut + finger room
peg_spacing = 25
peg_z = wall_z_bottom + wall_total_height * 0.85

back_y = -outer_depth / 2
peg_positions = [-peg_spacing, 0, peg_spacing]


def make_threaded_peg(x, back_y, peg_z, length, major_diameter, pitch):
    thread = IsoThread(
        major_diameter=major_diameter,
        pitch=pitch,
        length=length,
        external=True,
        end_finishes=("fade", "fade"),
    )
    core = cq.Workplane("XY").circle(thread.min_radius).extrude(length)
    rod = core.union(thread.cq_object)
    # rod is built along local +Z from 0 to length; rotate so it points -Y (outward)
    rod = rod.rotate((0, 0, 0), (1, 0, 0), 90)
    rod = rod.translate((x, back_y, peg_z))
    return rod


peg_shapes = [
    make_threaded_peg(x, back_y, peg_z, peg_length, thread_major_diameter, thread_pitch)
    for x in peg_positions
]

pegs = peg_shapes[0]
for shape in peg_shapes[1:]:
    pegs = pegs.union(shape)

result = phone_mount.union(pegs)

cq.exporters.export(result, "phonemount.stl")

# --- Matching nuts, exported separately so you can print 3 loose nuts ---
nut = HexNut(size="M6-1", fastener_type="iso4032", simple=False)

nut_spacing = 15   # lay the 3 nuts out side by side, flat on the print bed
nuts = cq.Workplane("XY")
for i, offset in enumerate([-nut_spacing, 0, nut_spacing]):
    nuts = nuts.union(nut.cq_object.translate((offset, 0, 0)))

cq.exporters.export(nuts, "nuts.stl")