import cv2
import numpy as np
import random

COVER_SIZE = 512
PHOTO_SIZE = 300
BORDER = 14


def load_small(path):
    img = cv2.imread(str(path), cv2.IMREAD_REDUCED_COLOR_4)
    return img


def add_border(img):

    return cv2.copyMakeBorder(
        img,
        BORDER,
        BORDER,
        BORDER,
        BORDER,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255)
    )


def rotate(img, angle):

    h, w = img.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    return cv2.warpAffine(
        img,
        M,
        (w, h),
        borderMode=cv2.BORDER_TRANSPARENT
    )


def add_shadow(canvas, x, y, w, h):

    shadow = canvas.copy()

    cv2.rectangle(
        shadow,
        (x+8, y+8),
        (x+w+8, y+h+8),
        (0,0,0),
        -1
    )

    alpha = 0.25

    cv2.addWeighted(shadow, alpha, canvas, 1-alpha, 0, canvas)


def paste(canvas, img, x, y):

    h, w = img.shape[:2]

    sub = canvas[y:y+h, x:x+w]

    mask = img.sum(axis=2) > 0

    sub[mask] = img[mask]


def prepare_image(path):

    img = load_small(path)

    if img is None:
        return None

    img = cv2.resize(img, (PHOTO_SIZE, PHOTO_SIZE))

    img = add_border(img)

    angle = random.uniform(-20, 20)

    img = rotate(img, angle)

    return img


def create_collage(paths):

    canvas = np.zeros((COVER_SIZE, COVER_SIZE, 3), dtype=np.uint8)

    imgs = []

    for p in paths:
        img = prepare_image(p)
        if img is not None:
            imgs.append(img)

    if len(imgs) < 3:
        return None

    positions = [
        (random.randint(40,80), random.randint(40,80)),
        (random.randint(150,200), random.randint(90,140)),
        (random.randint(90,140), random.randint(200,240))
    ]

    for img,(x,y) in zip(imgs,positions):

        h,w = img.shape[:2]

        add_shadow(canvas,x,y,w,h)
        paste(canvas,img,x,y)

    return canvas
