import gzip
import pathlib
import shutil
import sys
import tempfile

import numpy as np

from moviepy.editor import VideoFileClip

def get(video_file, sample_period_msec = 40, audio_sample_rate = 16000):
    suffixes = pathlib.Path(video_file).suffixes
    if suffixes[-1] == '.gz':
        with tempfile.NamedTemporaryFile(mode="w+b", suffix=suffixes[-2]) as temp_file:
            with gzip.open(video_file) as video_contents:
                shutil.copyfileobj(video_contents, temp_file)
                temp_file.flush()
                clip = VideoFileClip(temp_file.name)
    else:
        clip = VideoFileClip(video_file)

    sample_period_sec = sample_period_msec / 1000.0
    if sample_period_sec > clip.duration:
        sample_period_sec = clip.duration

    subsampled_audio = clip.audio.set_fps(audio_sample_rate)

    samples_per_audio_frame = audio_sample_rate * sample_period_sec

    current_ts = 0
    video_frames = []
    audio_frames = []
    while current_ts + sample_period_sec <= clip.duration:
        video_frame = clip.get_frame(current_ts + sample_period_sec/2)
        video_frames.append(video_frame)

        audio_frame = subsampled_audio.subclip(
            current_ts,
            current_ts + sample_period_sec).iter_frames()
        audio_frame = np.array(list(audio_frame)).mean(1)
        audio_frame = audio_frame[:int(samples_per_audio_frame)]
        audio_frames.append(audio_frame)

        current_ts += sample_period_sec

    return {
        "video_frames" : video_frames,
        "audio_frames" : audio_frames
    }
