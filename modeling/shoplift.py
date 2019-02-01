CLASSES = {
    0: "Face-or-head",
    1: "Left-hand",
    2: "Right-hand",
    3: "Body"
}
STATES = {
    0: "Lookout",
    1: "Talking-to-someone",
    2: "Taking-objects",
    3: "Open-bag-pocket",
    4: "Close-bag-pocket",
    5: "Pointing",
    6: "Using-phones",
    7: "Put-sth-into-bag-pocket",
    8: "Walking",
    9: "Running",
    10: "Standing"
}

_CLASSES = {}
for k in CLASSES:
    _CLASSES[CLASSES[k]] = k
_STATES = {}
for k in STATES:
    _STATES[STATES[k]] = k

CLASS_TO_STATE = {
    0: [0, 1],
    1: [2, 3, 4, 5, 6, 7],
    2: [2, 3, 4, 5, 6, 7],
    3: [8, 9, 10]
}
STATE_TO_CLASS = {
    0: 0,
    1: 0,
    2: [1, 2],
    3: [1, 2],
    4: [1, 2],
    5: [1, 2],
    6: [1, 2],
    7: [1, 2],
    8: 3,
    9: 3,
    10: 3
}

import json
import logging
import os.path

import cv2
import numpy as np
import torch
import torch.utils.data as data_utl
from PIL import Image
from tqdm import tqdm
from sklearn.model_selection import KFold

from modeling import *

logger = logging.getLogger(__name__)


def video_to_tensor(pic):
    """Convert a ``numpy.ndarray`` to tensor.
    Converts a numpy.ndarray (T x H x W x C)
    to a torch.FloatTensor of shape (C x T x H x W)

    Args:
         pic (numpy.ndarray): Video to be converted to tensor.
    Returns:
         Tensor: Converted video.
    """
    return torch.from_numpy(pic.transpose([3, 0, 1, 2]))


def load_rgb_frames(v, start, num):
    image_dir = os.path.join(settings.BASE_DIR, 'static', 'frames', v.slug)
    frames = []
    for i in range(start, start + num):
        img = cv2.imread(v.getframepath(frame=i, base=image_dir))[:, :, [2, 1, 0]]
        w, h, c = img.shape
        if w < 226 or h < 226:
            d = 226. - min(w, h)
            sc = 1 + d / min(w, h)
            img = cv2.resize(img, dsize=(0, 0), fx=sc, fy=sc)
        img = (img / 255.) * 2 - 1
        frames.append(img)
    return np.asarray(frames, dtype=np.float32)


def load_flow_frames(v, start, num):
    image_dir = os.path.join(settings.BASE_DIR, 'static', 'frames', v.slug)
    frames = []
    for i in range(start, start + num - 1):
        flowXY = np.fromfile(v.getframepath(frame=i, base=image_dir) + '.flo', dtype=np.float32)[3:]
        shape = np.fromfile(v.getframepath(frame=i, base=image_dir) + '.flo', dtype=np.int32, count=3)[1:3]

        w, h = shape
        imgX = flowXY[:w * h].reshape((w, h))
        imgY = flowXY[w * h:].reshape((w, h))
        if w < 224 or h < 224:
            d = 224. / min(w, h)
            w2 = w * d
            h2 = h * d
            imgX = Image.fromarray(imgX).resize(size=(w2, h2)).getdata()
            imgY = Image.fromarray(imgY).resize(size=(w2, h2)).getdata()

        img = np.asarray([imgX, imgY]).transpose([1, 2, 0])
        frames.append(img)
    return np.asarray(frames, dtype=np.float32)


def make_dataset(split_file, split, mode, num_classes=len(STATES)):
    dataset = []
    with open(split_file, 'r') as f:
        data = json.load(f)

    i = 0
    for job_id in data.keys():
        if data[job_id]['subset'] != split:
            continue

        job = Job.objects.filter(id=job_id, completed=True).first()
        if job is None:
            continue
        num_frames = job.segment.stop - job.segment.start + 1
        if mode == 'flow':
            num_frames = num_frames - 1

        label = np.zeros((num_classes, num_frames), np.float32)

        solutions = job.solutions
        video = job.segment.video
        attributes = []
        for solution in solutions.all():
            for path in solution.paths.all():
                attributes.extend(path.attributes.all())
        for attr in tqdm(attributes):
            nf = attr.frame
            nc = _STATES[attr.attribute.text]
            if attr.value:
                label[nc, nf] = 1
        dataset.append((job, label, num_frames))
        i += 1

    return dataset


class ShopliftDataset(data_utl.Dataset):

    def __init__(self, split_file, split, mode, transforms=None):

        self.data = make_dataset(split_file, split, mode)
        self.split_file = split_file
        self.transforms = transforms
        self.mode = mode
        # self.save_dir = save_dir

    def __getitem__(self, index):
        """
        Args:
            index (int): Index

        Returns:
            tuple: (image, target) where target is class_index of the target class.
        """
        job, label, nf = self.data[index]
        v = job.segment.video
        if self.mode == 'rgb':
            imgs = load_rgb_frames(v, 0, nf)
        else:
            imgs = load_flow_frames(v, 0, nf)

        imgs = self.transforms(imgs)

        return video_to_tensor(imgs), torch.from_numpy(label), job.id

    def __len__(self):
        return len(self.data)


def get_splits(n_splits=3, group_id=2, output_dir=None):
    jobs = Job.objects.filter(group_id=group_id, completed=True).all()
    X = np.array([job.id for job in jobs])
    y = np.arange(0, len(X))
    kf = KFold(n_splits=n_splits)
    if output_dir is not None and os.path.exists(output_dir):
        i = 0
        for train_index, test_index in kf.split(X):
            with open(os.path.join(output_dir, 'fold_{}.json'.format(i+1)), 'w') as f:
                data = {}
                X_train, X_test = X[train_index], X[test_index]
                for id in X_train:
                    data[str(id)] = {'subset': 'train'}
                for id in X_test:
                    data[str(id)] = {'subset': 'test'}
                json.dump(data, f)
            f.close()
            i += 1
    return kf, X
