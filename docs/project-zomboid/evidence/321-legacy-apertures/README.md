# Legacy glass door aperture investigation

Source `fixtures_doors_01_48/49` accounts for nine unresolved openings in Cantó revision34.
The read-only inspect_opening_profile.py tool records atlas region, page hash, opaque
silhouette bounds and crops. System Python lacked Pillow; used the bundled workspace
Python runtime. No asset pixels, atlas, scene or save were altered.

The generic 3D adapter uses reviewed silhouette-envelope proportions for these two
closed glass-door IDs only, with floor-aligned base. These are inferred dimensions;
frame, handle, centre rail and materials are not faithfully reconstructed. Other tiles
remain unknown; authored explicit profiles take precedence. This is diagnostic migration,
not a new accepted shipping art family.

Initial browser verification failed with 'Wall junction consumes an opening or short wall'.
A narrow side jamb near a corner intersects the existing thick-wall miter partition.
Do not shrink the opening or claim it solved. The adapter now isolates/reports such
conflicts instead of aborting all preview geometry. A regression test reproduces this
case; actual intersecting geometry still requires a general clipping/junction solution.
