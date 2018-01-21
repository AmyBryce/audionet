import collections
import frames
import json
import sys

import os.path

import matplotlib
import matplotlib.pylab as pylab

import numpy as np

pylab.switch_backend('agg')

stats_file = sys.argv[1]
video_file = sys.argv[2]

with open(stats_file) as jsondata:
    statistics = json.load(jsondata)

with open(os.path.join("input", "labels.json")) as f:
    labels = json.load(f)

video_labels = {
    "67GZuUxV27w_30.000.mkv.gz"  : "Rooster (Cock)",
    "9PmzQI8ZYpg_30.000.mkv.gz"  : "Sewing Machine",
    "_A30xsFBMXA_40.000.mkv.gz"  : "Fire Truck",
    "BUGx2e7OgFE_30.000.mkv.gz"  : "Harmonica",
    "eHIlPlNWISg_90.000.mkv.gz"  : "Polaroid Camera",
    "eV5JX81GzqA_150.000.mkv.gz" : "Race Car",
    "-OAyRsvFGgc_30.000.mkv.gz"  : "Electric Guitar",
    "rctt0dhCHxs_16.000.mkv.gz"  : "Tree Frog",
    "rTh92nlG9io_30.000.mkv.gz"  : "Keyboard",
    "-XilaFMUwng_50.000.mkv.gz"  : "Magpie"
}

video_labels = collections.OrderedDict(
    sorted(video_labels.items(), key=lambda t: t[1]))

# Grab the indices of the top three most
# probable sounds found across all of our frames.
probabilities = np.array(statistics["frame_probabilities"])
mean_probabilities = np.mean(probabilities, axis=0)
top3_categories = reversed(np.argsort(mean_probabilities)[-3:])

# Plot the probabilities associated with these
# top three indices across all of our frames.
pylab.subplot(2, 1, 1)
pylab.title("Top 3 Most Probable Sounds\nin the '{}' Video"
            .format(video_labels[os.path.basename(video_file)]),
            fontsize=14,
            fontweight='bold')
pylab.xlabel('Frame #')
pylab.ylabel('Probability')

for index in top3_categories:
    pylab.plot([p[index] for p in statistics["frame_probabilities"]],
               label=labels[str(index)][:18] + (labels[str(index)][18:] and '...'))

# Format the legend for the top subplot.
lgd_top = pylab.legend(bbox_to_anchor=(1.05, 1, 0.4, 0), loc=2, borderaxespad=0., mode="expand")

# Grab the audio signal out of the video itself and plot it.
pylab.subplot(2, 1, 2)
pylab.xlabel('Time (s)')
pylab.ylabel('Amplitude')
pylab.xticks(range(11))
frame_data = frames.get(video_file, statistics["sample_period_msec"])
audio_frames = np.ndarray.flatten(np.asarray(frame_data["audio_frames"]))
time = [t * (10.0/(len(audio_frames) - 1)) for t in range(len(audio_frames))]
pylab.plot(time, audio_frames, label="Audio Signal", color='blue')

# Format the legend for the bottom subplot.
lgd_bot = pylab.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

# Tighten the layout for all subplot and their label placement.
pylab.tight_layout()

# Output the plot to a PNG file.
plots_dir = os.path.join("output", "graphs", statistics["model_file"])
plots_path = os.path.join(plots_dir, os.path.basename(stats_file) + "-signal-plot.png")
os.makedirs(plots_dir , exist_ok=True)
fig = open(plots_path, 'wb')
pylab.savefig(fig, format='png', bbox_extra_artists=(lgd_top, lgd_bot), bbox_inches='tight')
fig.close()
print("Plot written to: {}".format(plots_path))
