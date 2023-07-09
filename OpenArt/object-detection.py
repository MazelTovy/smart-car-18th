import os
import tf
from pyb import LED
from machine import UART
import utime
import seekfree
import math
import sensor, image, time

uart = UART(1, baudrate=115200) # 串口

day_brightness = 300
card_threshold = [(47, 100, -4, 68, -17, 29)]

def openart_init():
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_brightness(day_brightness)
    sensor.skip_frames(20)
    sensor.set_auto_gain(False)
    sensor.set_auto_whitebal(True, (0, 0, 0))

#图片矫正函数
def picture_correct():

    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QQVGA)
    sensor.set_brightness(day_brightness)
    sensor.skip_frames(20)
    sensor.set_auto_gain(False)
    sensor.set_auto_whitebal(False,(0,0,0))

    dis_X = 0
    dis_Y = 0
    distance = 0
    correct_flag = 1

    global uart_num

    while correct_flag:

        uart_num = uart.any()  # 鑾峰彇褰撳墠涓插彛鏁版嵁鏁伴噺
        img = sensor.snapshot()

        if(uart_num != 0):
            correct_flag = 0
            break
        else:
            for b in img.find_blobs(card_threshold, pixels_threshold=400, area_threshold=400, margin=1, merge=True, invert=0):
                #寻找角点
                corners = b.min_corners()
                point_corners = tuple(sorted(corners))
                for corner in corners:
                    img.draw_circle(corner[0], corner[1], 5, color=(0, 255, 0))
                x0, y0 = point_corners[3]
                x1, y1 = point_corners[2]
                x3, y3 = point_corners[0]

                len1 = (x0 - x1) ** 2 + (y0 - y1) ** 2
                len2 = (x1 - x3) ** 2 + (y1 - y3) ** 2

                if x1 == x0:
                    q = 0
                else:
                    q = math.atan((x1 - x0) / (y1 - y0))

                q = int(q * 60)


                img.draw_circle(b.cx(), b.cy(), 5, color=(0, 255, 0))
                dis_X = b.cx() - 91
                dis_Y = b.cy() - 70
                distance = math.sqrt((dis_X ** 2) + (dis_Y ** 2))
                print("disx:%d , disy:%d, angle:%d" % (dis_X, dis_Y, q))

                #发送数据
                uart.write("C")
                uart.write("%c" % dis_X)
                uart.write("%c" % dis_Y)
                if distance < 5:
                    uart.write("%c" % 1)
                else:
                    uart.write("%c" % 0)
                uart.write("D")
                img.draw_string(10,10,"correct", (255,0,0))
                lcd.show_image(img, 160, 120, zoom=0)

                if distance < 5:
                    correct_flag = 0


def object_detection(net, face_detect):
    detec_flag = 1

    while detec_flag:
        uart_num = uart.any()
        img = sensor.snapshot()

        if uart_num != 0:
            detec_flag = 0
            break

        closest_dis = float('inf')  # Initialize with a very large distance
        closest_obj = None

        # 使用模型进行识别
        for obj in tf.detect(net, img):
            x1, y1, x2, y2, label, scores = obj

            if scores > 0.50:
                w = x2 - x1
                h = y2 - y1
                x1 = int((x1 - 0.1) * img.width())
                y1 = int(y1 * img.height())
                w = int(w * img.width())
                h = int(h * img.height())
                center_x = x1 + w // 2
                center_y = y1 + h // 2

                dis_center_x = center_x - 160
                dis_center_y = center_y - 240

                if dis_center_x < -128:
                    dis_center_x = -128
                if dis_center_x > 128:
                    dis_center_x = 128

                if dis_center_y < -128:
                    dis_center_y = -128
                if dis_center_y > 128:
                    dis_center_y = 128

                max_distance_threshold = 150
                angle = -int(math.atan((center_x - 160) / (center_y - 240)) * 60)
                dis = int(math.sqrt(((center_x - 160) ** 2) + ((center_y - 240) ** 2)))

                if dis < closest_dis and dis < max_distance_threshold:
                    closest_dis = dis
                    closest_obj = obj

        if closest_obj is not None:
            x1, y1, x2, y2, label, scores = closest_obj
            w = x2 - x1
            h = y2 - y1
            x1 = int((x1 - 0.1) * img.width())
            y1 = int(y1 * img.height())
            img.draw_cross(x1, y1, size=5, color=(255, 0, 0))
            w = int(w * img.width())
            h = int(h * img.height())
            center_x = x1 + w // 2
            center_y = y1 + h // 2

            dis_center_x = center_x - 160
            dis_center_y = center_y - 240

            dis = int(math.sqrt(((center_x - 160) ** 2) + ((center_y - 240) ** 2)))

            if dis_center_x < -127:
                dis_center_x = -127
            if dis_center_x > 127:
                dis_center_x = 127

            if dis_center_y < -127:
                dis_center_y = -127
            if dis_center_y > 127:
                dis_center_y = 127

            img.draw_string(center_x, center_y, "Angle:" + str(angle), color=(255, 0, 0), scale=2, mono_space=False)
            img.draw_string(center_x, center_y - 30, "Dis:" + str(dis), color=(255, 0, 0), scale=2, mono_space=False)
            img.draw_cross(center_x, center_y, size=5, color=(255, 0, 0))
            img.draw_line(160, 240, center_x, center_y, color=(255, 0, 0))
            img.draw_rectangle((x1, y1, w, h), thickness=2)

            uart.write("C")
            uart.write("%c" % dis_center_x)
            uart.write("%c" % -dis_center_y)
            uart.write("%c" % 0)
            uart.write("D")
            print("dis:%d, angle:%d, center_x:%d, center_y:%d" % (dis, angle, center_x - 160, dis_center_y))
            if dis < 40:
                detec_flag = 0
                uart.write("C")
                uart.write("%c" % dis_center_x)
                uart.write("%c" % -dis_center_y)
                uart.write("%c" % 1)
                uart.write("D")
                break

def main():
    openart_init()

    face_detect = '/sd/yolo3_iou_smartcar_final_with_post_processing.tflite'
    net = tf.load(face_detect)

    while True:
        img = sensor.snapshot()
        #object_detection(net, face_detect)

        uart_num = uart.any()  # 鑾峰彇褰撳墠涓插彛鏁版嵁鏁伴噺
        if uart_num:
            uart_str = uart.read(uart_num).strip()  # 璇诲彇涓插彛鏁版嵁
            print(uart_str.decode())
            if uart_str.decode() == "F":
                print("F")
                uart_num = 0
                object_detection(net, face_detect)

if __name__ == '__main__':
    main()
