# -*- coding: utf-8 -*-
import tensorflow as tf
import numpy as np
import random
import time
import sys

# from game_state import GameState
# from game_state import ACTION_SIZE
from constants import ACTION_SIZE
from game_ac_network import GameACFFNetwork, GameACLSTMNetwork

from constants import GAMMA
from constants import LOCAL_T_MAX
from constants import ENTROPY_BETA
from constants import USE_LSTM

from jsp_data import get_data_by_machine
from jsp_env import JspEnv

LOG_INTERVAL = 100
PERFORMANCE_LOG_INTERVAL = 1000

class A3CTrainingThread(object):
  def __init__(self,
               thread_index,
               initial_learning_rate,
               learning_rate_input,
               grad_applier,
               max_global_time_episode,
               device, arrived_jobs, condition):

    self.thread_index = thread_index
    self.learning_rate_input = learning_rate_input
    self.max_global_time_episode = max_global_time_episode

    # 通过thread_index 即机器编号来获取在该机器上加工的所有工序
    self.operations = get_data_by_machine(thread_index)
    self.condition = condition
    self.is_terminal_counted = False
    self.last_episode_reward = 0


    if USE_LSTM:
        # 第一个参数是action size，这里传入在该机器上代加工的工序数
      self.local_network = GameACLSTMNetwork(ACTION_SIZE, thread_index, device)
    else:
        # 第一个参数是action size，这里传入在该机器上代加工的工序数
      self.local_network = GameACFFNetwork(ACTION_SIZE, thread_index, device)

    self.local_network.prepare_loss(ENTROPY_BETA)

    with tf.device(device):
      var_refs = [v._ref() for v in self.local_network.get_vars()]
      self.gradients = tf.gradients(
        self.local_network.total_loss, var_refs,
        gate_gradients=False,
        aggregation_method=None,
        colocate_gradients_with_ops=False)

    self.apply_gradients = grad_applier.apply_gradients(
      self.local_network.get_vars(),
      self.gradients )
      
    # self.sync = self.local_network.sync_from(global_network)
    
    # self.game_state = GameState(113 * thread_index)
    # 创建该工序的环境
    self.env = JspEnv(self.operations, thread_index, arrived_jobs)
    
    self.local_t = 0

    self.initial_learning_rate = initial_learning_rate

    self.episode_reward = 0

    # variable controling log output
    self.prev_local_t = 0

  def _anneal_learning_rate(self, global_time_step):
    # return self.initial_learning_rate
    learning_rate = self.initial_learning_rate * (self.max_global_time_episode - global_time_step) / self.max_global_time_episode
    if learning_rate < 0.0:
      learning_rate = 0.0
    return learning_rate

  def choose_action(self, pi_values, use_max_choice):
    # if len(self.env.action_space) != 1:
    #   print('\n------------------------------------------------'
    #         'machine = {}'.format(self.thread_index))
    #   print('action space = {}'.format(self.env.action_space))
    #   print('pi = {}'.format(pi_values))
    #
    # for i in range(len(pi_values)):
    #   if i not in self.env.action_space:
    #     pi_values[i] = 0
    # sum = np.sum(pi_values)
    # if sum == 0:
    #   return np.random.choice(self.env.action_space)
    # else:
    #   for i in range(len(pi_values)):
    #     pi_values[i] = pi_values[i] / sum
    #   if use_max_choice:
    #     if len(self.env.action_space) != 1:
    #       pi_values[self.env.machine_size] = 0
    #     return np.argmax(pi_values)
    #   else:
    #     return np.random.choice(range(len(pi_values)), p=pi_values)
    return np.random.choice(range(len(pi_values)), p=pi_values)



  def _record_score(self, sess, summary_writer, summary_op, score_input, score, global_t):
    summary_str = sess.run(summary_op, feed_dict={
      score_input: score
    })
    summary_writer.add_summary(summary_str, global_t)
    summary_writer.flush()
    
  def set_start_time(self, start_time):
    self.start_time = start_time

  def process(self, sess, global_t, summary_writer, summary_op, score_input, use_max_choice):
    states = []
    actions = []
    rewards = []
    values = []

    terminal_end = False

    # copy weights from shared to local
    # sess.run( self.sync )

    start_local_t = self.local_t

    if USE_LSTM:
      start_lstm_state = self.local_network.lstm_state_out
    
    # t_max times loop
    # for i in range(LOCAL_T_MAX):
    while True:
      # pi_, value_ = self.local_network.run_policy_and_value(sess, self.game_state.s_t)
      pi_, value_ = self.local_network.run_policy_and_value(sess, self.env.local_state)
      action = self.choose_action(pi_, use_max_choice)

      # states.append(self.game_state.s_t)
      states.append(self.env.local_state)
      actions.append(action)
      values.append(value_)

      # if (self.thread_index == 0) and (self.local_t % LOG_INTERVAL == 0):
      # if (self.thread_index == 0):
      #   print('machine index: ' + str(self.thread_index))
      #   print('arrived jobs:{}'.format(self.env.arrived_jobs[self.thread_index]))
      #   print('actions:{}'.format(action))
      #   print('clock:{}'.format(self.env.clock))
      #   print("action space = {}".format(self.env.action_space))
      #
      #   print("pi={}".format(pi_))
      #   print(" V={}".format(value_))

      '''
      # process game
      self.game_state.process(action)

      # receive game result
      reward = self.game_state.reward
      terminal = self.game_state.terminal
      '''

      new_state, reward, terminal, info = self.env.step(action)

      self.episode_reward += reward

      # clip reward
      # rewards.append( np.clip(reward, -1, 1) )
      rewards.append(reward)

      self.local_t += 1

      # s_t1 -> s_t
      # self.game_state.update()
      
      if terminal:
        terminal_end = True
        # print("score={}".format(self.episode_reward))
        # print("complete time={}".format(self.env.clock))

        self._record_score(sess, summary_writer, summary_op, score_input,
                           self.episode_reward, global_t)

        # print('\n----------------------------------------------------')
        # print('machine index: ' + str(self.thread_index))
        # print('arrived jobs:{}'.format(self.env.arrived_jobs[self.thread_index]))
        # print('actions:{}'.format(action))
        # print('clock:{}'.format(self.env.clock))
        # print("jobs size = {}".format(len(self.env.init_operations)))
        # print("action space = {}".format(self.env.action_space))
        # print("pi={}".format(pi_))
        # print(" V={}".format(value_))
        # print('----------------------------------------------------\n')

        self.complete_time = self.env.clock
        self.last_episode_reward = self.episode_reward
        self.episode_reward = 0
        # self.game_state.reset()
        self.env.reset()
        if USE_LSTM:
          self.local_network.reset_state()
        break


    R = 0.0
    if not terminal_end:
      # R = self.local_network.run_value(sess, self.game_state.s_t)
      R = self.local_network.run_value(sess, self.env.local_state)

    actions.reverse()
    states.reverse()
    rewards.reverse()
    values.reverse()

    batch_si = []
    batch_a = []
    batch_td = []
    batch_R = []

    # compute and accmulate gradients
    for(ai, ri, si, Vi) in zip(actions, rewards, states, values):
      R = ri + GAMMA * R
      td = R - Vi
      # a = np.zeros([ACTION_SIZE])
      a = np.zeros([ACTION_SIZE])
      a[ai] = 1

      batch_si.append(si)
      batch_a.append(a)
      batch_td.append(td)
      batch_R.append(R)

    cur_learning_rate = self._anneal_learning_rate(global_t)

    if USE_LSTM:
      batch_si.reverse()
      batch_a.reverse()
      batch_td.reverse()
      batch_R.reverse()

      sess.run( self.apply_gradients,
                feed_dict = {
                  self.local_network.s: batch_si,
                  self.local_network.a: batch_a,
                  self.local_network.td: batch_td,
                  self.local_network.r: batch_R,
                  self.local_network.initial_lstm_state: start_lstm_state,
                  self.local_network.step_size : [len(batch_a)],
                  self.learning_rate_input: cur_learning_rate } )
    else:
      sess.run( self.apply_gradients,
                feed_dict = {
                  self.local_network.s: batch_si,
                  self.local_network.a: batch_a,
                  self.local_network.td: batch_td,
                  self.local_network.r: batch_R,
                  self.learning_rate_input: cur_learning_rate} )
      
    # if (self.thread_index == 0) and (self.local_t - self.prev_local_t >= PERFORMANCE_LOG_INTERVAL):
    #   self.prev_local_t += PERFORMANCE_LOG_INTERVAL
    #   elapsed_time = time.time() - self.start_time
    #   steps_per_sec = global_t / elapsed_time
    #   print("### Performance : {} STEPS in {:.0f} sec. {:.0f} STEPS/sec. {:.2f}M STEPS/hour".format(
    #     global_t,  elapsed_time, steps_per_sec, steps_per_sec * 3600 / 1000000.))

    # return advanced local step size
    diff_local_t = self.local_t - start_local_t
    return diff_local_t, self.complete_time, self.last_episode_reward
    
