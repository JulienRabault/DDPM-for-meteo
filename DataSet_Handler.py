#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 11 13:54:10 2022

@author: brochetc

DataSet class from Importance_Sampled images

"""

import os

import numpy as np
import pandas as pd
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torch.utils.data import Dataset

################ reference dictionary to know what variables to sample where
################ do not modify unless you know what you are doing 

var_dict = {'rr': 0, 'u': 1, 'v': 2, 't2m': 3, 'orog': 4}


################
class ISDataset(Dataset):

    def __init__(self, data_dir, ID_file, var_indexes, crop_indexes, \
                 transform, add_coords=False):
        self.data_dir = data_dir
        self.transform = transform
        self.labels = pd.read_csv(data_dir + ID_file)

        ## portion of data to crop from (assumed fixed)

        self.CI = crop_indexes
        self.VI = var_indexes
        # self.coef_avg2D = coef_avg2D

        ## adding 'positional encoding'
        self.add_coords = add_coords
        Means = np.load(data_dir + 'mean_with_orog.npy')[self.VI]
        Maxs = np.load(data_dir + 'max_with_orog.npy')[self.VI]
        self.means = list(tuple(Means))
        self.stds = list(tuple((1.0 / 0.95) * (Maxs)))

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # idx=idx+19
        sample_path = os.path.join(self.data_dir, self.labels.iloc[idx, 0])
        # print(sample_path, idx)
        sample = np.float32(np.load(sample_path + '.npy')) \
            [self.VI, self.CI[0]:self.CI[1], self.CI[2]:self.CI[3]]
        # print("where I am", len(sample))
        importance = self.labels.iloc[idx, 1]
        position = self.labels.iloc[idx, 2]

        ## transpose to get off with transform.Normalize builtin transposition
        sample = sample.transpose((1, 2, 0))
        # sample[:,:,2]=2.*(sample[:,:,2]-251.14634704589844)/(315.44622802734375-251.14634704589844)-1.
        # sample[:,:,0]=2.*(sample[:,:,0]+27.318836212158203)/(29.181968688964844 + 27.318836212158203)-1.
        # sample[:,:,1]=2.*(sample[:,:,1]+25.84168815612793)/(27.698963165283203 + 25.84168815612793)-1.
        self.transform = transforms.Compose(
            [
                # transforms.ToPILImage(),
                # transforms.Resize((self.img_size, self.img_size)),
                transforms.ToTensor(),
                transforms.Normalize(self.means, self.stds),
                # transforms.Lambda(lambda x: torch.nn.functional.avg_pool2d(x, kernel_size=self.coef_avg2D,
                #                                                           stride=self.coef_avg2D)),
                # transforms.RandomHorizontalFlip(p=0.5),
                # transforms.Normalize(
                #     [0.5 for _ in range(config.CHANNELS_IMG)],
                #     [0.5 for _ in range(config.CHANNELS_IMG)],
                # ),
            ]
        )

        sample = self.transform(sample)
        # print(sample.size())

        # , importance, position

        return sample


class ISData_Loader():

    def __init__(self, path, batch_size, var_indexes, crop_indexes, \
                 shuf=False, add_coords=False, device='cuda'):
        self.path = path
        self.batch = batch_size

        self.shuf = shuf  # shuffle performed once per epoch

        self.VI = var_indexes
        self.CI = crop_indexes
        # self.img_size=img_size

        Means = np.load(path + 'mean_with_orog.npy')[self.VI]
        Maxs = np.load(path + 'max_with_orog.npy')[self.VI]

        self.means = list(tuple(Means))
        self.stds = list(tuple((1.0 / 0.95) * (Maxs)))
        self.add_coords = add_coords

    # def transform(self, totensor, normalize):

    #     print("I'm never here bro")
    #     options = []
    #     if totensor:
    #         options.append(ToTensor())

    #     if normalize:
    #         options.append(Normalize(self.means, self.stds))

    #     transform = Compose(options)
    #     return transform

    def loader(self):
        from multiprocessing import cpu_count
        self.device = 'cuda'
        dataset = ISDataset(self.path, 'IS_method_labels.csv', self.VI, self.CI, self.device)

        loader = DataLoader(dataset=dataset,
                            batch_size=self.batch,
                            num_workers=cpu_count(),
                            pin_memory=True,
                            shuffle=True,
                            drop_last=True,
                            )
        return loader, dataset
