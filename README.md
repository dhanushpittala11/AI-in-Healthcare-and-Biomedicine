# Breast Tumor Segmentation

This is a Project to survey the performance of different CNN architectures on segmenting breast tumors. All the information about the Dataset can be found [here](https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset). The code for the project can be found [here](https://github.com/dhanushpittala11/AI-in-Healthcare-and-Biomedicine/blob/main/breastcancerdetection_nb.ipynb).

## 1. Architectures 

### 1.1 UNet

#### 1.1.1 Architecture
![UNet Architecture](UNET_ARCHITECTURE.png)

#### 1.1.2 Segmentation Results

![](Unet_img1.png)

![](Unet_img2.png)

### 1.2 Attention UNet

#### 1.2.1 Architecture

![](Attention_UNET.png)
          Block Diagram of the Attention UNet Architecture

![](Attention_Gate.png)
         Schematic of the Attention Gate

#### 1.2.2 Segmentation Results

![](Att_Unet_img1.png)

![](Att_Unet_img2.png)

### 1.3 ResUNet

#### 1.3.1 Architecture

![](Convolutional_block_RESUNET.png)

Schematic of the Residual Block.

![](ResUNET_original_architecture.png)

Residual UNET

#### 1.3.2 Segmentation Results

![](ResUnet_img1.png)

![](ResUnet_img2.png)

## 2 Loss Function

Dice loss and Cross entropy loss have been used for the loss. **Loss = DiceLoss+ Binary CrossEntropy Loss**

* **Dice Loss**
 ![](Dice_Loss.png)
 
*  **BCE Loss**
  
 ![](BCE_loss2.png)

**For training the model, I implemented K-fold cross validation.**

**Exploring several other architectures for improving the segmentation of breast tumors. Will update soon the improved segmantations...**

