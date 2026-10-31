"""Show the red, green and blue values of 3% of the pixels of a color image,
then display the image in Napari with the sampled pixels marked.

Run it from the top folder of the workshop repository with:

    uv run src/cell_rgb_sample.py

The full table, and a screenshot of the Napari window, are saved in the
"results" folder.  Napari opens in its own window.  Close that window to end
the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile

# Build the paths starting from this script's location, so the script works
# no matter which folder you started it from.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "Cell_cropped_2.tif"
RESULTS_DIR = REPO / "results"

# Which fraction of the pixels to sample: 3% = 0.03.
FRACTION = 0.03

# The full table has thousands of lines, too many to read in the terminal.
# Show only this many lines from the start of the table (the whole table is
# saved to a file).  Set it to None to print every line.
LINES_TO_SHOW = 20

# Open the TIFF file.  For a color image "pixels" has three dimensions:
# (rows, columns, 3).  The last dimension holds the red, green and blue value
# of each pixel.
with tifffile.TiffFile(IMAGE) as tif:
    pixels = tif.asarray()

    # The pixel size is stored as a "resolution": how many pixels fit in one
    # micrometer.  The size of one pixel is the inverse.
    numerator, denominator = tif.pages[0].tags["XResolution"].value
    pixel_size = denominator / numerator

rows, columns, colors = pixels.shape
total = rows * columns

# Spread the sample evenly over the image, like the points of a grid.
# If we take a fraction f of the rows and a fraction f of the columns, we get
# f x f of all pixels.  To end up with 3% of the pixels, f must be the
# square root of 0.03 (about 0.17, so roughly every 6th row and column).
f = np.sqrt(FRACTION)
n_rows = round(rows * f)
n_columns = round(columns * f)

# np.linspace gives evenly spaced numbers from the first to the last row; we
# round them to whole numbers because row numbers must be integers.
sample_rows = np.linspace(0, rows - 1, n_rows).round().astype(int)
sample_columns = np.linspace(0, columns - 1, n_columns).round().astype(int)

# Make every combination of a sampled row and a sampled column: the grid points.
grid_rows, grid_columns = np.meshgrid(sample_rows, sample_columns, indexing="ij")
grid_rows = grid_rows.ravel()
grid_columns = grid_columns.ravel()

# Look up the red, green and blue value at each grid point.
red = pixels[grid_rows, grid_columns, 0]
green = pixels[grid_rows, grid_columns, 1]
blue = pixels[grid_rows, grid_columns, 2]

n_samples = len(grid_rows)
print(f"Image: {IMAGE.name}")
print(f"Size       : {rows} rows x {columns} columns = {total} pixels")
print(f"Number type: {pixels.dtype}  (values 0 - 255 for each color)")
print(f"Sampled    : {n_samples} pixels = {100 * n_samples / total:.2f}% of the image")
print(f"             ({n_rows} rows x {n_columns} columns, evenly spaced)")
print()

# Print the table: one line per sampled pixel.
# ":>6" means "right-aligned in a space 6 characters wide", which lines up the
# columns of the table.
header = f"{'row':>6} {'column':>6} {'R':>6} {'G':>6} {'B':>6}"
print(header)
print("-" * len(header))
lines_to_show = n_samples if LINES_TO_SHOW is None else min(LINES_TO_SHOW, n_samples)
for i in range(lines_to_show):
    print(
        f"{grid_rows[i]:>6} {grid_columns[i]:>6} "
        f"{red[i]:>6} {green[i]:>6} {blue[i]:>6}"
    )
if lines_to_show < n_samples:
    print(f"... ({n_samples - lines_to_show} more lines in the saved table)")

# Save the full table as a CSV file ("comma-separated values"), which opens in
# Excel or any spreadsheet program.
RESULTS_DIR.mkdir(exist_ok=True)
table_file = RESULTS_DIR / f"{IMAGE.stem}_rgb_sample.csv"
table = np.column_stack([grid_rows, grid_columns, red, green, blue])
np.savetxt(table_file, table, fmt="%d", delimiter=",", header="row,column,R,G,B", comments="")
print()
print(f"Saved: {table_file}")

# Show the image in Napari.  "rgb=True" tells Napari that the last dimension
# holds the red, green and blue values, so it shows one color image.  "scale"
# makes the scale bar show micrometers.
viewer = napari.Viewer()
viewer.add_image(
    pixels,
    name=IMAGE.stem,
    rgb=True,
    scale=(pixel_size, pixel_size),
    units=("um", "um"),
)

# Mark the sampled pixels with small yellow dots, so you can see where the
# values in the table come from.  Hide them with the eye icon in the layer list.
viewer.add_points(
    np.column_stack([grid_rows, grid_columns]),
    name="sampled pixels",
    size=1.5,
    face_color="yellow",
    border_width=0,
    scale=(pixel_size, pixel_size),
    units=("um", "um"),
)
viewer.scale_bar.visible = True
viewer.reset_view()

# Save a screenshot of the Napari window.
screenshot_file = RESULTS_DIR / f"{IMAGE.stem}_rgb_sample_napari.png"
viewer.screenshot(screenshot_file, canvas_only=False, flash=False)
print(f"Saved: {screenshot_file}")

# Start the Napari window and wait until you close it.
napari.run()
