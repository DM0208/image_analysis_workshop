"""Print every third pixel of one or more images, show their number type, then
display them side by side in Napari.

The printed numbers and a screenshot of the Napari window are also saved in
the "results" folder of the workshop repository.

Run it from the top folder of the workshop repository with:

    uv run src/inspect_nucleus_skip.py nucleus_cropped_1.tif nucleus_cropped_2.tif nucleus_cropped_3.tif

The file names after the script tell it which images in "testImages" to open.
Give one name or several.  Leave them out to open nucleus_cropped_1.tif.

Napari opens in its own window.  Close that window to end the script.
"""

import sys
from pathlib import Path

import napari
import numpy as np
import tifffile

# Build the path to the images starting from this script's location, so the
# script works no matter which folder you started it from.
REPO = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO / "testImages"
RESULTS_DIR = REPO / "results"

# "sys.argv" is the list of words typed on the command line.  sys.argv[1:]
# means "everything after the script name": the file names.  If none were
# given, use image 1.
file_names = sys.argv[1:]
if not file_names:
    file_names = ["nucleus_cropped_1.tif"]

# Keep one row, skip two, keep the next, and so on: a step of 3.
# The same goes for the columns.
STEP = 3
COUNT = 10

# pixels[start:stop:step] - "0:30:3" means rows 0, 3, 6, ... 27.
# Ten rows with a step of 3 reach up to row 27, so we stop at 10 * 3 = 30.
stop = COUNT * STEP

# Make NumPy print each row of the matrix on a single line, and show decimal
# numbers (if the image has them) with 2 digits after the decimal point.
np.set_printoptions(linewidth=200, precision=2, suppress=True)

# Everything we print is also collected in this list, so it can be saved to a
# text file at the end.
report = []


def show(text=""):
    """Print a line in the terminal and remember it for the report file."""
    print(text)
    report.append(str(text))


# One Napari window for all images.
viewer = napari.Viewer()

# Where to place the next image, in micrometers from the left edge.  Each image
# is shifted to the right of the previous one so they appear side by side.
x_position = 0.0

# Repeat the same steps for every file name.
for file_name in file_names:
    image = IMAGE_DIR / file_name

    # Open the TIFF file.  "pixels" becomes a NumPy array: a grid of numbers
    # with one number per pixel.
    with tifffile.TiffFile(image) as tif:
        pixels = tif.asarray()

        # The pixel size is stored in the file as a "resolution": how many
        # pixels fit in one unit (here micrometers).  The size of one pixel is
        # the inverse.
        numerator, denominator = tif.pages[0].tags["XResolution"].value
        pixel_size = denominator / numerator

    subset = pixels[0:stop:STEP, 0:stop:STEP]

    show(f"Image: {image.name}")
    show()
    show(f"10 rows and 10 columns, keeping 1 and skipping {STEP - 1} each time")
    show(f"(rows and columns {list(range(0, stop, STEP))}):")
    show(subset)
    show()
    show(f"Number type     : {pixels.dtype}")
    show(f"Lowest value    : {pixels.min()}")
    show(f"Highest value   : {pixels.max()}")
    # How many different brightness levels actually occur in the image.
    show(f"Different values: {len(np.unique(pixels))}")
    show("-" * 60)

    # Add the image to Napari as its own layer.  "scale" tells Napari how big
    # each pixel really is, so the scale bar shows real distances.
    # "translate" moves the image (down, right) by the given distances, which
    # puts it next to the previous image instead of on top of it.
    viewer.add_image(
        pixels,
        name=image.stem,
        scale=(pixel_size, pixel_size),
        translate=(0, x_position),
        units=("um", "um"),
    )

    # The next image starts after this one's width, plus a 5-pixel gap.
    width = pixels.shape[1]
    x_position += (width + 5) * pixel_size

viewer.scale_bar.visible = True
# Zoom so that all images fit in the window.
viewer.reset_view()

# Save the results.  The file names are built from the image names, e.g.
# "nucleus_cropped_1_nucleus_cropped_2_values.txt", so results from different
# runs do not overwrite each other.
RESULTS_DIR.mkdir(exist_ok=True)
base_name = "_".join(Path(name).stem for name in file_names)

text_file = RESULTS_DIR / f"{base_name}_values.txt"
text_file.write_text("\n".join(report) + "\n")

screenshot_file = RESULTS_DIR / f"{base_name}_napari.png"
viewer.screenshot(screenshot_file, canvas_only=False, flash=False)

print(f"Saved: {text_file}")
print(f"Saved: {screenshot_file}")

# Start the Napari window and wait until you close it.
napari.run()
