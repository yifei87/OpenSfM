import logging
import os

import numpy as np

from opensfm import pydense
from opensfm import dataset
from opensfm import io

logger = logging.getLogger(__name__)


class Command:
    name = 'export_openmvs'
    help = "Export reconstruction to openMVS format"

    def add_arguments(self, parser):
        parser.add_argument('dataset', help='dataset to process')

    def run(self, args):
        data = dataset.DataSet(args.dataset)
        udata = dataset.UndistortedDataSet(data, 'undistorted')
        reconstructions = udata.load_undistorted_reconstruction()
        tracks_manager = udata.load_undistorted_tracks_manager()

        if reconstructions:
            self.export(reconstructions[0], tracks_manager, udata, data)

    def export(self, reconstruction, tracks_manager, udata, data):
        exporter = pydense.OpenMVSExporter()
        for camera in reconstruction.cameras.values():
            if camera.projection_type == 'perspective':
                w, h = camera.width, camera.height
                K = np.array([
                    [camera.focal, 0, (w - 1.0) / 2 / max(w, h)],
                    [0, camera.focal, (h - 1.0) / 2 / max(w, h)],
                    [0, 0, 1],
                ])
                exporter.add_camera(str(camera.id), K)

        for shot in reconstruction.shots.values():
            if shot.camera.projection_type == 'perspective':
                image_path = udata._undistorted_image_file(shot.id)
                exporter.add_shot(
                    str(os.path.abspath(image_path)),
                    str(shot.id),
                    str(shot.camera.id),
                    shot.pose.get_rotation_matrix(),
                    shot.pose.get_origin())

        for point in reconstruction.points.values():
            shots = list(tracks_manager.get_track_observations(point.id))

            coordinates = np.array(point.coordinates, dtype=np.float64)
            exporter.add_point(coordinates, shots)

        io.mkdir_p(udata.data_path + '/openmvs')
        exporter.export(udata.data_path + '/openmvs/scene.mvs')
