# CCN
Convolutional Capsule Network

## Requirements
* [Anaconda](https://www.anaconda.com/download/)
* PyTorch
```
conda install pytorch torchvision cuda90 -c pytorch
```
* PyTorchNet
```
pip install git+https://github.com/pytorch/tnt.git@master
```
* tqdm
```
pip install tqdm
```
* OpenCV
```
conda install opencv
```

## Usage
```
python -m visdom.server -logging_level WARNING & python main.py
optional arguments:
--data_type                   dataset type [default value is 'MNIST'](choices:['MNIST', 'FashionMNIST', 'SVHN', 'CIFAR10', 'CIFAR100', 'STL10'])
--use_data_augmentation       use data augmentation or not [default value is 'yes'](choices:['yes', 'no'])
--batch_size                  train batch size [default value is 16]
--num_epochs                  train epochs number [default value is 100]
--target_category             the category of visualization [default value is None]
--target_layer                the layer of visualization [default value is None]
```
Visdom now can be accessed by going to `127.0.0.1:8097/env/$data_type` in your browser, `$data_type` means the dataset type which you are training.

## Benchmarks(STL10)

Default PyTorch Adam optimizer hyperparameters were used with no learning 
rate scheduling. Epochs with batch size of 60 takes ~3 minutes on a NVIDIA GTX TiTAN GPU.

- Loss/Accuracy Graphs
<table>
  <tr>
    <td>
     <img src="results/train_loss.png"/>
    </td>
    <td>
     <img src="results/test_loss.png"/>
    </td>
  </tr>
</table>
<table>
  <tr>
    <td>
     <img src="results/train_acc.png"/>
    </td>
    <td>
     <img src="results/test_acc.png"/>
    </td>
  </tr>
</table>

- Confusion Matrix
<img src="results/confusion_matrix.png"/> 
