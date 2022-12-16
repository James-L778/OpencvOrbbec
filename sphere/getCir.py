import numpy as np

def sphere_surface(points):
    num_points = points.shape[0]
    # print(num_points)
    x, y, z = points[:, 0], points[:, 1], points[:, 2]

    x_avr, y_avr, z_avr = sum(x) / num_points, sum(y) / num_points, sum(z) / num_points
    xx_avr, yy_avr, zz_avr = sum(x * x) / num_points, sum(y * y) / num_points, sum(z * z) / num_points
    xy_avr, xz_avr, yz_avr = sum(x * y) / num_points, sum(x * z) / num_points, sum(y * z) / num_points

    xxx_avr = sum(x * x * x) / num_points
    xxy_avr = sum(x * x * y) / num_points
    xxz_avr = sum(x * x * z) / num_points
    xyy_avr = sum(x * y * y) / num_points
    xzz_avr = sum(x * z * z) / num_points
    yyy_avr = sum(y * y * y) / num_points
    yyz_avr = sum(y * y * z) / num_points
    yzz_avr = sum(y * z * z) / num_points
    zzz_avr = sum(z * z * z) / num_points

    A = np.array([[xx_avr - x_avr * x_avr, xy_avr - x_avr * y_avr, xz_avr - x_avr * z_avr],
                  [xy_avr - x_avr * y_avr, yy_avr - y_avr * y_avr, yz_avr - y_avr * z_avr],
                  [xz_avr - x_avr * z_avr, yz_avr - y_avr * z_avr, zz_avr - z_avr * z_avr]])
    b = np.array([xxx_avr - x_avr * xx_avr + xyy_avr - x_avr * yy_avr + xzz_avr - x_avr * zz_avr,
                  xxy_avr - y_avr * xx_avr + yyy_avr - y_avr * yy_avr + yzz_avr - y_avr * zz_avr,
                  xxz_avr - z_avr * xx_avr + yyz_avr - z_avr * yy_avr + zzz_avr - z_avr * zz_avr])
    b = b / 2
    center = np.linalg.solve(A, b)
    x0, y0, z0 = center[0], center[1], center[2]
    r2 = xx_avr - 2 * x0 * x_avr + x0 * x0 + yy_avr - 2 * y0 * y_avr + y0 * y0 + zz_avr - 2 * z0 * z_avr + z0 * z0
    r = r2 ** 0.5
    return center[0], center[1], center[2], r * 2


# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
    path = './test.txt'  # 点云数据存储地址
    points = np.loadtxt(path,
                 delimiter=",", dtype=float)
# points = np.array(cloud, dtype='float64')  # cloud为点云坐标的列表
sphere_surface(points)  # 球心拟合算法
print("拟合球心坐标及直径如下：")
print(sphere_surface(points))
