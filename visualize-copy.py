from plot import line_plot
import numpy as np
from constants import RESULT_DIR

# makespan = np.loadtxt('makespan.txt')
# complete_time = np.loadtxt('complete_time.txt')
all_episode_rewards = np.load('all_episode_rewards.pickle')
line_plot(np.arange(len(all_episode_rewards)), tuple(all_episode_rewards), "episode", "reward",
          "all_episode_rewards")

# line_plot(np.arange(len(makespan)), makespan, "episode", "makespan", "Makespan")
# for i in range(len(all_episode_rewards[1,:])):
    # line_plot(np.arange(len(all_episode_rewards)), all_episode_rewards[:, i], "episode", "reward", "rewards of machine 0")
    # line_plot(np.arange(len(makespan)), complete_time[:, i], "episode", "reward", "rewards of machine 0")
