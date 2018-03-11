import unittest
from keras.datasets import mnist
from keras.utils import np_utils
import numpy as np


from astroNN.models import Cifar10_CNN, Galaxy10_CNN
from astroNN.models import load_folder


class Models_TestCase(unittest.TestCase):
    def test_mnist(self):
        (x_train, y_train), (x_test, y_test) = mnist.load_data()
        y_train = np_utils.to_categorical(y_train, 10)

        # To convert to desirable type
        x_train = x_train.astype(np.float32)
        x_test = x_test.astype(np.float32)
        y_train = y_train.astype(np.float32)

        # create model instance
        mnist_test = Cifar10_CNN()
        mnist_test.max_epochs = 1

        mnist_test.train(x_train[:1000], y_train[:1000])
        mnist_test.test(x_test[:1000])

        # create model instance for binary classification
        mnist_test = Cifar10_CNN()
        mnist_test.max_epochs = 1
        mnist_test.task = 'binary_classification'

        mnist_test.train(x_train[:1000], y_train[:1000])
        prediction = mnist_test.test(x_test[:1000])

        mnist_test.save('mnist_test')
        mnist_reloaded = load_folder("mnist_test")
        prediction_loaded = mnist_reloaded.test(x_test[:1000])

        # Cifar10_CNN is deterministic
        np.testing.assert_array_equal(prediction, prediction_loaded)

    def test_color_images(self):
        # test colored 8bit images
        (x_train, y_train), (x_test, y_test) = mnist.load_data()
        x_train = np.random.randint(0, 255, size=(1000, 28, 28, 3))
        x_test = np.random.randint(0, 255, size=(100, 28, 28, 3))
        y_train = y_train[:1000]
        y_train = np_utils.to_categorical(y_train, 10)
        # To convert to desirable type

        x_train = x_train.astype(np.float32)
        x_test = x_test.astype(np.float32)
        y_train = y_train.astype(np.float32)

        # create model instance
        mnist_test = Cifar10_CNN()
        mnist_test.max_epochs = 1

        mnist_test.train(x_train, y_train[:1000])
        mnist_test.test(x_test[:1000])

        # create model instance for binary classification
        mnist_test = Galaxy10_CNN()
        mnist_test.max_epochs = 1

        mnist_test.train(x_train[:1000], y_train[:1000])
        prediction = mnist_test.test(x_test[:1000])

        mnist_test.save('cifar10_test')
        mnist_reloaded = load_folder("cifar10_test")
        prediction_loaded = mnist_reloaded.test(x_test[:1000])

        # Cifar10_CNN is deterministic
        np.testing.assert_array_equal(prediction, prediction_loaded)


if __name__ == '__main__':
    unittest.main()