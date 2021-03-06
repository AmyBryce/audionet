import torch

class Model(torch.nn.Module):
    def __init__(self):
        super(Model, self).__init__()

        self.conv = torch.nn.Conv1d(
            in_channels=1,     # This is fixed to 1 for raw audio input.
            out_channels=16,
            kernel_size=64,
            stride=2,
            padding=32)

        self.maxpool = torch.nn.MaxPool1d(
            kernel_size=8,
            stride=1,
            padding=4)

        self.dense = torch.nn.Linear(
            in_features=16,    # This must match 'out_channels' from self.conv.
            out_features=1000) # This is fixed by imagenet.

    def forward(self, x):
        x = x.unsqueeze(1) # Add a channel dimension.
        x = self.conv(x)
        x = self.maxpool(x)
        x = torch.nn.functional.avg_pool1d(x, kernel_size=x.size()[2])
        x = x.squeeze(2) # Remove the averaged value's dimension.
        x = self.dense(x)
        return x

    def save(self, path):
        torch.save(self.state_dict(), path)


def loadModel(path):
    load = torch.load(path, map_location=(lambda storage, location: storage))
    model = Model()
    model.load_state_dict(load)
    return model
