# Single Color RGB565 Blob Tracking Example
#
# This example from OpenMV was altered to try and track different objects
# It takes the largest "blob" it finds and for skystones can give an estimate of 1ft distance
#   based on the average values of 10 cycles as well as predict the true distance

import sensor, image, time, math

threshold_index = 4 # 0 for red, 1 for green, 2 for blue, 3 for cube, 4 for skystone, 5 for cone, 6 for sarah

# Color Tracking Thresholds (L Min, L Max, A Min, A Max, B Min, B Max)
# The below thresholds track in general red/green/blue things. You may wish to tune them...
thresholds = [(30, 100, 15, 127, 15, 127), # generic_red_thresholds
              (30, 100, -64, -8, -32, 32), # generic_green_thresholds
              (0, 30, 0, 64, -128, 0), (52, 36, 6, 41, 127, 34), (60, 35, 8, 67, 82, 38), (0, 80, -5, 25, 35, 79), (6, 71, 5, 32, 7, 30)] # generic_blue_thresholds

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False) # must be turned off for color tracking
sensor.set_auto_whitebal(False) # must be turned off for color tracking
clock = time.clock()

# Only blobs that with more pixels than "pixel_threshold" and more area than "area_threshold" are
# returned by "find_blobs" below. Change "pixels_threshold" and "area_threshold" if you change the
# camera resolution. "merge=True" merges all overlapping blobs in the image.

count = 0 #used for filtering out noise
one_foot_count = 0
close_count = 0
far_count = 0
uncentered_count = 0
width_avg = 0
px_to_in = 12/174

while(True):
    clock.tick()
    img = sensor.snapshot()
    blob_list = img.find_blobs([thresholds[threshold_index]], pixels_threshold = 200, area_threshold = 200, merge = True)
    biggest_blob = None
    for blob in blob_list:
        if biggest_blob != None:
            biggest_width = biggest_blob.min_corners()[0][0] - biggest_blob.min_corners()[2][0]
            biggest_height = biggest_blob.min_corners()[0][1] - biggest_blob.min_corners()[2][1]
            width = blob.min_corners()[0][0] - blob.min_corners()[2][0]
            height = blob.min_corners()[0][1] - blob.min_corners()[2][1]
            if width * height > biggest_width * biggest_height:
               biggest_blob = blob
        else:
            biggest_blob = blob
    big_list = []
    if biggest_blob != None:
        big_list.append(biggest_blob)
    else:
        continue
    for blob in big_list: #should just have one blob b/c it's a list of the largest blob (singular)
        # These values depend on the blob not being circular - otherwise they will be shaky.
        if blob.elongation() > 0.5:
            img.draw_edges(blob.min_corners(), color=(255,0,0))
            img.draw_line(blob.major_axis_line(), color=(0,255,0))
            img.draw_line(blob.minor_axis_line(), color=(0,0,255))
            x_avg = (blob.min_corners()[2][0] + blob.min_corners()[0][0]) / 2
            y_avg = (blob.min_corners()[2][1] + blob.min_corners()[0][1]) / 2
            width = blob.min_corners()[2][0] - blob.min_corners()[0][0]
            height = blob.min_corners()[2][1] - blob.min_corners()[0][1]
            width_avg += width
            ss_pix_width = 0 #skystone pixel width at 1ft distance
            ss_pix_height = 0 #skystone pixel height at 1ft distance
            #IMPROVEMENT: Make this so that it only considers the biggest blob (our target)
            if x_avg >= 130 and x_avg <= 190 and y_avg >= 90 and y_avg <= 170:
                #print('wow ur centered')
                if width in range(150, 190) and height in range(75, 115):
                    one_foot_count += 1
                    #print('about 1 ft away')
                elif width > 180 or height > 105:
                    close_count += 1
                    #print('personal space pls')
                else:
                    far_count += 1
                    #print('too far')

            else:
                #print('uncoordinated')
                uncentered_count += 1

            if count == 10:
                total_count = one_foot_count + close_count + far_count + uncentered_count
                print(close_count, far_count, one_foot_count, uncentered_count, total_count)
                if one_foot_count / total_count >= 0.6:
                    print('about 1 ft away')
                    print(width)
                elif close_count / total_count >= 0.6:
                    print('personal space pls')
                    print('Estimate:', str(((174 - abs(width)) * px_to_in) + 12) + 'in')
                elif far_count / total_count >= 0.6:
                    print('too far')
                    print('Estimate:', str(((174 - abs(width)) * px_to_in) + 12) + 'in')
                else:
                    print('inconclusive')
                one_foot_count = 0
                close_count = 0
                far_count = 0
                uncentered_count = 0
                count = 0
                width_avg /= 10
                #print('Width:', width_avg)
                width_avg = 0

            count += 1
            #print(count)


            #TODO: find the distance based on how large the box appears (proportional) - DONE
            #based on size of box, align:
            #box must be centered horizontally/vertically (calibrate to position on bot later)
            #distance: based on how far, generate velocity profile (horizontal and vertical components separately)
            #skystone is 8in x 4in
            #width at 1ft is approx 174 px


        # These values are stable all the time.
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        # Note - the blob rotation is unique to 0-180 only.
        img.draw_keypoints([(blob.cx(), blob.cy(), int(math.degrees(blob.rotation())))], size=20)
    #print(clock.fps())
