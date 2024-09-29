import sys
import numpy as np
import cv2
import math
import math
from moviepy.editor import VideoFileClip
import os
from uuid import uuid4
from sqlmodel import Session
from ..models import MediaItem, MediaItemState
from ..helpers.db import engine
from ..helpers.storage import upload_file_to_storage
import tempfile
import requests

THRESHOLD_RATIO = 2000
MIN_AVG_RED = 60
MAX_HUE_SHIFT = 120
BLUE_MAGIC_VALUE = 1.2
SAMPLE_SECONDS = 2 # Extracts color correction from every N seconds

def hue_shift_red(mat, h):

    U = math.cos(h * math.pi / 180)
    W = math.sin(h * math.pi / 180)

    r = (0.299 + 0.701 * U + 0.168 * W) * mat[..., 0]
    g = (0.587 - 0.587 * U + 0.330 * W) * mat[..., 1]
    b = (0.114 - 0.114 * U - 0.497 * W) * mat[..., 2]

    return np.dstack([r, g, b])

def normalizing_interval(array):

    high = 255
    low = 0
    max_dist = 0

    for i in range(1, len(array)):
        dist = array[i] - array[i-1]
        if(dist > max_dist):
            max_dist = dist
            high = array[i]
            low = array[i-1]

    return (low, high)

def apply_filter(mat, filt):

    r = mat[..., 0]
    g = mat[..., 1]
    b = mat[..., 2]

    r = r * filt[0] + g*filt[1] + b*filt[2] + filt[4]*255
    g = g * filt[6] + filt[9] * 255
    b = b * filt[12] + filt[14] * 255

    filtered_mat = np.dstack([r, g, b])
    filtered_mat = np.clip(filtered_mat, 0, 255).astype(np.uint8)

    return filtered_mat

def get_filter_matrix(mat):

    mat = cv2.resize(mat, (256, 256))

    # Get average values of RGB
    avg_mat = np.array(cv2.mean(mat)[:3], dtype=np.uint8)
    
    # Find hue shift so that average red reaches MIN_AVG_RED
    new_avg_r = avg_mat[0]
    hue_shift = 0
    while(new_avg_r < MIN_AVG_RED):

        shifted = hue_shift_red(avg_mat, hue_shift)
        new_avg_r = np.sum(shifted)
        hue_shift += 1
        if hue_shift > MAX_HUE_SHIFT:
            new_avg_r = MIN_AVG_RED

    # Apply hue shift to whole image and replace red channel
    shifted_mat = hue_shift_red(mat, hue_shift)
    new_r_channel = np.sum(shifted_mat, axis=2)
    new_r_channel = np.clip(new_r_channel, 0, 255)
    mat[..., 0] = new_r_channel

    # Get histogram of all channels
    hist_r = hist = cv2.calcHist([mat], [0], None, [256], [0,256])
    hist_g = hist = cv2.calcHist([mat], [1], None, [256], [0,256])
    hist_b = hist = cv2.calcHist([mat], [2], None, [256], [0,256])

    normalize_mat = np.zeros((256, 3))
    threshold_level = (mat.shape[0]*mat.shape[1])/THRESHOLD_RATIO
    for x in range(256):
        
        if hist_r[x] < threshold_level:
            normalize_mat[x][0] = x

        if hist_g[x] < threshold_level:
            normalize_mat[x][1] = x

        if hist_b[x] < threshold_level:
            normalize_mat[x][2] = x

    normalize_mat[255][0] = 255
    normalize_mat[255][1] = 255
    normalize_mat[255][2] = 255

    adjust_r_low, adjust_r_high = normalizing_interval(normalize_mat[..., 0])
    adjust_g_low, adjust_g_high = normalizing_interval(normalize_mat[..., 1])
    adjust_b_low, adjust_b_high = normalizing_interval(normalize_mat[..., 2])


    shifted = hue_shift_red(np.array([1, 1, 1]), hue_shift)
    shifted_r, shifted_g, shifted_b = shifted[0][0]

    red_gain = 256 / (adjust_r_high - adjust_r_low)
    green_gain = 256 / (adjust_g_high - adjust_g_low)
    blue_gain = 256 / (adjust_b_high - adjust_b_low)

    redOffset = (-adjust_r_low / 256) * red_gain
    greenOffset = (-adjust_g_low / 256) * green_gain
    blueOffset = (-adjust_b_low / 256) * blue_gain

    adjust_red = shifted_r * red_gain
    adjust_red_green = shifted_g * red_gain
    adjust_red_blue = shifted_b * red_gain * BLUE_MAGIC_VALUE

    return np.array([
        adjust_red, adjust_red_green, adjust_red_blue, 0, redOffset,
        0, green_gain, 0, 0, greenOffset,
        0, 0, blue_gain, 0, blueOffset,
        0, 0, 0, 1, 0,
    ])

def correct(mat):
    original_mat = mat.copy()

    filter_matrix = get_filter_matrix(mat)
    
    corrected_mat = apply_filter(original_mat, filter_matrix)
    corrected_mat = cv2.cvtColor(corrected_mat, cv2.COLOR_RGB2BGR)

    return corrected_mat

def process_image(input_image_path, output_image_path):
    mat = cv2.imread(input_image_path)
    mat = cv2.cvtColor(mat, cv2.COLOR_BGR2RGB)
    
    corrected_mat = correct(mat)

    cv2.imwrite(output_image_path, corrected_mat)

def analyze_video(input_video_path, output_video_path):
    
    # Initialize new video writer
    cap = cv2.VideoCapture(input_video_path)
    fps = math.ceil(cap.get(cv2.CAP_PROP_FPS))
    frame_count = math.ceil(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Get filter matrices for every 10th frame
    filter_matrix_indexes = []
    filter_matrices = []
    count = 0
    
    print("Analyzing...")
    while(cap.isOpened()):
        
        count += 1  
        # print(f"{count} frames", end="\r")
        ret, frame = cap.read()
        if not ret:
            # End video read if we have gone beyond reported frame count
            if count >= frame_count:
                break

            # Failsafe to prevent an infinite loop
            if count >= 1e6:
                break

            # Otherwise this is just a faulty frame read, try reading next frame
            continue

        # Pick filter matrix from every N seconds
        if count % (fps * SAMPLE_SECONDS) == 0:
            mat = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            filter_matrix_indexes.append(count) 
            filter_matrices.append(get_filter_matrix(mat))

    cap.release()

    # Build a interpolation function to get filter matrix at any given frame
    filter_matrices = np.array(filter_matrices)

    return {
        "input_video_path": input_video_path,
        "output_video_path": output_video_path,
        "fps": fps,
        "frame_count": count,
        "filters": filter_matrices,
        "filter_indices": filter_matrix_indexes
    }

def process_video_internal(video_data):
    cap = cv2.VideoCapture(video_data["input_video_path"])

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Change the codec to H.264
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    corrected_without_audio_output_path = f"/tmp/{uuid4()}.mp4"
    new_video = cv2.VideoWriter(corrected_without_audio_output_path, fourcc, video_data["fps"], (frame_width, frame_height))      

    filter_matrices = video_data["filters"]
    filter_indices = video_data["filter_indices"]

    filter_matrix_size = len(filter_matrices[0])
    def get_interpolated_filter_matrix(frame_number):
        return [np.interp(frame_number, filter_indices, filter_matrices[..., x]) for x in range(filter_matrix_size)]

    print("Processing...")

    frame_count = video_data["frame_count"]

    count = 0
    while cap.isOpened():
        count += 1  
        percent = 100*count/frame_count
        # print("{:.2f}".format(percent), end=" % \r")
        ret, frame = cap.read()
        
        if not ret:
            if count >= frame_count or count >= 1e6:
                break
            continue

        rgb_mat = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        interpolated_filter_matrix = get_interpolated_filter_matrix(count)
        corrected_mat = apply_filter(rgb_mat, interpolated_filter_matrix)
        corrected_mat = cv2.cvtColor(corrected_mat, cv2.COLOR_RGB2BGR)

        new_video.write(corrected_mat) 

    cap.release()
    new_video.release()

    # Combine processed video with original audio
    print("Combining video and audio...")
    
    original_clip = VideoFileClip(video_data["input_video_path"])
    corrected_without_audio_clip = VideoFileClip(corrected_without_audio_output_path)
    final_clip = corrected_without_audio_clip.set_audio(original_clip.audio)
    final_clip.write_videofile(video_data["output_video_path"], codec="libx264", audio_codec="aac")

    final_clip.close()
    corrected_without_audio_clip.close()
    original_clip.close()

    # Clean up temporary file
    os.unlink(corrected_without_audio_output_path)

    print("Processing complete.")

def process_video(input_video_path, output_video_path):

    video_data = analyze_video(input_video_path, output_video_path)
    process_video_internal(video_data)


def color_correct_media(media_item_id: int):
    with Session(engine) as session:
        media_item = session.get(MediaItem, media_item_id)
        if not media_item:
            return

        # Download the file
        response = requests.get(media_item.raw_url)
        if response.status_code != 200:
            print(f"Failed to download file for media item {media_item_id}")
            return

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # Process the file
        if media_item.mime_type.startswith('image/'):
            output_file_path = f"/tmp/{uuid4()}.png"
            process_image(temp_file_path, output_file_path)

        elif media_item.mime_type.startswith('video/'):
            output_file_path = f"/tmp/{uuid4()}.mp4"
            process_video(temp_file_path, output_file_path)
        else:
            print(f"Unsupported media type for item {media_item_id}")
            os.unlink(temp_file_path)
            return

        # Upload the processed file
        file_extension = os.path.splitext(media_item.filename)[1] if media_item.filename else ''
        def get_raw_url_uuid():
            filename = media_item.raw_url.split("/")[-1]
            raw_uuid = filename[:filename.find("_")]
            return raw_uuid
            
        processed_key = f"user-{media_item.user_id}/{get_raw_url_uuid()}_processed{file_extension}"
        
        with open(output_file_path, 'rb') as processed_file:
            upload_file_to_storage(processed_file, processed_key)

        # Update the media_item with the new processed_url
        bucket_name = os.getenv("STORAGE_BUCKET")
        storage_endpoint = os.getenv('STORAGE_ENDPOINT_URL')
        processed_url = f"{storage_endpoint}/{bucket_name}/{processed_key}"
        
        media_item.processed_url = processed_url
        media_item.state = MediaItemState.READY
        session.commit()

        # Clean up temporary files
        os.unlink(temp_file_path)
        os.unlink(output_file_path)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage")
        print("-"*20)
        print("For image:")
        print("$python correct.py image <source_image_path> <output_image_path>\n")
        print("-"*20)
        print("For video:")
        print("$python correct.py video <source_video_path> <output_video_path>\n")
        exit(0)

    if (sys.argv[1]) == "image":
        process_image(sys.argv[2], sys.argv[3])
    
    else:
        process_video(sys.argv[2], sys.argv[3])
        