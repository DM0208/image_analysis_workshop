"""See what happens when a JPG is opened and saved again, over and over: save a
color TIFF as JPG, then re-save that JPG 100 times.  Compare the JPG after 1
save and after 100 saves with the original, and show everything in Napari.

Run it from the top folder of the workshop repository with:

    uv run src/jpg_resave_100.py

The final JPG and the difference images are saved in the "results" folder.
Napari opens in its own window.  Close that window to end the script.
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
JPG = RESULTS / "Cell_cropped_2_resaved.jpg"

QUALITY = 75  # JPG quality, from 1 (worst) to 95 (best)
TIMES = 100  # how many times to re-save

RESULTS.mkdir(exist_ok=True)

# Open the original.  "YXS" gives rows (Y), columns (X) and the 3 color values
# (S: red, green, blue) of every pixel.
img = BioImage(INPUT)
original = img.get_image_data("YXS")
pixel_size = img.physical_pixel_sizes

# Save as JPG once, and read it back.
Image.fromarray(original).save(JPG, quality=QUALITY)
jpg_once = np.array(Image.open(JPG))

# Now open the JPG and save it again, TIMES times in a row.  This is what
# happens when you edit a JPG and save it, again and again.
jpg = jpg_once
for _ in range(TIMES):
    Image.fromarray(jpg).save(JPG, quality=QUALITY)
    jpg = np.array(Image.open(JPG))
jpg_many = jpg


def difference(changed):
    """Changed image minus the original, as numbers that can be negative.

    uint8 cannot be negative (3 - 5 would wrap around to 254), so convert to
    int16 first.  Positive: brighter than the original; negative: darker.
    """
    return changed.astype(np.int16) - original.astype(np.int16)


diff_once = difference(jpg_once)
diff_many = difference(jpg_many)

print(f"{'':28s}{'after 1 save':>14s}{f'after {TIMES + 1} saves':>18s}")
for label, func in [
    ("Pixel values changed (%)", lambda d: np.mean(d != 0) * 100),
    ("Largest change", lambda d: np.abs(d).max()),
    ("Average change", lambda d: np.abs(d).mean()),
]:
    print(f"{label:28s}{func(diff_once):>14.2f}{func(diff_many):>18.2f}")
changed_by_resaving = np.mean(jpg_many != jpg_once) * 100
print(f"\nPixel values that changed between save 1 and save {TIMES + 1}: "
      f"{changed_by_resaving:.1f}%")

# Save both difference images as TIFF, keeping the pixel size.  "resolution"
# is the number of pixels per micrometer (1 / pixel size).
for name, diff in [("1x", diff_once), (f"{TIMES + 1}x", diff_many)]:
    path = RESULTS / f"Cell_cropped_2_jpg_{name}_difference.tif"
    tifffile.imwrite(
        path,
        diff,
        imagej=True,
        resolution=(1 / pixel_size.X, 1 / pixel_size.Y),
        metadata={"unit": "micron", "axes": "YXS"},
    )
    print(f"Saved {path}")
print(f"Saved {JPG}")

# Show everything side by side in Napari (grid mode).  To keep the number of
# panels small, each difference image shows the average change over the red,
# green and blue values of each pixel.  Gray = no change, white = the JPG is
# brighter than the original, black = darker.
viewer = napari.Viewer()
scale = (pixel_size.Y, pixel_size.X)
units = ("um", "um")
viewer.add_image(original, name="original", rgb=True, scale=scale, units=units)
viewer.add_image(jpg_once, name="JPG, 1 save", rgb=True, scale=scale, units=units)
viewer.add_image(
    jpg_many, name=f"JPG, {TIMES + 1} saves", rgb=True, scale=scale, units=units
)
for name, diff in [("1 save", diff_once), (f"{TIMES + 1} saves", diff_many)]:
    viewer.add_image(
        diff.mean(axis=2),
        name=f"difference, {name}",
        colormap="gray",
        contrast_limits=(-20, 20),
        scale=scale,
        units=units,
    )
viewer.canvas.grid.enabled = True
viewer.canvas.overlays.scale_bar.visible = True

# Start the Napari window and wait until you close it.
napari.run()
