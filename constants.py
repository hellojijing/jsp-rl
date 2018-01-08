# -*- coding: utf-8 -*-
from jsp_data import get_jobs_size
from jsp_data import get_machine_size

LOCAL_T_MAX = 20 # repeat step size
RMSP_ALPHA = 0.99 # decay parameter for RMSProp
RMSP_EPSILON = 0.1 # epsilon parameter for RMSProp
CHECKPOINT_DIR = 'checkpoints'
RESULT_DIR = '/home/peter/hfut/sourceCode/async_deep_reinforce/results'
LOG_FILE = 'tmp/a3c_log'
INITIAL_ALPHA_LOW = 1e-4    # log_uniform low limit for learning rate
INITIAL_ALPHA_HIGH = 1e-2   # log_uniform high limit for learning rate

PARALLEL_SIZE = 10 # parallel thread size
ROM = "pong.bin"     # action size = 3
ACTION_SIZE = get_jobs_size()+1 # action size  +1表示该机器没有处于等待状态的工序时，应该选择一个空闲action

INITIAL_ALPHA_LOG_RATE = 0.4226 # log_uniform interpolate rate for learning rate (around 7 * 10^-4)
GAMMA = 0.99 # discount factor for rewards
ENTROPY_BETA = 0.01 # entropy regurarlization constant
MAX_TIME_STEP = 10 * 10**7
GRAD_NORM_CLIP = 40.0 # gradient norm clipping
USE_GPU = True # To use GPU, set True
USE_LSTM = True # True for A3C LSTM, False for A3C FF

PROJECT_PATH = "/home/peter/hfut/sourceCode/async_deep_reinforce"  # 数据路径
MAX_TIME_EPISODE = 50
MACHINE_SIZE = get_machine_size()
