import collections
import json
import sys

import os.path

import matplotlib
import matplotlib.pylab as pylab

import numpy as np

pylab.switch_backend('agg')

stats_file = sys.argv[1]
beg_range = int(sys.argv[2])
end_range = int(sys.argv[3])

with open(stats_file) as jsondata:
    statistics = json.load(jsondata)

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

colors = {
    "67GZuUxV27w_30.000.mkv.gz"  : "C0",
    "9PmzQI8ZYpg_30.000.mkv.gz"  : "C1",
    "_A30xsFBMXA_40.000.mkv.gz"  : "C2",
    "BUGx2e7OgFE_30.000.mkv.gz"  : "C3",
    "eHIlPlNWISg_90.000.mkv.gz"  : "C4",
    "eV5JX81GzqA_150.000.mkv.gz" : "C5",
    "-OAyRsvFGgc_30.000.mkv.gz"  : "C6",
    "rctt0dhCHxs_16.000.mkv.gz"  : "C7",
    "rTh92nlG9io_30.000.mkv.gz"  : "C8",
    "-XilaFMUwng_50.000.mkv.gz"  : "C9"
}

# Grab the kldiv statistics from the statistics file.
kldivs = {}
for epoch in statistics["epochs"]:
    for video in epoch["videos"]:
      kldivs.setdefault(video, [])
      kldiv_per_frame = epoch["videos"][video]["kldiv_per_frame"]
      kldivs[video].append(np.mean(kldiv_per_frame))

# Plot them on a per-video basis following the order in 'video_labels'.
pylab.title('Average KL-Divergence Per\nTraining Epoch in each Video',
            fontsize=14,
            fontweight='bold')
pylab.xlabel('Epoch #')
pylab.ylabel('Average KL-Divergence')

for video in video_labels.keys():
    if video in epoch["videos"]:
        pylab.plot(kldivs[video][beg_range:end_range],
                   label=video_labels[video],
                   color=colors[video])

# Format the legend
lgd = pylab.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

# Output the plot to a PNG file.
plots_dir = os.path.join("output", "graphs")
plots_path = os.path.join(plots_dir, os.path.basename(stats_file) + "-kldivs-{}-{}-plot.png".format(beg_range, end_range))
fig = open(plots_path, 'wb')
os.makedirs(plots_dir , exist_ok=True)
pylab.savefig(fig, format='png', bbox_extra_artists=(lgd,), bbox_inches='tight')
fig.close()
print("Plot written to: {}".format(plots_path))
