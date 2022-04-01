#!/usr/bin/env python3

import tensorflow as tf
import symbols

MODEL_FILE = "./model.tflite"


def _scale_time_and_coordinates(strokes):
    """Scale coordinates so that the lowest and leftmost sample is at (0, 0) and the highest and rightmost sample is at (1, 1). Time is converted to dt from the last stroke."""

    min_x = min(s[1] for s in strokes)
    max_x = max(s[1] for s in strokes)
    min_y = min(s[2] for s in strokes)
    max_y = max(s[2] for s in strokes)

    # In this degenerate case the bounding rect is either a point or a line, we make the box slightly bigger so that the coordinates still work out.

    if min_y == max_y:
        max_y += 1
    if min_x == max_x:
        max_x += 1

    dx = max_x - min_x
    dy = max_y - min_y

    t_prev = strokes[0][0]
    out = []
    for s in strokes:
        out.append(((s[0] - t_prev) / 1000, (s[1] - min_x) / dx, (s[2] - min_y) / dy))
        t_prev = s[0]

    return out


class Classifier:
    def __init__(self):
        self.model = tf.lite.Interpreter(MODEL_FILE)
        self.model.allocate_tensors()

    def classify(self, samples, k=5):

        sample = tf.constant([_scale_time_and_coordinates(samples)])
        self.model.resize_tensor_input(0, sample.shape)
        self.model.allocate_tensors()
        self.model.set_tensor(0, sample)
        self.model.invoke()
        output_idx = self.model.get_output_details()[0]["index"]
        output_data = self.model.get_tensor(output_idx)
        out = tf.math.top_k(output_data, k=k).indices.numpy()[0]
        return [symbols.CLASSES[c] for c in out]
