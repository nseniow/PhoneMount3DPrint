import math
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

# Wall around the phone — ONLY the side walls (X-extreme faces) taper outward;
# front/back stay flat since depth (Y) is identical at the top and bottom profile.
#
# The wall is now FLUSH (vertical, untapered) for the entire height of the
# base block, so its inner surface sits exactly on the base's side edges
# the whole way up. It only starts flaring outward once it rises above the
# top of the base (i.e. above where the phone actually sits).
wall_expand = 3
wall_thickness = 3
wall_height_above_top = 30
wall_side_taper_angle = 10   # degrees; tune this down if it's too aggressive

outer_length = base_length + 2 * wall_expand
outer_depth = base_depth + 2 * wall_expand
inner_length = outer_length - 2 * wall_thickness
inner_depth = outer_depth - 2 * wall_thickness

wall_total_height = base_height + wall_height_above_top
wall_z_bottom = -base_height / 2

# Height over which the side walls stay flush/vertical (matches the base
# exactly) before the taper begins.
wall_flush_height = base_height
# Height over which the side walls taper outward, above the base.
wall_taper_height = wall_height_above_top


def loft_side_flush_then_tapered(length_bottom, depth, flush_height, taper_height, z_bottom, taper_deg):
    """Rectangular profile that stays constant width for `flush_height`
    (so it sits flush against the base's straight sides), then tapers
    outward over `taper_height` above that."""
    half_delta = taper_height * math.tan(math.radians(taper_deg))
    length_top = length_bottom + 2 * half_delta
    return (
        cq.Workplane("XY")
        .workplane(offset=z_bottom)
        .rect(length_bottom, depth)
        .workplane(offset=flush_height)
        .rect(length_bottom, depth)
        .workplane(offset=taper_height)
        .rect(length_top, depth)
        .loft(ruled=True)
    )


def width_at_z(length_bottom, flush_height, taper_height, z_bottom, taper_deg, z):
    """Width of the tapered/flush profile at a given absolute z height."""
    flush_top_z = z_bottom + flush_height
    if z <= flush_top_z:
        return length_bottom
    half_delta_total = taper_height * math.tan(math.radians(taper_deg))
    frac = (z - flush_top_z) / taper_height
    return length_bottom + 2 * half_delta_total * frac


wall_outer_solid = loft_side_flush_then_tapered(
    outer_length, outer_depth, wall_flush_height, wall_taper_height, wall_z_bottom, wall_side_taper_angle
)
wall_inner_solid = loft_side_flush_then_tapered(
    inner_length, inner_depth, wall_flush_height, wall_taper_height, wall_z_bottom, wall_side_taper_angle
)

wall = wall_outer_solid.cut(wall_inner_solid)

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

# --- Thicken the back wall to fit bolt heads (moved BEFORE the bottom
# cutouts, so those cutouts also cut through this added material) ---
back_extra_thickness = 3
total_back_thickness = wall_thickness + back_extra_thickness

back_wall_extension = (
    loft_side_flush_then_tapered(
        outer_length, back_extra_thickness, wall_flush_height, wall_taper_height, wall_z_bottom, wall_side_taper_angle
    )
    .translate((0, -(outer_depth / 2 + back_extra_thickness / 2), 0))
)

phone_mount = phone_mount.union(back_wall_extension)

# --- Two rectangular cutouts in the bottom band — now cut AFTER the back
# wall extension exists, so they punch through everything including it ---
center_keep_width = 25   # solid strip kept in the middle for the charger

cutout_top_z = wall_z_bottom + 20
cutout_bottom_z = wall_z_bottom
cutout_height = cutout_top_z - cutout_bottom_z
cutout_center_z = cutout_bottom_z + cutout_height / 2

width_at_cutout_top = width_at_z(
    outer_length, wall_flush_height, wall_taper_height, wall_z_bottom, wall_side_taper_angle, cutout_top_z
)
cutout_width = (width_at_cutout_top - center_keep_width) / 2

left_cutout_x = -(center_keep_width / 2 + cutout_width / 2)
right_cutout_x = (center_keep_width / 2 + cutout_width / 2)

cut_depth = outer_depth + total_back_thickness + 40   # generous — clears the wall, base, and back extension

for x_center in (left_cutout_x, right_cutout_x):
    cutter = (
        cq.Workplane("XZ")
        .workplane(offset=front_y)
        .center(x_center, cutout_center_z)
        .rect(cutout_width, cutout_height)
        .extrude(cut_depth, both=True)
    )
    phone_mount = phone_mount.cut(cutter)

# --- Bolt holes ---
bolt_hole_diameter = 6
bolt_head_diameter = 11.5
bolt_head_depth = 3.5

bolt_spacing = 25
bolt_z = wall_z_bottom + wall_total_height * 0.85

inner_back_y = -inner_depth / 2
bolt_positions = [-bolt_spacing, bolt_spacing]

bolt_cutters = []
for x in bolt_positions:
    through_hole = cq.Solid.makeCylinder(
        bolt_hole_diameter / 2,
        total_back_thickness,
        cq.Vector(x, inner_back_y, bolt_z),
        cq.Vector(0, -1, 0)
    )
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