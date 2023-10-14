# -*- coding: utf-8 -*-
"""Copy_of_breastcancerdetection3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1snp_591G6hbcP1P74t3oM0BmqU13h9BD
"""

from google.colab import drive
drive.mount('/content/gdrive')

!unzip gdrive/MyDrive/Breast_US.zip

"""**Import Libraries**"""

import os
import sys
import random
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2

from keras.preprocessing.image import ImageDataGenerator
from keras import layers
from keras.layers import Input, BatchNormalization, Activation, Dense, Dropout,UpSampling2D,Add
from sklearn.model_selection import train_test_split
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import SGD, schedules, Adam,Adadelta
from keras.layers import Conv2D, Conv2DTranspose
from keras.layers import MaxPooling2D, GlobalMaxPool2D
from keras.models import Model, load_model
from tensorflow.python.keras import losses

from keras.layers import concatenate
from skimage.metrics import structural_similarity as ssim
from tensorflow.keras.utils import plot_model

"""**Load Dataset**"""

image_height = 256
image_width = 256
dpath= "/content/Dataset_BUSI_with_GT/"
classes = ['benign', 'malignant', 'normal']

data = {'image' : [],
        'mask' : []}

os.listdir(dpath)

def load_data(path, data_obj, class_name):
    img_names_list = os.listdir(path+class_name)
    image_names = []
    mask_names = []
    names_truncated = []

    for i in range(len(img_names_list)):
        names_truncated.append(img_names_list[i].split(')')[0])

    names_truncated = list(set(names_truncated))

    for i in range(len(names_truncated)):
        image_names.append(names_truncated[i]+').png')
        mask_names.append(names_truncated[i]+')_mask.png')

    data_obj = preprocess_data(image_names, mask_names, image_width, image_height, path, class_name, data_obj)


    return data_obj

"""**Data Preprocessing**"""

def preprocess_data(image_names, mask_names, img_width, img_height, dpath, dclass, data_obj):
    for index in range (len(image_names)):
        image_path = dpath+'/'+dclass+'/'+ image_names[index]
        mask_path = dpath+'/'+dclass+'/'+ mask_names[index]

        x = cv2.imread(image_path, cv2.IMREAD_COLOR)
        x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB)
        x = np.round(cv2.resize(x, (image_height, image_width)))
        x.dtype = np.uint8
        y = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        y = cv2.resize(y, (image_height, image_width))

        x= x/255.0
        y= y/255.0
        data_obj['image'].append(x)
        data_obj['mask'].append(y)

    return data_obj

data = load_data(dpath, data, classes[0])
ln = len(data['image'])
print("Number of benign tumor images", ln)
data = load_data(dpath, data, classes[1])
print("Number of malignant tumor images", len(data['image'])-ln)
print("Total images for segmentation", len(data['image']))

type(data['image'])

data['mask'][0].shape

"""**Visualization**"""

def visualize_example(data, index = None):
    if index is None:
        index = random.randint(0, len(data['image']))
    X = data['image']
    y = data['mask']
    has_mask = y[index].max() > 0

    fig, ax = plt.subplots(1, 2, figsize=(20, 10))
    ax[0].imshow(X[index])
    if has_mask:
        ax[0].contour(y[index].squeeze(), colors='k', levels=[0.5])
    ax[0].set_title('Image')

    ax[1].imshow(y[index].squeeze())
    ax[1].set_title('Mask')

visualize_example(data)

data['image'] = np.array(data['image'])
data['image'].shape

data['mask'] = np.array(data['mask'])
data['mask'] =  np.expand_dims(data['mask'], -1)
data['mask'].shape

"""**Train-Test Split**"""

X_train, X_test, y_train, y_test = train_test_split(data['image'], data['mask'], test_size=0.1, random_state=42)
print(len(X_train), len(y_train), len(X_test), len(y_test))

X_train.shape

tf.keras.backend.clear_session()

"""**Loss Function**"""

def dice_coeff(y_true, y_pred):
    smooth = 1.
    # Flatten
    y_true_f = tf.reshape(y_true, [-1])
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    score = (2. * intersection + smooth) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + smooth)
    return score

def dice_loss(y_true, y_pred):
    loss = 1 - dice_coeff(y_true, y_pred)
    return loss

def tot_loss(y_true,y_pred):
  l1=losses.binary_crossentropy(y_true, y_pred)
  l2= dice_loss(y_true,y_pred)
  l=l1+l2
  # l=l2
  return l

"""**Models**"""

# def bn_act(x, act=True):
#   #'batch normalization layer with an optinal activation layer'
#   x = tf.keras.layers.BatchNormalization()(x)
#   if act == True:
#     x = tf.keras.layers.Activation('relu')(x)
#   return x

# def conv_block(x, filters, kernel_size=3, padding='same', strides=1):
#     # 'convolutional layer which always uses the batch normalization layer'

#     conv = bn_act(x)
#     conv = Conv2D(filters, kernel_size, padding=padding, strides=strides)(conv)
#     return conv

# def stem(x, filters, kernel_size=3, padding='same', strides=1):
#     conv = Conv2D(filters, kernel_size, padding=padding, strides=strides)(x)
#     conv = conv_block(conv, filters, kernel_size, padding, strides)
#     shortcut = Conv2D(filters, kernel_size=1, padding=padding, strides=strides)(x)
#     shortcut = bn_act(shortcut, act=False)
#     output = Add()([conv, shortcut])
#     return output

# def residual_block(x, filters, kernel_size=3, padding='same', strides=1):
#     res = conv_block(x, filters, kernel_size, padding, strides)
#     res = conv_block(res, filters, kernel_size, padding, 1)
#     shortcut = Conv2D(filters, kernel_size, padding=padding, strides=strides)(x)
#     shortcut = bn_act(shortcut, act=False)
#     output = Add()([shortcut, res])
#     return output

# def upsample_concat_block(x, xskip):
#   u = UpSampling2D((2,2))(x)
#   c = concatenate([u, xskip],)
#   return c

# *************** ResUNet *********************
# def ResUNet(img_h, img_w):
#     f = [16, 32, 64, 128, 256]
#     inputs = Input((img_h, img_w, 3))

#     ## Encoder
#     e0 = inputs
#     e1 = stem(e0, f[0])
#     p1= Dropout(0.4)(e1)


#     e2 = residual_block(p1, f[1], strides=2)
#     p2= Dropout(0.4)(e2)


#     e3 = residual_block(p2, f[2], strides=2)
#     p3= Dropout(0.3)(e3)


#     e4 = residual_block(p3, f[3], strides=2)
#     p4= Dropout(0.3)(e4)

#     e5 = residual_block(p4, f[4], strides=1)

#     ## Bridge
#     # b0 = conv_block(e4, f[3], strides=1)
#     # b1 = conv_block(b0, f[3], strides=1)
#     p5 = MaxPooling2D((2, 2))(e5)
#     ## Decoder
#     u1 = upsample_concat_block(p5, e4)
#     d1 = residual_block(u1, f[3])
#     p6=Dropout(0.4)(d1)


#     u2 = upsample_concat_block(p6, e3)
#     d2 = residual_block(u2, f[2])
#     p7= Dropout(0.4)(d2)

#     u3 = upsample_concat_block(p7, e2)
#     d3 = residual_block(u3, f[1])
#     p8=Dropout(0.3)(d3)


#     u4 = upsample_concat_block(d3, e1)
#     d4 = residual_block(u4, f[0])
#     p9= Dropout(0.3)(d4)

#     outputs = tf.keras.layers.Conv2D(1, (1, 1), padding="same", activation="sigmoid")(p9)
#     model = tf.keras.models.Model(inputs, outputs)
#     return model

# #****************** U Net Architecture****************************
# def conv2d_block(input_tensor, n_filters, kernel_size = 3, batchnorm = True):
#     # first layer
#     x = Conv2D(filters = n_filters, kernel_size = (kernel_size, kernel_size),\
#               kernel_initializer = 'he_normal', padding = 'same')(input_tensor)
#     if batchnorm:
#         x = BatchNormalization()(x)
#     x = Activation('relu')(x)

#     # second layer
#     x = Conv2D(filters = n_filters, kernel_size = (kernel_size, kernel_size),\
#               kernel_initializer = 'he_normal', padding = 'same')(input_tensor)
#     if batchnorm:
#         x = BatchNormalization()(x)
#     x = Activation('relu')(x)

#     return x
# def get_unet(input_img, n_filters = 16, dropout = 0.3, batchnorm = True):
#     # Contracting Path
#     c1 = conv2d_block(input_img, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)
#     p1 = MaxPooling2D((2, 2))(c1)
#     p1 = Dropout(dropout)(p1)

#     c2 = conv2d_block(p1, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)
#     p2 = MaxPooling2D((2, 2))(c2)
#     p2 = Dropout(dropout)(p2)

#     c3 = conv2d_block(p2, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)
#     p3 = MaxPooling2D((2, 2))(c3)
#     p3 = Dropout(dropout)(p3)

#     c4 = conv2d_block(p3, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)
#     p4 = MaxPooling2D((2, 2))(c4)
#     p4 = Dropout(dropout)(p4)

#     c5 = conv2d_block(p4, n_filters = n_filters * 16, kernel_size = 3, batchnorm = batchnorm)

#     # Expansive Path
#     u6 = Conv2DTranspose(n_filters * 8, (3, 3), strides = (2, 2), padding = 'same')(c5)
#     u6 = concatenate([u6, c4])
#     u6 = Dropout(dropout)(u6)
#     c6 = conv2d_block(u6, n_filters * 8, kernel_size = 3, batchnorm = batchnorm)

#     u7 = Conv2DTranspose(n_filters * 4, (3, 3), strides = (2, 2), padding = 'same')(c6)
#     u7 = concatenate([u7, c3])
#     u7 = Dropout(dropout)(u7)
#     c7 = conv2d_block(u7, n_filters * 4, kernel_size = 3, batchnorm = batchnorm)

#     u8 = Conv2DTranspose(n_filters * 2, (3, 3), strides = (2, 2), padding = 'same')(c7)
#     u8 = concatenate([u8, c2])
#     u8 = Dropout(dropout)(u8)
#     c8 = conv2d_block(u8, n_filters * 2, kernel_size = 3, batchnorm = batchnorm)

#     u9 = Conv2DTranspose(n_filters * 1, (3, 3), strides = (2, 2), padding = 'same')(c8)
#     u9 = concatenate([u9, c1])
#     u9 = Dropout(dropout)(u9)
#     c9 = conv2d_block(u9, n_filters * 1, kernel_size = 3, batchnorm = batchnorm)

#     outputs = Conv2D(1, (1, 1), activation='sigmoid')(c9)
#     model = Model(inputs=[input_img], outputs=[outputs])
#     return model

# ******* Nested UNet*********
# def conv_block(inputs, n_filters, kernel_size=3, activation='relu', padding='same', kernel_initializer='he_normal'):
#     c = Conv2D(n_filters, kernel_size, activation=activation, padding=padding, kernel_initializer=kernel_initializer)(inputs)
#     c = BatchNormalization()(c)
#     c = Conv2D(n_filters, kernel_size, activation=activation, padding=padding, kernel_initializer=kernel_initializer)(c)
#     c = BatchNormalization()(c)
#     return c

# def nested_unet_model(IMG_HEIGHT=256, IMG_WIDTH=256, IMG_CHANNELS=3):
#     # Build the model
#     inputs = Input((IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS))
#     s = inputs

#     # Contracting path
#     c1 = conv_block(s, 16)
#     p1 = MaxPooling2D((2, 2))(c1)
#     c2 = conv_block(p1, 32)
#     p2 = MaxPooling2D((2, 2))(c2)
#     c3 = conv_block(p2, 64)
#     p3 = MaxPooling2D((2, 2))(c3)
#     c4 = conv_block(p3, 128)
#     p4 = MaxPooling2D(pool_size=(2, 2))(c4)
#     c5 = conv_block(p4, 256)

#     # Expansive path
#     u6 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(c5)
#     u6 = concatenate([u6, c4])
#     c6 = conv_block(u6, 128)
#     u7 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(c6)
#     u7 = concatenate([u7, c3])
#     c7 = conv_block(u7, 64)
#     u8 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(c7)
#     u8 = concatenate([u8, c2])
#     c8 = conv_block(u8, 32)
#     u9 = Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same')(c8)
#     u9 = concatenate([u9, c1], axis=3)
#     c9 = conv_block(u9, 16)

#     outputs = Conv2D(1, (1, 1), activation='sigmoid')(c9)

#     model = Model(inputs=[inputs], outputs=[outputs])
#     return model

# def attention_block(x, shortcut, filters, kernel_size=(3, 3), padding="same"):
#     g1 = Conv2D(filters, kernel_size, padding=padding)(x)
#     g1 = BatchNormalization()(g1)
#     x1 = Conv2D(filters, kernel_size, padding=padding)(shortcut)
#     x1 = BatchNormalization()(x1)
#     f = Activation('relu')(g1 + x1)
#     g2 = Conv2D(filters, kernel_size, padding=padding)(f)
#     g2 = BatchNormalization()(g2)
#     x2 = Conv2D(filters, kernel_size, padding=padding)(f)
#     x2 = BatchNormalization()(x2)
#     h = Activation('sigmoid')(g2 + x2)
#     return f * h + f

# def attention_unetplusplus_model(IMG_HEIGHT=256, IMG_WIDTH=256, IMG_CHANNELS=3):
#     # Build the model
#     inputs = Input((IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS))
#     #s = Lambda(lambda x: x / 255)(inputs)   # No need for this if we normalize our inputs beforehand
#     s = inputs

#     # Contraction path
#     c1 = Conv2D(16, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(s)
#     c1 = Dropout(0.1)(c1)
#     c1 = Conv2D(16, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c1)
#     p1 = MaxPooling2D((2, 2))(c1)

#     c2 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(p1)
#     c2 = Dropout(0.1)(c2)
#     c2 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c2)
#     p2 = MaxPooling2D((2, 2))(c2)

#     c3 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(p2)
#     c3 = Dropout(0.2)(c3)
#     c3 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c3)
#     p3 = MaxPooling2D((2, 2))(c3)

#     c4 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(p3)
#     c4 = Dropout(0.2)(c4)
#     c4 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c4)
#     p4 = MaxPooling2D(pool_size=(2, 2))(c4)

#     c5 = Conv2D(256, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(p4)
#     c5 = Dropout(0.3)(c5)
#     c5 = Conv2D(256, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c5)

#         # Expansive path
#     u6 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(c5)
#     u6 = concatenate([u6, c4])
#     u6 = Dropout(0.2)(u6)
#     u6 = attention_block(u6, c4, 128)
#     c6 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(u6)
#     c6 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c6)

#     u7 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(c6)
#     u7 = concatenate([u7, c3])
#     u7 = Dropout(0.2)(u7)
#     u7 = attention_block(u7, c3, 64)
#     c7 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(u7)
#     c7 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c7)

#     u8 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(c7)
#     u8 = concatenate([u8, c2])
#     u8 = Dropout(0.1)(u8)
#     u8 = attention_block(u8, c2, 32)
#     c8 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(u8)
#     c8 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c8)

#     u9 = Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same')(c8)
#     u9 = concatenate([u9, c1])
#     u9 = Dropout(0.1)(u9)
#     u9 = attention_block(u9, c1, 16)
#     c9 = Conv2D(16, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(u9)
#     c9 = Conv2D(16, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c9)

#     outputs = Conv2D(1, (1, 1), activation='sigmoid')(c9)

#     model = Model(inputs=[inputs], outputs=[outputs])
#     return model

# def conv_block(inputs, n_filters, kernel_size=3, batchnorm=False, activation='relu'):
#     x = Conv2D(n_filters, kernel_size, padding='same')(inputs)
#     if batchnorm:
#         x = BatchNormalization()(x)
#     x = Activation(activation)(x)
#     x = Conv2D(n_filters, kernel_size, padding='same')(x)
#     if batchnorm:
#         x = BatchNormalization()(x)
#     x = Activation(activation)(x)
#     return x

# def up_conv_block(inputs, n_filters, kernel_size=2, batchnorm=False, activation='relu'):
#     x = Conv2DTranspose(n_filters, kernel_size, strides=(2, 2), padding='same')(inputs)
#     if batchnorm:
#         x = BatchNormalization()(x)
#     x = Activation(activation)(x)
#     return x

# def unet_pp3_model(IMG_HEIGHT=256, IMG_WIDTH=256, IMG_CHANNELS=3):
#     # Build the model
#     inputs = Input((IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS))

#     # Level 1
#     c1 = conv_block(inputs, 16, batchnorm=True)
#     p1 = MaxPooling2D((2, 2))(c1)

#     # Level 2
#     c2 = conv_block(p1, 32, batchnorm=True)
#     p2 = MaxPooling2D((2, 2))(c2)

#     # Level 3
#     c3 = conv_block(p2, 64, batchnorm=True)
#     p3 = MaxPooling2D((2, 2))(c3)

#     # Level 4
#     c4 = conv_block(p3, 128, batchnorm=True)
#     p4 = MaxPooling2D((2, 2))(c4)

#     # Level 5
#     c5 = conv_block(p4, 256, batchnorm=True)

#     # Level 4a
#     u4a = up_conv_block(c5, 128, batchnorm=True)
#     m4a = concatenate([u4a, c4], axis=3)
#     c4a = conv_block(m4a, 128, batchnorm=True)

#     # Level 3a
#     u3a = up_conv_block(c4a, 64, batchnorm=True)
#     m3a = concatenate([u3a, c3], axis=3)
#     c3a = conv_block(m3a, 64, batchnorm=True)

#     # Level 2a
#     u2a = up_conv_block(c3a, 32, batchnorm=True)
#     m2a = concatenate([u2a, c2], axis=3)
#     c2a = conv_block(m2a, 32, batchnorm=True)

#     # Level 1a
#     u1a = up_conv_block(c2a, 16, batchnorm=True)
#     m1a = concatenate([u1a, c1], axis=3)
#     c1a = conv_block(m1a, 16, batchnorm=True)

#     # Output layer
#     outputs = Conv2D(1, (1, 1), activation='sigmoid')(c1a)

#     model = Model(inputs=[inputs], outputs=[outputs])
#     return model

image_height= 256
image_width= 256
# input_layer= Input((image_height, image_width, 3), name='img')
model = ResUNet(image_height,image_width)
# model = get_unet(input_layer, n_filters=16, dropout=0.3, batchnorm=True)
model.summary()

"""**Step 11: Setting up Hyperparameters**"""

model.compile(optimizer=Adam(),
                  loss= tot_loss,
                  metrics=[dice_loss, dice_coeff, 'accuracy'])

callbacks = [
    ReduceLROnPlateau(factor=0.1, patience=5, min_lr=0.0001, verbose=1),
    ModelCheckpoint('model-checkpoint.h5', verbose=1, save_best_only=True, save_weights_only=True)
]

batch_size = 32
epochs = 70

# import tensorflow as tf
# print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

tf.debugging.set_log_device_placement(True)

l_train= len(X_train)
u= np.arange(0,l_train)
print(len(u))

"""**Training the Model**"""

for i in range(3):
  u= np.arange(0,l_train)
  newarr = np.array_split(u, 3)
  x_valid= X_train[newarr[i]]
  y_valid= y_train[newarr[i]]

  newarr= np.delete(newarr, [i],axis=0)
  # x_train= X_train[newarr[0]]
  # yy_train= y_train[newarr[0]]
  x_train= X_train[np.concatenate((newarr[0],newarr[1]),axis=0)]
  yy_train= y_train[np.concatenate((newarr[0],newarr[1]),axis=0)]

  model_history = model.fit(x_train,yy_train,
                    batch_size=batch_size,
                    steps_per_epoch=int(np.ceil(len(X_train) / float(batch_size))),
                    epochs=epochs,
                    callbacks=callbacks,
                    validation_data=(x_valid, y_valid),
                    verbose = 1)
  plt.figure(figsize=(6, 6))
  plt.title("Learning curve")
  plt.plot(model_history.history["loss"], label="loss")
  plt.plot(model_history.history["val_loss"], label="val_loss")
  plt.plot( np.argmin(model_history.history["val_loss"]), np.min(model_history.history["val_loss"]), marker="x", color="r", label="best model")
  plt.xlabel("Epochs")
  plt.ylabel("log_loss")
  plt.legend();

"""**Learning Curve Visualization**"""

plt.figure(figsize=(6, 6))
plt.title("Learning curve")
plt.plot(model_history.history["loss"], label="loss")
plt.plot(model_history.history["val_loss"], label="val_loss")
plt.plot( np.argmin(model_history.history["val_loss"]), np.min(model_history.history["val_loss"]), marker="x", color="r", label="best model")
plt.xlabel("Epochs")
plt.ylabel("loss")
plt.legend();

plt.figure(figsize=(6, 6))
plt.title("Dice loss")
plt.plot(model_history.history["dice_loss"], label="Dice loss")
plt.plot(model_history.history["val_dice_loss"], label="validation dice loss")
# plt.plot( np.argmin(model_history.history["val_loss"]), np.min(model_history.history["val_loss"]), marker="x", color="r", label="best model")
plt.xlabel("Epochs")
plt.ylabel("loss")
plt.legend();

plt.figure(figsize=(6, 6))
plt.title("Dice Coefficient")
plt.plot(model_history.history["dice_coeff"], label="Dice Coefficient")
plt.plot(model_history.history["val_dice_coeff"], label="validation Dice Coefficient")

# plt.plot( np.argmin(model_history.history["val_loss"]), np.min(model_history.history["val_loss"]), marker="x", color="r", label="best model")
plt.xlabel("Epochs")
# plt.ylabel("loss")
plt.legend();

plt.figure(figsize=(6, 6))
plt.title("Accuracy")
plt.plot(model_history.history["accuracy"], label="Accuracy")
plt.plot(model_history.history["val_accuracy"], label="validation accuracy")

# plt.plot( np.argmin(model_history.history["val_loss"]), np.min(model_history.history["val_loss"]), marker="x", color="r", label="best model")
plt.xlabel("Epochs")
# plt.ylabel("loss")
plt.legend();

"""**Evaluating the model on test sets**"""

model.load_weights('model-checkpoint.h5')
model.evaluate(X_test, y_test, verbose=1)

preds_test = model.predict(X_test, verbose=1)
preds_test_t = (preds_test > 0.8).astype(np.uint8)

"""**Manual Testing**"""

def plot_sample(X, y, preds, binary_preds, ix=None):
    if ix is None:
        ix = random.randint(0, len(X))

    for i in range(len(X)//4):
      has_mask = y[i].max() > 0

      fig, ax = plt.subplots(1, 4, figsize=(20, 10))
      ax[0].imshow(X[i])
      if has_mask:
        ax[0].contour(y[i].squeeze(), colors='k', levels=[0.5])
      ax[0].set_title('Image')

      ax[1].imshow(y[i].squeeze())
      ax[1].set_title('Mask')

      ax[2].imshow(preds[i].squeeze(), vmin=0, vmax=1)
      ax[2].set_title('Mask Predicted')

      ax[3].imshow(binary_preds[i].squeeze(), vmin=0, vmax=1)
      ax[3].set_title('Mask Predicted binary');

#@title Default title text
plot_sample(X_test, y_test, preds_test, preds_test_t)

