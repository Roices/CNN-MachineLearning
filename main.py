import torch
import torch.nn as nn
import torchmetrics
import torchvision
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn.functional as F
import pytorch_lightning as pl
from pytorch_lightning import Trainer

num_classes = 3
VGG16_epochs = 2
ConvNet_epochs = 5
batch_size = 100
learning_rate = 0.001

# Data dir
train_dir = '/Users/tuan/Downloads/DATA_CHAMBER_2021/train'
test_dir = '/Users/tuan/Downloads/DATA_CHAMBER_2021/test'

# Data transforms
training_transforms = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.RandomCrop(32, padding=4),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor()
  ])
testing_transforms = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor()
  ])


class VGG16(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.features = self._make_layers()
        self.classfier_head = nn.Linear(512, 3)
        self.accuracy = torchmetrics.Accuracy()

    def forward(self, x):
        out = self.features(x)
        out = self.classfier_head(out.view(out.size(0), -1))
        return out

    def _make_layers(self):
        config = [64, 64, 'MP', 128, 128, 'MP', 256, 256, 256, 'MP', 512, 512, 512, 'MP', 512, 512, 512, 'MP']
        layers = []
        c_in = 3
        for c in config:
            if c == 'MP':
                layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
            else:
                layers += [
                    nn.Conv2d(in_channels=c_in, out_channels=c, kernel_size=3, padding=1),
                    nn.BatchNorm2d(c),
                    nn.ReLU6(inplace=True)
                ]
                c_in = c
        return nn.Sequential(*layers)

    def training_step(self, batch, batch_idx):
        images, labels = batch

        # Forward pass
        outputs = self(images)
        loss = F.cross_entropy(outputs, labels)

        self.log('train_acc', self.accuracy(outputs, labels))
        self.log("train_loss", loss)
        return loss

    # define what happens for testing here

    def train_dataloader(self):
        train_dataset = torchvision.datasets.ImageFolder(train_dir, transform=training_transforms)
        train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=batch_size, num_workers=4,
                                                   shuffle=True)
        return train_loader

    def test_dataloader(self):
        test_dataset = torchvision.datasets.ImageFolder(test_dir, transform=testing_transforms)
        test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=batch_size, num_workers=4,
                                                  shuffle=False)
        return test_loader

    def test_step(self, batch, batch_idx):
        images, labels = batch

        # Forward pass
        outputs = self(images)
        loss = F.cross_entropy(outputs, labels)

        self.log('test_acc', self.accuracy(outputs, labels))
        self.log("test_loss", loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9, weight_decay=5e-4)


class Resnet18(pl.LightningModule):
    def __init__(self):
        super(Resnet18, self).__init__()
        self.features = models.resnet18(pretrained=True)
        # Freeze all layers
        for param in self.features.parameters():
            param.requires_grad = False
        # change the last layer
        num_ftrs = self.features.fc.in_features
        self.features.fc = torch.nn.Linear(num_ftrs, 3)

        self.accuracy = torchmetrics.Accuracy()

    def forward(self, x):
        out = self.features(x)
        # out = F.log_softmax(out, dim=1)
        return out

    def training_step(self, batch, batch_idx):
        images, labels = batch

        # Forward pass
        outputs = self(images)
        loss = F.cross_entropy(outputs, labels)

        self.log('train_acc', self.accuracy(outputs, labels))
        self.log("train_loss", loss)
        return loss

    def train_dataloader(self):
        train_dataset = torchvision.datasets.ImageFolder(train_dir, transform=training_transforms)

        train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=batch_size, num_workers=4,
                                                   shuffle=True)
        return train_loader

    def test_dataloader(self):
        test_dataset = torchvision.datasets.ImageFolder(test_dir, transform=testing_transforms)

        test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=batch_size, num_workers=4,
                                                  shuffle=False)
        return test_loader

    def test_step(self, batch, batch_idx):
        images, labels = batch

        # Forward pass
        outputs = self(images)
        loss = F.cross_entropy(outputs, labels)

        self.log('test_acc', self.accuracy(outputs, labels))
        self.log("test_loss", loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=learning_rate)

if __name__ == '__main__':
    model = Resnet18()

    trainer = Trainer(auto_lr_find=True, max_epochs=5, fast_dev_run=False, auto_scale_batch_size=True)
    trainer.fit(model)
    trainer.test(model)