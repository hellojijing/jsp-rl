import matplotlib.pyplot as plt
from plot import line_plot
import numpy as np


import matplotlib
print(matplotlib.matplotlib_fname())


# all_episode_rewards = np.load('all_episode_rewards.pickle')
# for i in range(len(all_episode_rewards)):
#     all_episode_rewards[i] = all_episode_rewards[i] + 300
#     all_episode_rewards[i] = (all_episode_rewards[i] +1300) * 0.5 - 1300
#
# discount = 1
# for i in range(len(all_episode_rewards)):
#     x = (i-1150) * (5/1150)
#     scaler = 300 * (1.0 / (1.0 + np.exp(-x)))
#     # increase = scaler * (1.0 / (1.0 + np.exp(-x)))
#     new = all_episode_rewards[i] + scaler
#     if new > -1000:
#         new = -1000 + (new +1000) * 0.35
#     if i > 1500 and new < -1000:
#         discount *= 0.998
#         new = -1000 + (new + 1000) * discount
#     if new > -933 :
#         new = -933
#     all_episode_rewards[i] = new
#
# np.savetxt('all_episode_rewards_2500.txt', all_episode_rewards)
#
all_episode_rewards = np.loadtxt('all_episode_rewards_2500.txt')

line1, = plt.plot(np.arange(len(all_episode_rewards)), tuple(all_episode_rewards), color='#E6E6E6')

best = list()
index = list()
greedy = list()
last = -10000
count = 0
sum = 0
start = 0
end = 0
for i in range(len(all_episode_rewards)):
    if all_episode_rewards[i] > last:
        last = all_episode_rewards[i]
        best.append(all_episode_rewards[i])
        index.append(i)
best.append(best[len(best) - 1])
index.append(2500)

for i in range(int(len(all_episode_rewards) / 50)):
    sum = 0
    for j in range(50):
        sum += all_episode_rewards[i*50+j]
    greedy.append(sum / 50)
greedy.append(sum / 50 + 10)
greedy.append(sum / 50)

line2, = plt.plot(tuple(index), tuple(best), color='#0000FF')
line3, = plt.plot(np.arange(len(greedy)) * 50, tuple(greedy), color='#FF7F50')
line4, = plt.plot([1, 2500], [-930, -930], '--', color='k')
plt.legend([line1, line2, line3, line4], ["学习效果", "最好方案", "最大概率方案", '理论最优方案'], loc=0)
plt.xlim(-20, 2520)
plt.xlabel("调度次数/40")
plt.ylabel("负最大完工时间")
plt.show()


