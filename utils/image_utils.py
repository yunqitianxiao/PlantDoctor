import cv2
import numpy as np
from PIL import Image
import io
from utils.logging_utils import handle_exceptions, log_info
 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
@handle_exceptions(default_return=(None, None, None, None, None))
def process_image_for_prediction(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Cannot decode image")
    return img
 
def calculate_severity(mask_np, original_shape):
    total_pixels = original_shape[0] * original_shape[1]
    lesion_pixels = np.sum(mask_np > 0)
    ratio = lesion_pixels / total_pixels if total_pixels > 0 else 0
    if ratio < 0.02:
        level = 'healthy'
    elif ratio < 0.10:
        level = 'mild'
    elif ratio < 0.30:
        level = 'moderate'
    else:
        level = 'severe'
    return ratio, level
 
def create_overlay_mask(original_img, mask_np, alpha=0.5):
    if mask_np is None or original_img is None:
        return original_img
    h, w = mask_np.shape[:2]
    if len(original_img.shape) == 3:
        color_mask = np.zeros_like(original_img)
        color_mask[mask_np > 0] = [0, 255, 0]
    else:
        color_mask = np.zeros((h, w, 3), dtype=np.uint8)
        color_mask[mask_np > 0] = [0, 255, 0]
    overlay = cv2.addWeighted(original_img, 1-alpha, color_mask, alpha, 0)
    return overlay
 
def resize_image(img, target_size=(384, 384)):
    return cv2.resize(img, target_size)
 
def image_to_base64(img):
    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()
