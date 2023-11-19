import os

import pandas as pd
import cv2
import numpy as np


def add_transparent_image(background, foreground, x_offset=None, y_offset=None):
    bg_h, bg_w, bg_channels = background.shape
    fg_h, fg_w, fg_channels = foreground.shape

    assert bg_channels == 3, f'background image should have exactly 3 channels (RGB). found:{bg_channels}'
    assert fg_channels == 4, f'foreground image should have exactly 4 channels (RGBA). found:{fg_channels}'

    # center by default
    if x_offset is None:
        x_offset = (bg_w - fg_w) // 2
    if y_offset is None:
        y_offset = (bg_h - fg_h) // 2

    w = min(fg_w, bg_w, fg_w + x_offset, bg_w - x_offset)
    h = min(fg_h, bg_h, fg_h + y_offset, bg_h - y_offset)

    if w < 1 or h < 1:
        return

    # clip foreground and background images to the overlapping regions
    bg_x = max(0, x_offset)
    bg_y = max(0, y_offset)
    fg_x = max(0, x_offset * -1)
    fg_y = max(0, y_offset * -1)
    foreground = foreground[fg_y:fg_y + h, fg_x:fg_x + w]
    background_subsection = background[bg_y:bg_y + h, bg_x:bg_x + w]

    # separate alpha and color channels from the foreground image
    foreground_colors = foreground[:, :, :3]
    alpha_channel = foreground[:, :, 3] / 255  # 0-255 => 0.0-1.0

    # construct an alpha_mask that matches the image shape
    alpha_mask = np.dstack((alpha_channel, alpha_channel, alpha_channel))

    # combine the background with the overlay image weighted by alpha
    composite = background_subsection * (1 - alpha_mask) + foreground_colors * alpha_mask

    # overwrite the section of the background image that has been updated
    background[bg_y:bg_y + h, bg_x:bg_x + w] = composite


frame = np.ones((960, 1440, 3), dtype=np.uint8) * 128

frames_dir = './amazon-kinesis-video-streams-consumer-library-for-python/frames'
detections_dir = './amazon-kinesis-video-streams-consumer-library-for-python/detections'
processed_fragments_dir = './amazon-kinesis-video-streams-consumer-library-for-python/processed_fragments'
license_plates_dir = './amazon-kinesis-video-streams-consumer-library-for-python/license_plates'

visualized_fragments = []

car_imgs_ = {}
track_ids_ = []

while True:

    for j in range(2):
        for file in sorted(os.listdir('./loading_frames')):
            img = cv2.imread('./loading_frames/' + file, cv2.IMREAD_UNCHANGED)
            add_transparent_image(frame, img)
            cv2.imshow('frame', frame)
            cv2.waitKey(25)

    # get fragments of data local
    frames = sorted(os.listdir(frames_dir),
                    key=lambda x: os.path.getmtime(os.path.join(frames_dir, x)))

    fragments = sorted(set([l.split('-')[0] for l in frames])) # fragment_number-frame_number.jpg

    # get fragments of data object detection
    fragments_object_detection = sorted(os.listdir(processed_fragments_dir),
                    key=lambda x: os.path.getmtime(os.path.join(processed_fragments_dir, x)))

    # iterate frames of matching fragments
    for fragment in fragments:
        if fragment not in visualized_fragments and fragment in fragments_object_detection:
            visualized_fragments.append(fragment)

            # draw bounding boxes

            data = pd.read_csv(os.path.join(detections_dir, '{}.csv'.format(fragment)))

            for frame_path in [f for f in frames if fragment in f]:
                frame = cv2.imread(os.path.join(frames_dir, frame_path))
                frame_ = frame.copy()

                frame_number = int(frame_path[:-4].split('-')[1])

                detections = data[data['frame_number'] == frame_number]

                for k in range(len(detections)):
                    det = detections.iloc[k]
                    x1, y1, x2, y2 = det['x1'], det['y1'], det['x2'], det['y2']
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 5)

                    x1car, y1car, x2car, y2car = det['x1car'], det['y1car'], det['x2car'], det['y2car']
                    if int(x1car) != -1:
                        if int(det['track_id']) not in car_imgs_.keys():
                            car_imgs_[int(det['track_id'])] = frame_[int(y1car):int(y2car), int(x1car):int(x2car), :]
                        cv2.rectangle(frame, (int(x1car), int(y1car)), (int(x2car), int(y2car)), (0, 255, 0), 5)

                    if int(det['track_id'] not in track_ids_):
                        track_ids_.append(det['track_id'])

                license_plates_track_ids = [int(l.split('_')[0]) for l in os.listdir(license_plates_dir)]
                license_plates_text = [l.split('_')[1] for l in os.listdir(license_plates_dir)]

                # draw license plate number
                for j in range(len(track_ids_)):
                    if track_ids_[- 1 - j] in license_plates_track_ids:
                        frame[50:250, 150:350, :] = [255, 255, 255]
                        frame[50:250, 375:1290, :] = [255, 255, 255]

                        frame[55:245, 155:345, :] = cv2.resize(car_imgs_[track_ids_[- 1 - j]], (190, 190))
                        cv2.putText(frame,
                                    license_plates_text[license_plates_track_ids.index(track_ids_[- 1 - j])],
                                    (400, 215),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    6,
                                    (0, 0, 0),
                                    13
                                    )

                        break

                cv2.imshow('frame', frame)
                cv2.waitKey(25)

                os.remove(os.path.join(frames_dir, frame_path))

        else:
            continue

