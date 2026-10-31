"""Cut a region of interest (ROI) out of the DAPI channel and save it as a
small TIFF, keeping the pixel size.  Then open the saved file again and check
that it is correct.

Run it from the top folder of the workshop repository with:

    uv run src/crop_dapi_roi.py

In the Napari window that opens:
  1. Draw a rectangle around the region you want (the rectangle tool is
     already selected: click and drag on the image).
  2. Click the "Crop and save" button on the right.
The cropped image appears on top of the original, and the terminal shows the
checks.  You can draw a new rectangle and click again; each click overwrites
the saved file.  Close the window to end the script.

The result is saved as testImages/DAPI_ROI.tif.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from bioio import BioImage
from magicgui import magicgui

# Build the paths starting from this script's location, so the script works
# no matter which folder you started it from.
REPO = Path(__file__).resolve().parent.parent
INPUT = (
    REPO
    / "testImages"
    / "3Channel_FF_Corrected_1"
    / "3Channel_FF_Corrected_1_MMStack_Pos0.ome.tif"
)
OUTPUT = REPO / "testImages" / "DAPI_ROI.tif"
CHANNEL = "DAPI"

# Open the image and take only the DAPI channel, as rows (Y) by columns (X).
img = BioImage(INPUT)
channel_names = [str(name) for name in img.channel_names]
dapi = img.get_image_data("YX", C=channel_names.index(CHANNEL))
pixel_size = img.physical_pixel_sizes

print(f"Loaded channel {CHANNEL} of {INPUT.name}")
print(f"  {dapi.shape[0]} x {dapi.shape[1]} pixels, {dapi.dtype}, "
      f"pixel size {pixel_size.X} um")


def crop_and_save(rectangle):
    """Cut the rectangle out of the DAPI image, save it, and check the file."""
    # A rectangle is stored as its 4 corners, each a (row, column) pair.  The
    # smallest and largest row and column give its edges.  Round to whole
    # pixels, and stay inside the image in case the rectangle sticks out.
    top = max(int(np.floor(rectangle[:, 0].min())), 0)
    bottom = min(int(np.ceil(rectangle[:, 0].max())), dapi.shape[0])
    left = max(int(np.floor(rectangle[:, 1].min())), 0)
    right = min(int(np.ceil(rectangle[:, 1].max())), dapi.shape[1])

    # "start:stop" picks rows (or columns) start up to, but not including, stop.
    roi = dapi[top:bottom, left:right]

    # Save as a TIFF that ImageJ/Fiji and Napari understand.  "resolution" is
    # the number of pixels per micrometer (1 / pixel size): this is how the
    # pixel size travels along with the image.
    tifffile.imwrite(
        OUTPUT,
        roi,
        imagej=True,
        resolution=(1 / pixel_size.X, 1 / pixel_size.Y),
        metadata={"unit": "micron"},
    )
    print(f"\nCut rows {top} - {bottom - 1}, columns {left} - {right - 1}")
    print(f"Saved {OUTPUT}")

    # Check: open the saved file again, as if it were a new image, and compare
    # it with what we meant to save.
    saved = BioImage(OUTPUT)
    saved_pixels = saved.get_image_data("YX")
    saved_size = saved.physical_pixel_sizes
    checks = {
        "size": (saved_pixels.shape, roi.shape),
        "number type": (saved_pixels.dtype, dapi.dtype),
        "pixel size (um)": (round(saved_size.X, 4), round(pixel_size.X, 4)),
        "pixel values identical to the original": (
            np.array_equal(saved_pixels, dapi[top:bottom, left:right]),
            True,
        ),
    }
    print("Checking the saved file:")
    for name, (found, expected) in checks.items():
        verdict = "OK" if found == expected else "PROBLEM"
        print(f"  {verdict:7s} {name}: {found} (expected {expected})")

    return saved_pixels, top, left


# Show the DAPI channel in Napari, with the real pixel size.
viewer = napari.Viewer()
viewer.add_image(
    dapi,
    name=CHANNEL,
    colormap="blue",
    scale=(pixel_size.Y, pixel_size.X),
    units=("um", "um"),
)
viewer.canvas.overlays.scale_bar.visible = True

# An empty layer to draw the rectangle in, with the rectangle tool selected.
# It gets the same scale as the image, so its corners are in pixel units.
rectangles = viewer.add_shapes(
    name="ROI",
    edge_color="yellow",
    face_color="transparent",
    edge_width=3,
    scale=(pixel_size.Y, pixel_size.X),
    units=("um", "um"),
)
rectangles.mode = "add_rectangle"


# A button on the side of the Napari window.  Clicking it runs this function.
@magicgui(call_button="Crop and save")
def crop_button():
    if len(rectangles.data) == 0:
        print("\nDraw a rectangle on the image first.")
        return
    saved_pixels, top, left = crop_and_save(rectangles.data[-1])

    # Show the saved file on top of the original.  "translate" shifts it to
    # where it was cut from, so you can see that it lines up.
    if "DAPI_ROI" in viewer.layers:
        viewer.layers.remove("DAPI_ROI")
    viewer.add_image(
        saved_pixels,
        name="DAPI_ROI",
        colormap="gray",
        scale=(pixel_size.Y, pixel_size.X),
        translate=(top * pixel_size.Y, left * pixel_size.X),
        units=("um", "um"),
    )


viewer.window.add_dock_widget(crop_button, area="right")

# Start the Napari window and wait until you close it.
napari.run()
