"""See what JPG compression does to an image: save a color TIFF as JPG, read the
JPG back in, and calculate the difference with the original.  Show all three
in Napari.

Run it from the top folder of the workshop repository with:

    uv run src/jpg_difference.py

The JPG and the difference image are saved in the "results" folder.  Napari
opens in its own window.  Close that window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from bioio import BioImage
from PIL import Image

# Build the paths starting from this script's location, so the script works
# no matter which folder you started it from.
REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Cell_cropped_2.tif"
RESULTS = REPO / "results"
JPG = RESULTS / "Cell_cropped_2_saved.jpg"
DIFFERENCE = RESULTS / "Cell_cropped_2_jpg_difference.tif"

# JPG quality, from 1 (smallest file, worst image) to 95 (largest, best).
# 75 is the usual default.  Try other values!
QUALITY = 75

RESULTS.mkdir(exist_ok=True)

# Step 1: open the original.  "YXS" gives rows (Y), columns (X) and the 3
# color values (S: red, green, blue) of every pixel.
img = BioImage(INPUT)
original = img.get_image_data("YXS")
pixel_size = img.physical_pixel_sizes

# Step 2: save it as JPG.
Image.fromarray(original).save(JPG, quality=QUALITY)

# Step 3: read the JPG back in, as a NumPy array just like the original.
jpg = np.array(Image.open(JPG))

# Step 4: the difference.  The pixels are uint8 (0 - 255), which cannot hold
# negative numbers: 3 - 5 would "wrap around" to 254.  So first convert to
# int16, which can be negative.  Positive: the JPG is brighter than the
# original; negative: darker; 0: no change.
difference = jpg.astype(np.int16) - original.astype(np.int16)

# Save the difference as a TIFF, keeping the pixel size.  "resolution" is the
# number of pixels per micrometer (1 / pixel size).  (A JPG cannot store a
# pixel size in micrometers, which is one more reason not to use it for
# microscopy.)
tifffile.imwrite(
    DIFFERENCE,
    difference,
    imagej=True,
    resolution=(1 / pixel_size.X, 1 / pixel_size.Y),
    metadata={"unit": "micron", "axes": "YXS"},
)

print(f"Original : {INPUT.stat().st_size / 1024:6.0f} KB  ({INPUT.name})")
print(f"JPG      : {JPG.stat().st_size / 1024:6.0f} KB  (quality {QUALITY})")
print(f"Pixel values changed by JPG: {np.mean(difference != 0) * 100:.1f}%")
print(f"Largest change             : {np.abs(difference).max()}")
print(f"Average change             : {np.abs(difference).mean():.2f}")
print(f"Saved {JPG}")
print(f"Saved {DIFFERENCE}")

# Show all three in Napari, side by side (grid mode).  The original and the
# JPG are color images (rgb=True).  The difference is shown as 3 separate
# layers, one per color, with a gray scale that runs from -20 (black) through
# 0 (middle gray) to +20 (white), so changes in both directions are visible.
viewer = napari.Viewer()
scale = (pixel_size.Y, pixel_size.X)
viewer.add_image(original, name="original", rgb=True, scale=scale, units=("um", "um"))
viewer.add_image(jpg, name="JPG", rgb=True, scale=scale, units=("um", "um"))
viewer.add_image(
    difference,
    channel_axis=2,
    name=["difference red", "difference green", "difference blue"],
    colormap="gray",
    contrast_limits=(-20, 20),
    scale=scale,
    units=("um", "um"),
)
viewer.canvas.grid.enabled = True
viewer.canvas.overlays.scale_bar.visible = True

# Start the Napari window and wait until you close it.
napari.run()
