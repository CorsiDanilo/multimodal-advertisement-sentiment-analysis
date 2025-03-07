"""The dataloader for UBFC-rPPG dataset.

Details for the UBFC-rPPG Dataset see https://sites.google.com/view/ybenezeth/ubfcrppg.
If you use this dataset, please cite this paper:
S. Bobbia, R. Macwan, Y. Benezeth, A. Mansouri, J. Dubois, "Unsupervised skin tissue segmentation for remote photoplethysmography", Pattern Recognition Letters, 2017.
"""
import glob
import os
import re

import cv2
import numpy as np
from packages.rppg_toolbox.dataset.data_loader.InferenceOnlyBaseLoader import InferenceOnlyBaseLoader


class CustomLoader(InferenceOnlyBaseLoader):
    """The data loader for the UBFC-rPPG dataset."""

    def __init__(self, name, data_path, config_data):
        """Initializes an UBFC-rPPG dataloader.
            Args:
                data_path(str): path of a folder which stores raw video and bvp data.
                e.g. data_path should be "RawData" for below dataset structure:
                -----------------
                     RawData/
                     |   |-- subject1/
                     |       |-- vid.mp4
                     |   |-- subject2/
                     |       |-- vid.mp4
                     |...
                     |   |-- subjectn/
                     |       |-- vid.mp4
                -----------------
                name(string): name of the dataloader.
                config_data(CfgNode): data settings(ref:config.py).
        """
        super().__init__(name, data_path, config_data)

    def get_raw_data(self, data_path):
        """Returns data directories under the path(For UBFC-rPPG dataset)."""
        data_dirs = glob.glob(data_path + os.sep + "video*")
        if not data_dirs:
            raise ValueError(self.dataset_name + " data paths empty!")
        dirs = [{"index": re.search(
            'video(\d+)', data_dir).group(0), "path": data_dir} for data_dir in data_dirs]
        return dirs

    def split_raw_data(self, data_dirs):
        """Returns a subset of data dirs, split with begin and end values."""
        return data_dirs

    def preprocess_dataset_subprocess(self, data_dirs, config_preprocess, i, file_list_dict):
        """ invoked by preprocess_dataset for multi_process."""
        filename = os.path.split(data_dirs[i]['path'])[-1]
        saved_filename = data_dirs[i]['index']

        # Read Frames
        if 'None' in config_preprocess.DATA_AUG:
            # Utilize dataset-specific function to read video
            frames = self.read_video(
                os.path.join(data_dirs[i]['path'],"video.mp4"))
            print(f"finished reading frames, frame length: {len(frames)}")
        elif 'Motion' in config_preprocess.DATA_AUG:
            # Utilize general function to read video in .npy format
            frames = self.read_npy_video(
                glob.glob(os.path.join(data_dirs[i]['path'],'*.npy')))
        else:
            raise ValueError(f'Unsupported DATA_AUG specified for {self.dataset_name} dataset! Received {config_preprocess.DATA_AUG}.')

        frames_clips = self.preprocess(frames=frames, 
                                       config_preprocess=config_preprocess)

        input_name_list = self.save_multi_process(frames_clips=frames_clips, 
                                                  filename=saved_filename)
        file_list_dict[i] = input_name_list

    @staticmethod
    def read_video(video_file):
        """Reads a video file, returns frames(T, H, W, 3) """
        VidObj = cv2.VideoCapture(video_file)
        VidObj.set(cv2.CAP_PROP_POS_MSEC, 0)
        success, frame = VidObj.read()
        frames = None
        i = 0
        max_frames = 1000
        while success:
            i += 1
            frame = cv2.cvtColor(np.array(frame), cv2.COLOR_BGR2RGB)
            if frames is None:
                frames = np.expand_dims(np.empty_like(frame), 0)
                frames = np.repeat(frames, max_frames, axis=0)
            frames[i] = frame
            success, frame = VidObj.read()
            if i == max_frames-1:
                break
        print(f"read video completed!")
        return frames

    @staticmethod
    def read_wave(bvp_file):
        """Reads a bvp signal file."""
        with open(bvp_file, "r") as f:
            str1 = f.read()
            str1 = str1.split("\n")
            bvp = [float(x) for x in str1[0].split()]
        return np.asarray(bvp)
