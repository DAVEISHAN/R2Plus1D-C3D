import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torchvision.datasets.cifar import CIFAR100, CIFAR10
from torchvision.datasets.mnist import MNIST, FashionMNIST
from torchvision.datasets.stl10 import STL10
from torchvision.datasets.svhn import SVHN

CLASS_NAME = {'MNIST': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
              'FashionMNIST': ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 'Sandal', 'Shirt', 'Sneaker',
                               'Bag', 'Ankle boot'],
              'SVHN': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
              'CIFAR10': ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck'],
              'CIFAR100': ['apple', 'aquarium_fish', 'baby', 'bear', 'beaver', 'bed', 'bee', 'beetle', 'bicycle',
                           'bottle', 'bowl', 'boy', 'bridge', 'bus', 'butterfly', 'camel', 'can', 'castle',
                           'caterpillar', 'cattle', 'chair', 'chimpanzee', 'clock', 'cloud', 'cockroach', 'couch',
                           'crab', 'crocodile', 'cup', 'dinosaur', 'dolphin', 'elephant', 'flatfish', 'forest', 'fox',
                           'girl', 'hamster', 'house', 'kangaroo', 'keyboard', 'lamp', 'lawn_mower', 'leopard', 'lion',
                           'lizard', 'lobster', 'man', 'maple_tree', 'motorcycle', 'mountain', 'mouse', 'mushroom',
                           'oak_tree', 'orange', 'orchid', 'otter', 'palm_tree', 'pear', 'pickup_truck', 'pine_tree',
                           'plain', 'plate', 'poppy', 'porcupine', 'possum', 'rabbit', 'raccoon', 'ray', 'road',
                           'rocket', 'rose', 'sea', 'seal', 'shark', 'shrew', 'skunk', 'skyscraper', 'snail', 'snake',
                           'spider', 'squirrel', 'streetcar', 'sunflower', 'sweet_pepper', 'table', 'tank', 'telephone',
                           'television', 'tiger', 'tractor', 'train', 'trout', 'tulip', 'turtle', 'wardrobe', 'whale',
                           'willow_tree', 'wolf', 'woman', 'worm'],
              'STL10': ['airplane', 'bird', 'car', 'cat', 'deer', 'dog', 'horse', 'monkey', 'ship', 'truck']}

data_set = {'MNIST': MNIST, 'FashionMNIST': FashionMNIST, 'SVHN': SVHN, 'CIFAR10': CIFAR10, 'CIFAR100': CIFAR100,
            'STL10': STL10}


def get_iterator(mode, data_type, batch_size):
    if data_type == 'STL10' or data_type == 'SVHN':
        if mode:
            data = data_set[data_type](root='data/' + data_type, split='train', transform=transforms.ToTensor(),
                                       download=True)
        else:
            data = data_set[data_type](root='data/' + data_type, split='test', transform=transforms.ToTensor(),
                                       download=True)
    else:
        data = data_set[data_type](root='data/' + data_type, train=mode, transform=transforms.ToTensor(), download=True)

    return DataLoader(dataset=data, batch_size=batch_size, shuffle=mode, num_workers=4)


class GradCam:
    def __init__(self, model, target_layer, target_category):
        self.model = model.eval()
        if torch.cuda.is_available():
            self.model = model.cuda()
        self.target_layer = target_layer
        self.target_category = target_category
        self.features = None
        self.gradients = None

    def save_gradient(self, grad):
        self.gradients = grad

    def __call__(self, x):
        # save the target layer' gradients and features, then get the category scores
        if torch.cuda.is_available():
            x = x.cuda()
        for name, module in self.model.features.named_children():
            x = module(x)
            if name == self.target_layer:
                x.register_hook(self.save_gradient)
                self.features = x
        x = x.view(x.size(0), -1)
        output = self.model.classifier(x)

        # if the target category equal None, return the feature map of the highest scoring category,
        # otherwise, return the feature map of the requested category
        if self.target_category is None:
            one_hot, self.target_category = output.max(dim=-1)
        else:
            one_hot = output[0][self.target_category]
        self.model.features.zero_grad()
        self.model.classifier.zero_grad()
        one_hot.backward()

        weights = self.gradients.mean(dim=-1, keepdim=True).mean(dim=-2, keepdim=True)
        cam = F.relu((weights * self.features).sum(dim=1))
        cam = cam - cam.min()
        cam = cam / cam.max()
        cam = transforms.ToPILImage()(cam.data.cpu())
        cam = transforms.Resize(size=(224, 224))(cam)
        return cam