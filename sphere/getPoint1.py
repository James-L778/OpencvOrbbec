import cv2
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    ## 计算点云
    fx=576.535217
    fy=576.535217
    cx=318.794861
    cy=240.753784

    img_w = 640
    img_h = 480

    cir_x = 384
    cir_y = 302
    cir_c = 29

    depth = cv2.imread("./depth.png", cv2.CV_16UC1)

    np_x = np.array([])
    np_y = np.array([])
    np_z = np.array([])

    file = open("./test.txt", 'a')
    for i in range(img_w):
        for j in range(img_h):
            if pow(i - cir_x,2) + pow(j - cir_y,2) < pow(cir_c,2):
                z = depth[j,i]
                if z > 0 and z < 800:
                    x = (i - cx)*z/fx
                    y = (j - cy)*z/fy
                    str = "{},{},{}\r\n".format(x,y,z)
                    file.write(str)
                    c = 0

                    np_x = np.append(np_x, x)
                    np_y = np.append(np_y, y)
                    np_z = np.append(np_z, z)


    ax = plt.subplot(projection='3d')  # 创建一个三维的绘图工程
    ax.set_title('3d_image_show')  # 设置本图名称
    ax.scatter(np_x, np_y, np_z, c='r')  # 绘制数据点 c: 'r'红色，'y'黄色，等颜色

    ax.set_xlabel('X')  # 设置x坐标轴
    ax.set_ylabel('Y')  # 设置y坐标轴
    ax.set_zlabel('Z')  # 设置z坐标轴

    plt.show()
