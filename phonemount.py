import cadquery as cq

# Base block dimensions (mm)
base_length = 78   # width, along which the phone will sit
base_depth = 14    # front-to-back depth
base_height = 25   # thickness of the base

base = (
    cq.Workplane("XY")
    .box(base_length, base_depth, base_height)
)

# Oval slot dimensions (cut from top)
slot_length = 14    # long axis, along base_length direction
slot_width = 9      # short axis, along base_depth direction
slot_depth = 18      # how deep into the top it's cut

oval_cutter = (
    cq.Workplane("XY")
    .workplane(offset=base_height / 2)   # start at the top face
    .slot2D(slot_length, slot_width, angle=0)
    .extrude(-slot_depth)                # cut downward into the block
)

# Rectangular through-slot dimensions (top to bottom)
rect_length = 9      # along base_length direction
rect_width = 3       # along base_depth direction

rect_cutter = (
    cq.Workplane("XY")
    .workplane(offset=base_height / 2)   # start at the top face
    .rect(rect_length, rect_width)
    .extrude(-base_height)               # cut all the way through
)

# New rectangular slot cut upward from the bottom
bottom_rect_length = 12   # along base_length direction
bottom_rect_width = 7     # along base_depth direction
bottom_rect_depth = 6     # how deep into the bottom it's cut

bottom_rect_cutter = (
    cq.Workplane("XY")
    .workplane(offset=-base_height / 2)  # start at the bottom face
    .rect(bottom_rect_length, bottom_rect_width)
    .extrude(bottom_rect_depth)          # cut upward into the block
)

result = base.cut(oval_cutter).cut(rect_cutter).cut(bottom_rect_cutter)

cq.exporters.export(result, "phonemount.stl")