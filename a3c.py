# -*- coding: utf-8 -*-
import tensorflow as tf
import threading
import numpy as np


import signal
import random
import math
import os
import time
import pickle

from game_ac_network import GameACFFNetwork, GameACLSTMNetwork
from a3c_training_thread import A3CTrainingThread
from rmsprop_applier import RMSPropApplier

from constants import ACTION_SIZE
from constants import PARALLEL_SIZE
from constants import INITIAL_ALPHA_LOW
from constants import INITIAL_ALPHA_HIGH
from constants import INITIAL_ALPHA_LOG_RATE
from constants import MAX_TIME_STEP
from constants import CHECKPOINT_DIR
from constants import LOG_FILE
from constants import RMSP_EPSILON
from constants import RMSP_ALPHA
from constants import GRAD_NORM_CLIP
from constants import USE_GPU
from constants import USE_LSTM
from constants import MAX_TIME_EPISODE
from constants import MACHINE_SIZE
from constants import RECORD_REWARD_INTERVAL


from plot import line_plot
import global_var

os.environ["CUDA_VISIBLE_DEVICES"] = ""

def log_uniform(lo, hi, rate):
  log_lo = math.log(lo)
  log_hi = math.log(hi)
  v = log_lo * (1-rate) + log_hi * rate
  return math.exp(v)

device = "/cpu:0"
if USE_GPU:
  device = "/gpu:0"

initial_learning_rate = log_uniform(INITIAL_ALPHA_LOW,
                                    INITIAL_ALPHA_HIGH,
                                    INITIAL_ALPHA_LOG_RATE)
print('initial_learning_rate = %f' % initial_learning_rate)
global_t = 0

stop_requested = False

# if USE_LSTM:
#   global_network = GameACLSTMNetwork(ACTION_SIZE, -1, device)
# else:
#   global_network = GameACFFNetwork(ACTION_SIZE, -1, device)


training_threads = []

learning_rate_input = tf.placeholder("float")

grad_applier = RMSPropApplier(learning_rate = learning_rate_input,
                              decay = RMSP_ALPHA,
                              momentum = 0.0,
                              epsilon = RMSP_EPSILON,
                              clip_norm = GRAD_NORM_CLIP,
                              device = device)
# 设置同步mutex
mutex = threading.Lock()
#设置同步的condition
condition = threading.Condition()


# 设置共享变量，用来线程间通信，存放刚完成前一道工序的job，即用来通知后一道工序的机器来启动该工序为等待状态
arrived_jobs = list()
for i in range(MACHINE_SIZE):
    arrived_jobs.append(list())
terminal_count = [0]
for i in range(PARALLEL_SIZE):
  training_thread = A3CTrainingThread(i, initial_learning_rate,
                                      learning_rate_input,
                                      grad_applier, MAX_TIME_EPISODE,
                                      device = device, arrived_jobs = arrived_jobs, condition=condition)
  training_threads.append(training_thread)

# prepare session
sess = tf.Session(config=tf.ConfigProto(log_device_placement=False,
                                        allow_soft_placement=True))

init = tf.global_variables_initializer()
sess.run(init)

# summary for tensorboard
score_input = tf.placeholder(tf.int32)
tf.summary.scalar("score", score_input)

summary_op = tf.summary.merge_all()
summary_writer = tf.summary.FileWriter(LOG_FILE, sess.graph)

# init or load checkpoint with saver
saver = tf.train.Saver()
checkpoint = tf.train.get_checkpoint_state(CHECKPOINT_DIR)
if checkpoint and checkpoint.model_checkpoint_path:
  saver.restore(sess, checkpoint.model_checkpoint_path)
  print("checkpoint loaded:", checkpoint.model_checkpoint_path)
  tokens = checkpoint.model_checkpoint_path.split("-")
  # set global step
  global_t = int(tokens[1])
  print(">>> global step set: ", global_t)
  # set wall time
  wall_t_fname = CHECKPOINT_DIR + '/' + 'wall_t.' + str(global_t)
  with open(wall_t_fname, 'r') as f:
    wall_t = float(f.read())
else:
  print("Could not find old checkpoint")
  # set wall time
  wall_t = 0.0

all_episode_rewards = list()
try:
    with open('all_episode_rewards.pickle', 'rb') as f:
        all_episode_rewards = pickle.load(f)
except IOError:
    pass
print('all episode rewards = {}'.format(all_episode_rewards))
# with open('global_episode_time', 'rb') as f:
#     global_episode_time = pickle.load(f)
# print('global episode time = %d' % global_episode_time)

# complete_time = np.zeros([MAX_TIME_EPISODE, MACHINE_SIZE])
# all_episode_rewards = np.zeros([MAX_TIME_EPISODE, MACHINE_SIZE])
use_max_choice = False
def train_function(parallel_index):
  global global_t
  global use_max_choice
  training_thread = training_threads[parallel_index]
  # set start_time
  start_time = time.time() - wall_t
  training_thread.set_start_time(start_time)


  while True:
    if stop_requested:
      break
    # if global_t > MAX_TIME_STEP:
    #   break
    if global_t > MAX_TIME_EPISODE:
      break

    diff_global_t, episode_complete_time, episode_reward = training_thread.process(sess, global_t, summary_writer,
                                            summary_op, score_input, use_max_choice)


    if parallel_index == 0:
        if use_max_choice:
            all_episode_rewards.append(episode_reward)
        print("episode = %d, complete time = %d, reward = %d" % (global_t, episode_complete_time, episode_reward))

        if global_t % RECORD_REWARD_INTERVAL == 0:
            use_max_choice = True
        else:
            use_max_choice = False

        global_t += 1


    # complete_time[global_t][parallel_index] = episode_complete_time
    # all_episode_rewards[global_t][parallel_index] = episode_reward

    condition.acquire()
    terminal_count[0] += 1
    if terminal_count[0] == MACHINE_SIZE:
        terminal_count[0] = 0
        condition.notifyAll()
    else:
        condition.wait()
    if global_var.is_global_terminal is True:
        global_var.is_global_terminal = False
    condition.release()


    
    
def signal_handler(signal, frame):
  global stop_requested
  print('You pressed Ctrl+C!')
  stop_requested = True
  
train_threads = []
for i in range(PARALLEL_SIZE):
  train_threads.append(threading.Thread(target=train_function, args=(i,)))
  
signal.signal(signal.SIGINT, signal_handler)

# set start time
start_time = time.time() - wall_t

for t in train_threads:
  t.start()

print('Press Ctrl+C to stop')
signal.pause()

# makespan = complete_time.max(axis=1)
# print("complete time: /n={}".format(complete_time))
# print("complete time for each episode: /n={}".format(makespan))

line_plot(np.arange(len(all_episode_rewards)), tuple(all_episode_rewards), "episode", "reward", "all_episode_rewards")

# np.savetxt('makespan.txt', makespan)
# np.savetxt('complete_time.txt', complete_time)
# np.savetxt('all_episode_rewards.txt', all_episode_rewards)

print('Now saving data. Please wait')

with open('all_episode_rewards.pickle', 'wb') as f:
    f.truncate()
    pickle.dump(all_episode_rewards, f)

for t in train_threads:
  t.join()

if not os.path.exists(CHECKPOINT_DIR):
  os.mkdir(CHECKPOINT_DIR)

# write wall time
wall_t = time.time() - start_time
wall_t_fname = CHECKPOINT_DIR + '/' + 'wall_t.' + str(global_t)
with open(wall_t_fname, 'w') as f:
  f.write(str(wall_t))

saver.save(sess, CHECKPOINT_DIR + '/' + 'checkpoint', global_step = global_t)



