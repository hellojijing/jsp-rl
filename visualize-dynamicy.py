import scipy.io
import matplotlib.pyplot as plt
import numpy as np


all_data = np.loadtxt('learningCurve_optimized.txt')

line1, = plt.plot(np.arange(len(all_data[4,:])), all_data[4,:], color='#D3D3D3')
line2, = plt.plot(np.arange(len(all_data[5,:])), all_data[5,:], color='#D3D3D3')
line3, = plt.plot(np.arange(len(all_data[6,:])), all_data[6,:], color='#D3D3D3')
line4, = plt.plot(np.arange(len(all_data[2,:])), all_data[2,:], color='blue')
line5, = plt.plot(np.arange(len(all_data[3,:])), all_data[3,:], color='#FF8254')


plt.legend([line1, line2, line3, line4, line5], ['FIFO','LPT', 'SPT', '学习(非延迟)', '学习（延迟）'])

plt.xlabel("调度次数/40")
plt.ylabel("负最大完工时间")
plt.show()

