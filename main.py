import argparse

import pandas as pd
import torch
import torchnet as tnt
from torch.autograd import Variable
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torchnet.engine import Engine
from torchnet.logger import VisdomPlotLogger, VisdomLogger
from torchvision.utils import make_grid
from tqdm import tqdm

import utils


def processor(sample):
    data, labels, training = sample
    labels = torch.eye(CLASSES).index_select(dim=0, index=labels)

    data = Variable(data)
    labels = Variable(labels)
    if torch.cuda.is_available():
        data = data.cuda()
        labels = labels.cuda()

    model.train(training)

    classes = model(data)
    loss = loss_criterion(classes, labels)
    return loss, classes


def on_sample(state):
    state['sample'].append(state['train'])


def reset_meters():
    meter_accuracy.reset()
    meter_loss.reset()
    confusion_meter.reset()


def on_forward(state):
    meter_accuracy.add(state['output'].data, state['sample'][1])
    confusion_meter.add(state['output'].data, state['sample'][1])
    meter_loss.add(state['loss'].data[0])


def on_start_epoch(state):
    reset_meters()
    state['iterator'] = tqdm(state['iterator'])


def on_end_epoch(state):
    print('[Epoch %d] Training Loss: %.4f Top1 Accuracy: %.2f%% Top5 Accuracy: %.2f%%' % (
        state['epoch'], meter_loss.value()[0], meter_accuracy.value()[0], meter_accuracy.value()[1]))

    train_loss_logger.log(state['epoch'], meter_loss.value()[0])
    train_top1_accuracy_logger.log(state['epoch'], meter_accuracy.value()[0])
    train_top5_accuracy_logger.log(state['epoch'], meter_accuracy.value()[1])
    results['train_loss'].append(meter_loss.value()[0])
    results['train_top1_accuracy'].append(meter_accuracy.value()[0])
    results['train_top5_accuracy'].append(meter_accuracy.value()[1])

    # learning rate scheduler
    scheduler.step(meter_loss.value()[0], epoch=state['epoch'])

    reset_meters()

    engine.test(processor, utils.get_iterator(False, DATA_TYPE, BATCH_SIZE, USE_DATA_AUGMENTATION))

    test_loss_logger.log(state['epoch'], meter_loss.value()[0])
    test_top1_accuracy_logger.log(state['epoch'], meter_accuracy.value()[0])
    test_top5_accuracy_logger.log(state['epoch'], meter_accuracy.value()[1])
    confusion_logger.log(confusion_meter.value())
    results['test_loss'].append(meter_loss.value()[0])
    results['test_top1_accuracy'].append(meter_accuracy.value()[0])
    results['test_top5_accuracy'].append(meter_accuracy.value()[1])

    print('[Epoch %d] Testing Loss: %.4f Top1 Accuracy: %.2f%% Top5 Accuracy: %.2f%%' % (
        state['epoch'], meter_loss.value()[0], meter_accuracy.value()[0], meter_accuracy.value()[1]))

    torch.save(model.state_dict(), 'epochs/epoch_%s_%d.pt' % (DATA_TYPE, state['epoch']))

    # save statistics at every 10 epochs
    if state['epoch'] % 10 == 0:
        out_path = 'statistics/'
        data_frame = pd.DataFrame(
            data={'train_loss': results['train_loss'], 'test_loss': results['test_loss'],
                  'train_top1_accuracy': results['train_top1_accuracy'],
                  'test_top1_accuracy': results['test_top1_accuracy'],
                  'train_top5_accuracy': results['train_top5_accuracy'],
                  'test_top5_accuracy': results['test_top5_accuracy']},
            index=range(1, state['epoch'] + 1))
        data_frame.to_csv(out_path + DATA_TYPE + '_results.csv', index_label='epoch')

    # features visualization
    original_image, _ = next(iter(utils.get_iterator(False, DATA_TYPE, 25, USE_DATA_AUGMENTATION)))
    data = Variable(original_image)
    if torch.cuda.is_available():
        data = data.cuda()
    features = utils.show_features(model, TARGET_LAYER, data)
    original_image_logger.log(make_grid(original_image, nrow=5, normalize=True).numpy())
    features_logger.log(make_grid(features, nrow=5, normalize=True).numpy())


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Train Capsule Classfication')
    parser.add_argument('--data_type', default='MNIST', type=str,
                        choices=['MNIST', 'FashionMNIST', 'SVHN', 'CIFAR10', 'CIFAR100', 'STL10'],
                        help='dataset type')
    parser.add_argument('--use_data_augmentation', default='yes', type=str, choices=['yes', 'no'],
                        help='use data augmentation or not')
    parser.add_argument('--routing_type', default='sum', type=str,
                        choices=['sum', 'dynamic', 'means', 'cosine', 'tonimoto', 'pearson'], help='routing type')
    parser.add_argument('--batch_size', default=64, type=int, help='train batch size')
    parser.add_argument('--num_epochs', default=100, type=int, help='train epochs number')
    parser.add_argument('--target_layer', default=None, type=int, help='the layer of visualization')

    opt = parser.parse_args()

    DATA_TYPE = opt.data_type
    USE_DATA_AUGMENTATION = True if opt.use_data_augmentation == 'yes' else False
    ROUTING_TYPE = opt.routing_type
    BATCH_SIZE = opt.batch_size
    NUM_EPOCHS = opt.num_epochs
    TARGET_LAYER = opt.target_layer

    results = {'train_loss': [], 'test_loss': [], 'train_top1_accuracy': [], 'test_top1_accuracy': [],
               'train_top5_accuracy': [], 'test_top5_accuracy': []}

    class_name = utils.CLASS_NAME[DATA_TYPE]
    CLASSES = 10
    if DATA_TYPE == 'CIFAR100':
        CLASSES = 100

    model = utils.models[DATA_TYPE](ROUTING_TYPE)
    loss_criterion = utils.MarginLoss()
    if torch.cuda.is_available():
        model.cuda()
        loss_criterion.cuda()

    print("# parameters:", sum(param.numel() for param in model.parameters()))

    optimizer = Adam(model.parameters())
    scheduler = ReduceLROnPlateau(optimizer, verbose=True)

    engine = Engine()
    meter_loss = tnt.meter.AverageValueMeter()
    meter_accuracy = tnt.meter.ClassErrorMeter(topk=[1, 5], accuracy=True)
    confusion_meter = tnt.meter.ConfusionMeter(CLASSES, normalized=True)

    train_loss_logger = VisdomPlotLogger('line', env=DATA_TYPE, opts={'title': 'Train Loss'})
    train_top1_accuracy_logger = VisdomPlotLogger('line', env=DATA_TYPE, opts={'title': 'Train Top1 Accuracy'})
    train_top5_accuracy_logger = VisdomPlotLogger('line', env=DATA_TYPE, opts={'title': 'Train Top5 Accuracy'})
    test_loss_logger = VisdomPlotLogger('line', env=DATA_TYPE, opts={'title': 'Test Loss'})
    test_top1_accuracy_logger = VisdomPlotLogger('line', env=DATA_TYPE, opts={'title': 'Test Top1 Accuracy'})
    test_top5_accuracy_logger = VisdomPlotLogger('line', env=DATA_TYPE, opts={'title': 'Test Top5 Accuracy'})
    confusion_logger = VisdomLogger('heatmap', env=DATA_TYPE,
                                    opts={'title': 'Confusion Matrix', 'columnnames': class_name,
                                          'rownames': class_name})
    original_image_logger = VisdomLogger('image', env=DATA_TYPE,
                                         opts={'title': 'Original Image', 'width': 371, 'height': 335})
    features_logger = VisdomLogger('image', env=DATA_TYPE,
                                   opts={'title': 'Features Image', 'width': 371, 'height': 335})

    engine.hooks['on_sample'] = on_sample
    engine.hooks['on_forward'] = on_forward
    engine.hooks['on_start_epoch'] = on_start_epoch
    engine.hooks['on_end_epoch'] = on_end_epoch

    engine.train(processor, utils.get_iterator(True, DATA_TYPE, BATCH_SIZE, USE_DATA_AUGMENTATION), maxepoch=NUM_EPOCHS,
                 optimizer=optimizer)
