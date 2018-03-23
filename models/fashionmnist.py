from capsule_layer import CapsuleLinear
from torch import nn
from torchvision.models.resnet import resnet34


class FashionMNISTCapsuleNet(nn.Module):
    def __init__(self, num_iterations=3):
        super(FashionMNISTCapsuleNet, self).__init__()

        layers = [nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1, bias=False)]
        for name, module in resnet34().named_children():
            if name == 'conv1' or isinstance(module, nn.MaxPool2d) or isinstance(module, nn.AvgPool2d) or isinstance(
                    module, nn.Linear):
                continue
            layers.append(module)
        self.features = nn.Sequential(*layers)
        self.pool = nn.AvgPool2d(kernel_size=4)
        self.classifier = nn.Sequential(CapsuleLinear(in_capsules=128, out_capsules=32, in_length=4, out_length=8,
                                                      routing_type='dynamic', share_weight=True,
                                                      num_iterations=num_iterations),
                                        CapsuleLinear(in_capsules=32, out_capsules=10, in_length=8, out_length=16,
                                                      routing_type='contract', share_weight=False,
                                                      num_iterations=num_iterations))

    def forward(self, x):
        out = self.features(x)
        out = self.pool(out)

        out = out.view(*out.size()[:2], -1)
        out = out.transpose(-1, -2)
        out = out.contiguous().view(out.size(0), -1, 4)

        out = self.classifier(out)
        classes = out.norm(dim=-1)
        return classes


if __name__ == '__main__':
    model = FashionMNISTCapsuleNet()
    for m in model.named_children():
        print(m)
