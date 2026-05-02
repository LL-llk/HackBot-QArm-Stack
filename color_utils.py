"""Shared color segmentation helpers for QArm Mini vision demos."""

import cv2
import numpy as np


COLOR_RANGES = {
    "red": [
        (np.array([0, 90, 60]), np.array([10, 255, 255])),
        (np.array([170, 90, 60]), np.array([180, 255, 255])),
    ],
    "green": [(np.array([35, 70, 50]), np.array([85, 255, 255]))],
    "blue": [(np.array([90, 70, 50]), np.array([130, 255, 255]))],
}

DRAW_COLORS = {
    "red": (0, 0, 255),
    "green": (0, 255, 0),
    "blue": (255, 0, 0),
}


def preprocess_mask(mask: np.ndarray) -> np.ndarray:
    """Smooth and clean a binary mask for contour detection."""
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return mask


def color_mask(hsv: np.ndarray, color: str) -> tuple[np.ndarray, tuple[int, int, int]]:
    """Return the binary mask and BGR draw color for a named target color."""
    if color not in COLOR_RANGES:
        raise ValueError(f"Unsupported color: {color}")

    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lower, upper in COLOR_RANGES[color]:
        mask |= cv2.inRange(hsv, lower, upper)
    return mask, DRAW_COLORS[color]


def find_largest_blob(mask: np.ndarray, min_area: float = 300):
    """Find the largest contour above min_area and return bbox/center/area."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_area = 0.0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        cx = x + w // 2
        cy = y + h // 2

        if area > best_area:
            best = (x, y, w, h, cx, cy, area)
            best_area = area

    return best

