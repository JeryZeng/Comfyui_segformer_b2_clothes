import os

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from transformers import SegformerImageProcessor, AutoModelForSemanticSegmentation

import folder_paths

processor = None
model = None


def load_model():
    global model
    global processor
    if model is not None:
        return
    model_folder_paths = folder_paths.get_folder_paths('segformer_b2_clothes')
    for path in model_folder_paths:
        if not os.path.exists(path):
            continue
        processor = SegformerImageProcessor.from_pretrained(path)
        model = AutoModelForSemanticSegmentation.from_pretrained(path)
        return
    raise Exception("model not found in paths")


def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


# Convert PIL to Tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


# 切割服装
def get_segmentation(tensor_image):
    load_model()
    cloth = tensor2pil(tensor_image)
    # 预处理和预测
    inputs = processor(images=cloth, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits.cpu()
    upsampled_logits = nn.functional.interpolate(logits, size=cloth.size[::-1], mode="bilinear", align_corners=False)
    pred_seg = upsampled_logits.argmax(dim=1)[0].numpy()
    return pred_seg, cloth


class segformer_b2_clothes:

    def __init__(self):
        pass

    # Labels: 0: "Background", 1: "Hat", 2: "Hair", 3: "Sunglasses", 4: "Upper-clothes", 5: "Skirt", 6: "Pants", 7: "Dress", 8: "Belt", 9: "Left-shoe", 10: "Right-shoe", 11: "Face", 12: "Left-leg", 13: "Right-leg", 14: "Left-arm", 15: "Right-arm", 16: "Bag", 17: "Scarf"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required":
            {
                "image": ("IMAGE", {"default": "", "multiline": False}),
                "Face": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Hat": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Hair": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Upper_clothes": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Skirt": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Pants": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Dress": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Belt": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "shoe": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "leg": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "arm": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Bag": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
                "Scarf": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("mask_image",)
    OUTPUT_NODE = True
    FUNCTION = "sample"
    CATEGORY = "CXH"

    def sample(self, image, Face, Hat, Hair, Upper_clothes, Skirt, Pants, Dress, Belt, shoe, leg, arm, Bag, Scarf):

        results = []
        for item in image:

            # seg切割结果，衣服pil
            pred_seg, cloth = get_segmentation(item)
            labels_to_keep = [0]
            # if background :
            #     labels_to_keep.append(0)
            if not Hat:
                labels_to_keep.append(1)
            if not Hair:
                labels_to_keep.append(2)
            if not Upper_clothes:
                labels_to_keep.append(4)
            if not Skirt:
                labels_to_keep.append(5)
            if not Pants:
                labels_to_keep.append(6)
            if not Dress:
                labels_to_keep.append(7)
            if not Belt:
                labels_to_keep.append(8)
            if not shoe:
                labels_to_keep.append(9)
                labels_to_keep.append(10)
            if not Face:
                labels_to_keep.append(11)
            if not leg:
                labels_to_keep.append(12)
                labels_to_keep.append(13)
            if not arm:
                labels_to_keep.append(14)
                labels_to_keep.append(15)
            if not Bag:
                labels_to_keep.append(16)
            if not Scarf:
                labels_to_keep.append(17)

            mask = np.isin(pred_seg, labels_to_keep).astype(np.uint8)

            # 创建agnostic-mask图像
            mask_image = Image.fromarray(mask * 255)
            mask_image = mask_image.convert("RGB")
            mask_image = pil2tensor(mask_image)
            results.append(mask_image)

        return (torch.cat(results, dim=0),)
