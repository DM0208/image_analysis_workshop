"""Look inside an image: print its numbers, its size and number type, then show it.

Run it from the top folder of the workshop repository with:

    uv run src/inspect_nucleus.py

Napari opens in its own window.  Close that window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile

# Build the path to the image starting from this script's location, so the
# script works no matter which folder you started it from.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "nucleus_cropped_1.tif"

# Open the TIFF file.  "pixels" becomes a NumPy array: a grid of numbers with
# one number per pixel.
with tifffile.TiffFile(IMAGE) as tif:
    pixels = tif.asarray()

    # The pixel size is stored in the file as a "resolution": how many pixels
    # fit in one unit (here micrometers).  The size of one pixel is the inverse.
    # The resolution is stored as a fraction (numerator, denominator).
    numerator, denominator = tif.pages[0].tags["XResolution"].value
    pixel_size = denominator / numerator
    unit = (tif.imagej_metadata or {}).get("unit", "pixel")

# Make NumPy print each row of the matrix on a single line.
np.set_printoptions(linewidth=200)

print(f"Image: {IMAGE.name}")
print()
print("First 10 rows and 10 columns (each number is one pixel's brightness):")
# pixels[0:10, 0:10] means "rows 0 up to (not including) 10, columns 0 to 10".
print(pixels[0:10, 0:10])
print()
rows, columns = pixels.shape
print(f"Number of rows    : {rows}")
print(f"Number of columns : {columns}")
print(f"Number type       : {pixels.dtype}")
print(f"  smallest possible value: {np.iinfo(pixels.dtype).min}")
print(f"  largest possible value : {np.iinfo(pixels.dtype).max}")
print(f"Pixel size        : {pixel_size:.4f} {unit}")

# Show the image in Napari.  "scale" tells Napari how big each pixel really is,
# so the scale bar shows real distances instead of pixel counts.
viewer = napari.Viewer()
viewer.add_image(
    pixels,
    name=IMAGE.stem,
    scale=(pixel_size, pixel_size),
    units=("um", "um"),
)
viewer.scale_bar.visible = True

# Start the Napari window and wait until you close it.
napari.run()
