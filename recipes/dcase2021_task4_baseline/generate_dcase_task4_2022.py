import argparse
from curses import meta
import glob
import time
import warnings
from pprint import pformat

import pandas as pd
import numpy as np
import os
import soundfile as sf
import random
import shutil

import desed

seed = 2021
random.seed(seed)
np.random.seed(seed)

def create_folder(folder, exist_ok=True, delete_if_exists=False):
    """ Create folder (and parent folders) if not exists.

    Args:
        folder: str, path of folder(s) to create.
        delete_if_exists: bool, True if you want to delete the folder when exists

    Returns:
        None
    """
    if not folder == "":
        if delete_if_exists:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                os.mkdir(folder)

        os.makedirs(folder, exist_ok=exist_ok)


def _create_symlink(src, dest, **kwargs):
    if os.path.exists(dest):
        warnings.warn(f"Symlink already exists : {dest}, skipping.\n")
    else:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        os.symlink(os.path.abspath(src), dest, **kwargs)


def create_synth_dcase2022(synth_path, destination_folder):
    print("Creating symlinks for real data")
    split_sets = ["train", "validation"]
    if os.path.exists(os.path.join(synth_path, "audio", "eval")):
        split_sets.append("eval")

    for split_set in split_sets:
        # AUDIO
        split_audio_folder = os.path.join(synth_path, "audio", split_set)
        audio_subfolders = [
            d
            for d in os.listdir(split_audio_folder)
            if os.path.isdir(os.path.join(split_audio_folder, d))
        ]
        # Manage the validation case which changed from 2020
        if split_set == "validation" and not len(audio_subfolders):
            split_audio_folder = os.path.join(synth_path, "audio")
            audio_subfolders = ["validation"]

        for subfolder in audio_subfolders:
            abs_src_folder = os.path.abspath(
                os.path.join(split_audio_folder, subfolder)
            )
            dest_folder = os.path.join(
                destination_folder, "audio", split_set, subfolder
            )
            _create_symlink(abs_src_folder, dest_folder)

        # META
        split_meta_folder = os.path.join(synth_path, "metadata", split_set, f"synthetic21_{split_set}")
        meta_files = glob.glob(os.path.join(split_meta_folder, "*.tsv"))
        for meta_file in meta_files:
            
            create_folder(destination_folder)
            dest_file = os.path.join(
                destination_folder, "metadata", split_set, f"synthetic21_{split_set}", os.path.basename(meta_file)
            )
            _create_symlink(meta_file, dest_file)


if __name__ == "__main__":
    t = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--basedir",
        type=str,
        default="../../data",
        help="The base data folder in which we'll create the different datasets."
        "Useful when you don't have any dataset, provide this one and the output folder",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default=None,
        help="Output basefolder in which to put the created 2021 dataset (with real and soundscapes)",
    )
    parser.add_argument(
        "--only_real", 
        action="store_true",
        help="True if only the real part of the dataset need to be downloaded"
    )

    parser.add_argument(
        "--only_synth",
        action="store_true",
        help="True if only the synthetic part of the dataset need to be downloaded"
    )

    args = parser.parse_args()
    pformat(vars(args))

    # #########
    # Paths
    # #########
    bdir = args.basedir
    dcase22_dataset_folder = args.out_dir
    only_real = args.only_real
    only_synth = args.only_synth
    missing_files = None

    download_all = (only_real and only_synth) or (not only_real and not only_synth)
    print(f"Download all: {download_all}")

    # Default paths if not defined (using basedir)
    if dcase22_dataset_folder is None:
        dcase22_dataset_folder = os.path.join(bdir, "dcase2022", "dataset")
        
    # #########
    # Download if not exists the different datasets
    # #########

    # download real dataset 
    if only_real or download_all:
        print('Downloading audioset dataset...')
        missing_files = desed.download_audioset_data(dcase22_dataset_folder, n_jobs=3, chunk_size=10)

    # download synthetic dataset
    if only_synth or download_all:
        print(f"Downloading synthetic part of the dataset")
        url_synth = (
            "https://zenodo.org/record/6026841/files/dcase_synth.zip?download=1"
        )
        synth_folder = str(os.path.basename(url_synth)).split('.')[0]
        # desed.download.download_and_unpack_archive(url_synth, dcase22_dataset_folder, archive_format="zip")
        synth_folder = os.path.join(bdir, "dcase2022", "dataset", synth_folder)
        create_synth_dcase2022(synth_folder, dcase22_dataset_folder)

    print(f"Time of the program: {time.time() - t} s")
    if missing_files is not None:
        warnings.warn(
            f"You have missing files.\n\n"
            f"Please try to redownload desed_real again: \n"
            f"import desed\n"
            f"desed.download_audioset_data('{dcase22_dataset_folder}', n_jobs=3, chunk_size=10)\n\n"
            f"Please, send your missing_files_xx.tsv to the task organisers to get your missing files.\n"
        )
        
