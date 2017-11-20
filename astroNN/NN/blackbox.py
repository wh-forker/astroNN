# ---------------------------------------------------------#
#   astroNN.NN.blackbox: eval NN attention via sliding a blackbox
# ---------------------------------------------------------#
import os
import time
from functools import reduce

import h5py
import numpy as np
import pylab as plt
import seaborn as sns
import tensorflow as tf
import matplotlib.ticker as ticker

from keras.backend.tensorflow_backend import set_session
from keras.models import load_model

from astroNN.NN.test import batch_predictions, target_name_conversion
from astroNN.shared.nn_tools import h5name_check

import pandas as pd
from urllib.request import urlopen

def url_correction(targetname):
    if len(targetname) < 2:
        fullname = '{}'.format(targetname)
    elif targetname == 'teff':
        fullname = '$T_{\mathrm{eff}}$'
    elif targetname == 'alpha':
        fullname = '[Alpha/M]'
    elif targetname == 'logg':
        fullname = '[Log(g)]'
    elif targetname == 'Ti2':
        fullname = 'TiII'
    elif targetname == 'Cl':
        fullname = 'CI'
    else:
        fullname = targetname
    return fullname

def blackbox_eval(h5name=None, folder_name=None):
    """
    NAME: blackbox_eval
    PURPOSE: To eval NN attention via sliding a blackbox
    INPUT:
        h5name = Name of the h5 data set
        folder_name = the folder name contains the model
    OUTPUT: plots
    HISTORY:
        2017-Nov-17 Henry Leung
    """

    # prevent Tensorflow taking up all the GPU memory
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    set_session(tf.Session(config=config))

    h5name_check(h5name)

    traindata = h5name + '_train.h5'

    currentdir = os.getcwd()
    fullfolderpath = currentdir + '/' + folder_name
    print(fullfolderpath)
    mean_and_std = np.load(fullfolderpath + '/meanstd.npy')
    spec_meanstd = np.load(fullfolderpath + '/spectra_meanstd.npy')
    target = np.load(fullfolderpath + '/targetname.npy')
    modelname = '/model_{}.h5'.format(folder_name[-11:])
    model = load_model(os.path.normpath(fullfolderpath + modelname))

    mean_labels = mean_and_std[0]
    std_labels = mean_and_std[1]
    num_labels = mean_and_std.shape[1]

    # ensure the file will be cleaned up
    with h5py.File(traindata) as F:
        i = 0
        index_not9999 = []
        for tg in target:
            temp = np.array(F['{}'.format(tg)])
            temp_index = np.where(temp != -9999)
            if i == 0:
                index_not9999 = temp_index
                i += 1
            else:
                index_not9999 = reduce(np.intersect1d, (index_not9999, temp_index))
        number_spectra = 100
        index_not9999 = index_not9999[0:number_spectra]

        test_spectra = np.array(F['spectra'])
        test_spectra = test_spectra[index_not9999]
        test_spectra -= spec_meanstd[0]
        test_spectra /= spec_meanstd[1]

        i = 0
        test_labels = []
        for tg in target:  # load data
            temp = np.array(F['{}'.format(tg)])
            temp = temp[index_not9999]
            if i == 0:
                test_labels = temp[:]
                if len(target) == 1:
                    test_labels = test_labels.reshape((len(test_labels), 1))
                i += 1
            else:
                test_labels = np.column_stack((test_labels, temp[:]))

    prediction = batch_predictions(model, test_spectra, number_spectra, num_labels, std_labels, mean_labels)

    print('Test set contains ' + str(len(test_spectra)) + ' stars')

    time1 = time.time()
    test_predictions = []
    for j in range(7514):
        temp = np.copy(test_spectra)
        temp[:,j:j+8] = 0
        test_predictions.extend([batch_predictions(model, temp, number_spectra, num_labels, std_labels, mean_labels) - prediction])
    print("{0:.2f}".format(time.time() - time1) + ' seconds to make ' + str(len(test_spectra)) + ' predictions')

    resid = np.median(test_predictions, axis=1)

    # Some plotting variables for asthetics
    plt.rcParams['axes.facecolor'] = 'white'
    sns.set_style("ticks")
    plt.rcParams['axes.grid'] = False
    plt.rcParams['grid.color'] = 'gray'
    plt.rcParams['grid.alpha'] = '0.4'

    for i in range(num_labels):

        fullname = target_name_conversion(target[i])

        fig = plt.figure(figsize=(45, 30), dpi=150)
        scale = np.max(np.abs((resid[:, i])))
        blue = np.abs((resid[:, i])[0:3028])
        greeen = np.abs((resid[:, i])[3028:5523])
        red = np.abs((resid[:, i])[5523:])
        lambda_blue = np.linspace(15146, 15910, 3028, endpoint=True)
        lambda_green = np.linspace(15961, 16434, 2495, endpoint=True)
        lambda_red = np.linspace(16476, 16953, 1991, endpoint=True)
        # plt.axhline(0, ls='--', c='k', lw=2)
        ax1 = fig.add_subplot(311)
        fig.suptitle('{}, Average of {} Stars'.format(fullname, number_spectra), fontsize=50)
        ax1.set_ylabel('Attention (Blue chip)', fontsize=40)
        ax1.set_ylim(0,scale)
        ax1.plot(lambda_blue, blue, linewidth=0.9, label='astroNN')
        ax2 = fig.add_subplot(312)
        ax2.set_ylabel('Attention (Green chip)', fontsize=40)
        ax2.set_ylim(0,scale)
        ax2.plot(lambda_green, greeen, linewidth=0.9, label='astroNN')
        ax3 = fig.add_subplot(313)
        ax3.set_ylim(0,scale)
        ax3.set_ylabel('Attention (Red chip)', fontsize=40)
        ax3.plot(lambda_red, red, linewidth=0.9, label='astroNN')
        ax3.set_xlabel(r'Wavelength (Angstrom)', fontsize=40)
        try:
            url = "https://svn.sdss.org/public/repo/apogee/idlwrap/trunk/lib/l31c/{}.mask".format(url_correction(target[i]))
            df = np.array(pd.read_csv(urlopen(url), header=None, sep='\t'))
            print(url)
            aspcap_windows = df*scale
            aspcap_blue = aspcap_windows[0:3028]
            aspcap_greeen = aspcap_windows[3028:5523]
            aspcap_red = aspcap_windows[5523:]
            ax1.plot(lambda_blue, aspcap_blue, linewidth=0.9, label='ASPCAP windows')
            ax2.plot(lambda_green, aspcap_greeen, linewidth=0.9, label='ASPCAP windows')
            ax3.plot(lambda_red, aspcap_red, linewidth=0.9, label='ASPCAP windows')
        except:
            print('No ASPCAP windows data for {}'.format(url_correction(target[i])))
        path = os.path.join(fullfolderpath, 'blackbox')
        if not os.path.exists(path):
            os.makedirs(path)
        tick_spacing = 50
        ax1.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
        ax2.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing/1.5))
        ax3.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing/1.7))

        ax1.minorticks_on()
        ax2.minorticks_on()
        ax3.minorticks_on()

        ax1.tick_params(labelsize=30, width=1, length=5)
        ax2.tick_params(labelsize=30, width=1, length=5)
        ax3.tick_params(labelsize=30, width=1, length=5)
        ax1.legend(loc='best', fontsize=40)
        plt.tight_layout()
        plt.subplots_adjust(left=0.05)
        plt.savefig(path + '/{}.png'.format(target[i]))
        plt.close('all')
        plt.clf()