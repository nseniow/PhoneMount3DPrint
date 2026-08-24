import cadquery as cq

# Base block dimensions (mm)
base_length = 78   # width, along which the phone will sit
base_depth = 14    # front-to-back depth
base_height = 25   # thickness of the base

base = (
    cq.Workplane("XY")
    .box(base_length, base_depth, base_height)
)

# Slot (oval) dimensions
slot_length = 14    # long axis, along base_length direction
slot_width = 9      # short axis, along base_depth direction
slot_depth = 18     # how deep into the top it's cut

slot_cutter = (
    cq.Workplane("XY")
    .workplane(offset=base_height / 2)   # start at the top face
    .slot2D(slot_length, slot_width, angle=0)
    .extrude(-slot_depth)                # cut downward into the block
)

result = base.cut(slot_cutter)

cq.exporters.export(result, "phonemount.stl")