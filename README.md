PYANO-admin
====

![PYANO](./static/images/favicon.ico)

## Introduction

This enhanced version of [PYANO framework](http://github.com/mental689/pyano) is to implement a `many-to-many` model to data collection and annotation process using PYANO.
The old PYANO framework only supports `one-to-many` models (`one` project owner versus `many` workers).
PYANO-admin enables PYANO to have `many` project owners with fundamental operations such as adding, maintaining topics, jobs, tasks (keyword search, QBE search, web-based surveys and space-time annotations) with large degree of automation in mind.
PYANO-amdin is similar to PYANO, it is a semi-automatic framework.


## Usage

### Docker
To build a docker image, and then run the image:
```bash
$ sudo docker-compose up --build
``` 

After that, you can access the service website at [http://localhost:8000/](http://localhost:8000/)


### Training I3D

This branch provides an example of how to train a deep learning model with the completed labels from workers.
Thanks our workers (Annotator 1, 2, 20, 21, 22) to make this available.

* To extract flow features using PWC-Net (CVPR 2018), first a bash script need to be extracted.
```bash
$ python3 modeling/model.py
```
Then extract flow features,
```bash
$ cd thirdparty/pytorch-pwc && bash pwc.sh
```

* After flow features are extracted, you can start training I3D models using the labels from your workers:
```bash
# First sample some splits
$ ipython3
> from modeling.shoplift import *
> get_splits(n_splits=3, group_id=2, output_dir='.') # group_id is the index of the JobGroup object in Django DB
> quit
# Now you can train I3D
$ python3 modeling/i3d/train_i3d.py -mode rgb -save_model thirdparty/pytorch-i3d/models/rgb_shoplift.pt -split_file fold_1.json
```

In the above example, only labels of completed jobs (approved by project owners) at the training time are used to train the models.

A sample output:
```bash
...
[2019-02-01 17:44:10,155] utils: DEBUG - (0.000) SELECT "vatic_attributeannotation"."id", "vatic_attributeannotation"."path_id", "vatic_attributeannotation"."attribute_id", "vatic_attributeannotation"."frame", "vatic_attributeannotation"."value", "vatic_attributeannotation"."created_at", "vatic_attributeannotation"."updated_at" FROM "vatic_attributeannotation" WHERE "vatic_attributeannotation"."path_id" = 72; args=(72,)
[2019-02-01 17:44:10,155] utils: DEBUG - (0.000) SELECT "vatic_attributeannotation"."id", "vatic_attributeannotation"."path_id", "vatic_attributeannotation"."attribute_id", "vatic_attributeannotation"."frame", "vatic_attributeannotation"."value", "vatic_attributeannotation"."created_at", "vatic_attributeannotation"."updated_at" FROM "vatic_attributeannotation" WHERE "vatic_attributeannotation"."path_id" = 73; args=(73,)
[2019-02-01 17:44:10,156] utils: DEBUG - (0.000) SELECT "vatic_attributeannotation"."id", "vatic_attributeannotation"."path_id", "vatic_attributeannotation"."attribute_id", "vatic_attributeannotation"."frame", "vatic_attributeannotation"."value", "vatic_attributeannotation"."created_at", "vatic_attributeannotation"."updated_at" FROM "vatic_attributeannotation" WHERE "vatic_attributeannotation"."path_id" = 74; args=(74,)
[2019-02-01 17:44:10,156] utils: DEBUG - (0.000) SELECT "vatic_attributeannotation"."id", "vatic_attributeannotation"."path_id", "vatic_attributeannotation"."attribute_id", "vatic_attributeannotation"."frame", "vatic_attributeannotation"."value", "vatic_attributeannotation"."created_at", "vatic_attributeannotation"."updated_at" FROM "vatic_attributeannotation" WHERE "vatic_attributeannotation"."path_id" = 75; args=(75,)
0it [00:00, ?it/s]
Step 0/64000.0
----------
/home/tuananhn/.local/lib/python3.6/site-packages/torch/nn/functional.py:1749: UserWarning: Default upsampling behavior when mode=linear is changed to align_corners=False since 0.4.0. Please specify align_corners=True if the old behavior is desired. See the documentation of nn.Upsample for details.
  "See the documentation of nn.Upsample for details.".format(mode))
modeling/i3d/train_i3d.py:106: UserWarning: invalid index of a 0-dim tensor. This will be an error in PyTorch 0.5. Use tensor.item() to convert a 0-dim tensor to a Python number
  tot_loc_loss += loc_loss.data[0]
modeling/i3d/train_i3d.py:111: UserWarning: invalid index of a 0-dim tensor. This will be an error in PyTorch 0.5. Use tensor.item() to convert a 0-dim tensor to a Python number
  tot_cls_loss += cls_loss.data[0]
modeling/i3d/train_i3d.py:114: UserWarning: invalid index of a 0-dim tensor. This will be an error in PyTorch 0.5. Use tensor.item() to convert a 0-dim tensor to a Python number
  tot_loss += loss.data[0]
val Loc Loss: 0.2320 Cls Loss: 0.3641 Tot Loss: 0.2981
Step 5/64000.0
----------
train Loc Loss: 0.0522 Cls Loss: 0.0846 Tot Loss: 0.0684
val Loc Loss: 0.0691 Cls Loss: 0.1972 Tot Loss: 0.1332
Step 10/64000.0
----------
val Loc Loss: 0.0352 Cls Loss: 0.1869 Tot Loss: 0.1111
Step 15/64000.0
...
```
**Note**: Depends on how hard-working your workers are, the training can go well or overfit after several steps.