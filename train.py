import frames
import gc
import json
import random
import sys
import time
import torch

import os.path

import audionet as an
import numpy as np
import torchvision.models.vgg as models
import torchvision.transforms as transforms

from PIL import Image

# Global, tunable parameters
num_epochs = 5000
video_sample_period_msec = 40
batch_size = 512
learning_rate = 1e-4

# Initialize a dictionary which will be used to dump per-epoch
# stats about the training after it is complete.
statistics = {
    "num_epochs": num_epochs,
    "video_sample_period_msec": video_sample_period_msec,
    "batch_size": batch_size,
    "learning_rate": learning_rate,
    "epochs": []
}

# Parse the arguments.
saved_model_path = None
for i, arg in enumerate(sys.argv):
    if arg == "-o":
        saved_model_path = sys.argv[i + 1]
        sys.argv.remove("-o")
        sys.argv.remove(saved_model_path)
        break

if not saved_model_path:
    print("You must supply an output path for"
          " the trained model with -o <path>",
          file=sys.stderr)
    sys.exit(1)

video_files = sys.argv[1:]

# Create a new audionet model.
# If GPUs are available, make sure to use them.
# Make sure it is possible to backpropagate the gradients through audionet.
audionet = an.Model()
if torch.cuda.is_available():
    audionet = torch.nn.DataParallel(audionet.cuda())
for param in audionet.parameters():
    param.requires_grad = True

# Load the pretrained vgg16 model.
# If GPUs are available, make sure to use them.
# Disallow backpropagation of the gradients through the pretrained vgg16 model.
vgg16 = models.vgg16(pretrained=True)
if torch.cuda.is_available():
    vgg16 = torch.nn.DataParallel(vgg16.cuda())
for param in vgg16.parameters():
    param.requires_grad = False

# Define some extra layers to pass the
# output through vgg16 and audionet.
softmax = torch.nn.Softmax()
logsoftmax = torch.nn.LogSoftmax()
kldivloss = torch.nn.KLDivLoss(reduce=False)

# Transforms to apply to each image frame for passing through vgg16.
# http://pytorch.org/docs/master/torchvision/models.html
image_transforms = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225])])

# Use a standard SGD optimizer to update the weigths in audionet.
optimizer = torch.optim.SGD(
    audionet.parameters(),
    lr=learning_rate,
    nesterov=True,
    momentum=0.9)

# Format the video and audio frames for processing.
paired_frames = []
for i, video_file in enumerate(video_files):
    print("Load Video {} of {}:".format(i + 1, len(video_files)))
    print("  Name: {}".format(video_file))

    frame_data = frames.get(
        video_file,
        video_sample_period_msec)

    file_names = [os.path.basename(video_file)] * len(frame_data["video_frames"])

    images = []
    for video_frame in frame_data["video_frames"]:
        img = Image.fromarray(video_frame, mode="RGB")
        img = img.resize((224, 224), resample=Image.NEAREST)
        img = image_transforms(img)
        images.append(img)

    paired_frames.extend(zip(file_names, images, frame_data["audio_frames"]))

# Start processing the video and audio frames.
for i in range(num_epochs):
    print("Epoch {} of {}:".format(i + 1, num_epochs))

    # Shuffle the paired frames so they are processed in a different order
    # than they were originally added in. This adds variance to the types of
    # sound processed each time we walk through the loop below.
    random.shuffle(paired_frames)

    # Add a dictionary to help collect statistics
    # about the training of this epoch.
    statistics["epochs"].append({})

    beg_time = time.time()
    for j in range(0, len(paired_frames), batch_size):
        # Pull the frame batches out of paired_frames.
        file_names = [pair[0] for pair in paired_frames[j:j+batch_size]]
        video_frames = [pair[1] for pair in paired_frames[j:j+batch_size]]
        audio_frames = [pair[2] for pair in paired_frames[j:j+batch_size]]

        # Use the optimizer to zero out all of the gradients in audionet.
        optimizer.zero_grad()

        # Format the video frame and audio frame batches for passing through
        # the vgg16 and audionet neural networks. Make sure and use GPUs if
        # they are available.
        image_tensor = torch.from_numpy(np.stack(video_frames)).float()
        audio_tensor = torch.from_numpy(np.stack(audio_frames)).float()
        if torch.cuda.is_available():
            image_tensor = image_tensor.cuda()
            audio_tensor = audio_tensor.cuda()
        image_input = torch.autograd.Variable(image_tensor)
        audio_input = torch.autograd.Variable(audio_tensor)

        # TODO: Explain why audionet's output needs to be logged()
        # before passing into the kldiv loss function.
        # http://pytorch.org/docs/0.3.0/nn.html#kldivloss
        # https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence

        # Pass the video frame batch through vgg16.
        vgg_output = vgg16(image_input)
        vgg_probs = softmax(vgg_output)

        # Pass audio frame batch through audionet.
        audionet_output = audionet(audio_input)
        audionet_log_probs = logsoftmax(audionet_output)

        # Compute the loss function as the KL
        # divergence between vgg16 and audionet.
        kldiv_output = kldivloss(audionet_log_probs, vgg_probs)
        kldiv_output = kldiv_output.sum(dim=1)

        # Sum the KL divergence across the entire batch.
        kldiv_average = kldiv_output.sum(dim=0)

        # Backpropogate the gradients through audionet.
        kldiv_average.backward()

        # Trigger the optimizer to update the weights
        # on all the layers in audionet.
        optimizer.step()

        # Gather stats about the kl-divergence computed for each video frame.
        for k in range(len(file_names)):
            statistics["epochs"][i].setdefault("videos", {})
            statistics["epochs"][i]["videos"].setdefault(file_names[k], {})
            statistics["epochs"][i]["videos"][file_names[k]].setdefault("kldiv_per_frame", [])
            statistics["epochs"][i]["videos"][file_names[k]]["kldiv_per_frame"].append(float(kldiv_output[k]))

        # Explicitly invoke the garbage collector
        # to cleanup any dangling references.
        gc.collect()

    end_time = time.time()

    training_time = end_time - beg_time
    statistics["epochs"][i]["training_time"] = training_time
    print("  Training Time: {:0.3f} s".format(training_time))

# Dump trained model into a file.
model_dir = os.path.join("output", "models")
model_path = os.path.join(model_dir, saved_model_path)
os.makedirs(model_dir, exist_ok=True)
if torch.cuda.is_available():
    audionet.module.save(model_path)
else:
    audionet.save(model_path)
print("Model written to: {}".format(model_path))

# Dump training statistics into a file.
stats_dir = os.path.join("output", "stats", "training")
stats_path = os.path.join(stats_dir, os.path.basename(saved_model_path) + ".stats.json")
os.makedirs(stats_dir , exist_ok=True)
with open(stats_path, 'w') as jsonfile:
    json.dump(statistics, jsonfile)
print("Model Statistics written to: {}".format(stats_path))
