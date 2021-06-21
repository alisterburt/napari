from skimage import data
import napari


blobs = data.binary_blobs(length=64, volume_fraction=0.1, n_dim=3).astype(
    float
)
viewer = napari.Viewer(ndisplay=3)
# add the volume
layer = viewer.add_image(blobs)

layer.mode = 'plane'
layer.rendering = 'average'
layer.plane_position = [32, 32, 32]
layer.plane_thickness = 10
layer.plane_angles = [45, 45]
