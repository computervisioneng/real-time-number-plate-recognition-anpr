import os
import time

import cv2
import numpy as np
import pandas as pd


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

cars = {}

fragment_number_index_ = -1
frame = np.ones((960, 1440, 3), dtype=np.uint8) * 128
fragment_number_index = 0

frames_dir = './amazon-kinesis-video-streams-consumer-library-for-python/frames/'
detections_dir = './amazon-kinesis-video-streams-consumer-library-for-python/detections/'
processed_fragments_dir = './amazon-kinesis-video-streams-consumer-library-for-python/processed_fragments/'
license_plates_dir = './amazon-kinesis-video-streams-consumer-library-for-python/license_plates/'

track_ids_ = []
car_imgs_ = {}

while True:

    frames_ = sorted(os.listdir(frames_dir),
                                    key=lambda x: os.path.getmtime(os.path.join(frames_dir, x)))

    fragments_ = sorted(set([l.split('-')[0] for l in frames_]))

    if len(frames_) == 0:
        for j in range(2):
            for file in sorted(os.listdir('./loading_frames')):
                img = cv2.imread('./loading_frames/' + file, cv2.IMREAD_UNCHANGED)
                add_transparent_image(frame, img)
                cv2.imshow('frame', frame)
                cv2.waitKey(40)

    for fragment_ in fragments_:
        while fragment_ not in [j for j in os.listdir(processed_fragments_dir)]:
            for j in range(2):
                for file in sorted(os.listdir('./loading_frames')):
                    img = cv2.imread('./loading_frames/' + file, cv2.IMREAD_UNCHANGED)
                    add_transparent_image(frame, img)
                    cv2.imshow('frame', frame)
                    cv2.waitKey(40)

        data = pd.read_csv(os.path.join(detections_dir, '{}.csv'.format(fragment_)))
        for file_index, file in enumerate([filename for filename in sorted(os.listdir(frames_dir),
                                                                           key=lambda x: os.path.getmtime(
                                                                               os.path.join(frames_dir, x))) if
                                                                                                fragment_ in filename]):

            frame = cv2.imread(frames_dir + file)
            frame_ = frame.copy()

            frame_number_ = file[:-4].split('-')[1]

            # detections_car = data[(data['frame_number'] == int(frame_number_)) & (data['class_id'] == 1)]
            detections_lc = data[(data['frame_number'] == int(frame_number_)) & (data['class_id'] == 0)]
            for k in range(len(detections_lc)):
                det = detections_lc.iloc[k]
                x1, y1, x2, y2 = det['x1'], det['y1'], det['x2'], det['y2']
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 5)

                x1car, y1car, x2car, y2car = det['x1car'], det['y1car'], det['x2car'], det['y2car']

                if int(x1car) != -1:
                    if int(det['track_id']) not in car_imgs_.keys():
                        car_imgs_[int(det['track_id'])] = frame_[int(y1car):int(y2car), int(x1car):int(x2car), :]
                    cv2.rectangle(frame, (int(x1car), int(y1car)), (int(x2car), int(y2car)), (0, 255, 0), 5)

                if int(det['track_id']) not in track_ids_:
                    track_ids_.append(int(det['track_id']))

            license_plates_tracks_ = [int(j.split('_')[0]) for j in sorted(os.listdir(license_plates_dir))]
            license_plates_texts_ = [j.split('_')[1] for j in sorted(os.listdir(license_plates_dir))]

            for j in range(len(track_ids_)):
                if track_ids_[- 1 - j] in license_plates_tracks_:
                    # frame[50:250, 150:1290, :] = [255, 255, 255]
                    frame[50:250, 150:350, :] = [255, 255, 255]
                    frame[50:250, 375:1290, :] = [255, 255, 255]

                    frame[55:245, 155:345, :] = cv2.resize(car_imgs_[track_ids_[- 1 - j]], (190, 190))
                    # cv2.putText(frame, license_plates_texts_[license_plates_tracks_.index(track_ids_[- 1 - j])],
                    #             (55, 255), cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 0, 0), 5, lineType=cv2.LINE_AA)

                    cv2.putText(frame, license_plates_texts_[license_plates_tracks_.index(track_ids_[- 1 - j])],
                                (400, 215), cv2.FONT_HERSHEY_SIMPLEX, 6, (0, 0, 0), 13, lineType=cv2.LINE_AA)

                    break

            cv2.imshow('frame', frame)
            cv2.waitKey(25)

            os.remove(frames_dir + file)
