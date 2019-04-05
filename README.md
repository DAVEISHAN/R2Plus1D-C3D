# CCN
A PyTorch implementation of Convolutional Capsule Network based on the paper [Convolutional Capsule Network for Activity Recoginition]().

## Requirements
- [Anaconda](https://www.anaconda.com/download/)
- [PyTorch](https://pytorch.org)
```
conda install pytorch torchvision -c pytorch
```
- opencv
```
conda install opencv
```
- rarfile
```
pip install rarfile
```
- PyTorchNet
```
pip install git+https://github.com/pytorch/tnt.git@master
```
- capsule-layer
```
pip install git+https://github.com/leftthomas/CapsuleLayer.git@master
```

## Datasets
The datasets are coming from [UCF101](http://crcv.ucf.edu/data/UCF101.php)
、[HMDB51](http://serre-lab.clps.brown.edu/resource/hmdb-a-large-human-motion-database/) 
and [20BN-something-something](https://20bn.com/datasets/something-something).
Download these datasets and `train/val/test` split files into `data` directory.
For `UCF101` and `HMDB51` datasets, we use the `split1` to split files.
For `20BN-something-something` dataset, after downloading all parts, run 
`cat 20bn-something-something-v2-?? | tar zx` to extract data. Finally Run `misc.py` to preprocess these datasets.

## Usage
### Train Model
```
visdom -logging_level WARNING & python train.py --num_epochs 200
optional arguments:
--data_type                   dataset type [default value is 'ucf101'](choices=['ucf101', 'hmdb51', 'ss174'])
--clip_len                    number of frames in each video [default value is 16]
--batch_size                  training batch size [default value is 20]
--num_epochs                  training epochs number [default value is 100]
```
Visdom now can be accessed by going to `127.0.0.1:8097` in your browser.

### Inference Video
```
python inference.py --video_name data/ucf101/ApplyLipstick/v_ApplyLipstick_g04_c02.avi
optional arguments:
--data_type                   dataset type [default value is 'ucf101'](choices=['ucf101', 'hmdb51', 'ss174'])
--clip_len                    number of frames in each video [default value is 16]
--video_name                  test video name
--model_name                  model epoch name [default value is 'ucf101_100.pth']
```
The inferences will show in a pop up window.

## Results
The train/val/test loss、accuracy and confusion matrix are showed on visdom. 
Pay attention, `something-something` dataset has not provide the real labels of test split, so the test accuracy is no
meaning here. We used a fake label for test data, just to make code uniformity.
### UCF101
![result](results/ucf101.png)
### HMDB51
![result](results/hmdb51.png)
### Something-something
![result](results/ss174.png)

