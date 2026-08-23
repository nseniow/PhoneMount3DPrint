import cadquery as cq

# Base block dimensions (mm)
base_length = 78   # width, along which the phone will sit
base_depth = 14     # front-to-back depth
base_height = 25    # thickness of the base

base = (
    cq.Workplane("XY")
    .box(base_length, base_depth, base_height)
)

# Export so you can view/print it
cq.exporters.export(base, "phonemount.stl")