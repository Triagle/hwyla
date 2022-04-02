#!/usr/bin/env python3

from distutils.core import setup


setup(
    name="hwyla",
    version="1.0",
    description="Local detexify clone",
    author="Jake Faulkner",
    author_email="jakefaulkn@gmail.com",
    packages=["hwyla", "hwyla.icons", "hwyla.model_tflite"],
    install_requires=["pycairo", "pyclip", "pygobject", "tensorflow"],
    scripts=["runhwyla"],
    package_data={"hwyla": ["icons/*.svg", "model_tflite/model.tflite"]},
)
