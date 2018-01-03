import logging
import numpy as np
import random
from gym import spaces
import gym
from jsp_data import get_machine_and_job_by_job_index
from jsp_data import get_jobs_size
from jsp_data import get_machine_size
import time
logger = logging.getLogger(__name__)


class JspEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self, operations, machine_index, arrived_jobs):
        self.is_terminal = False
        self.clock = 0  # 用来同步的时钟
        self.arrived_jobs = arrived_jobs
        self.machine_index = machine_index
        self.init_operations = operations
        self.initActions = list()
        self.action_space = list()
        self.idle_action = len(operations)
        self.machine_size = get_machine_size()
        self.job_size = get_jobs_size()
        self.local_state = np.zeros([2*self.job_size+1, 1])
        self.job_init_arrived_time = np.ones([self.job_size, 1]) * -1

        # 保存没有前驱的工序
        for i in range(len(operations)):
            if operations[i][1] == 0:
                self.initActions.append(i)
                self.job_init_arrived_time[i] = 0
        # 添加idle action
        self.initActions.append(self.idle_action)

        self.reset()

    def _reset(self):
        self.clock = 0
        self.operations = np.matrix(self.init_operations)
        # 用operations的剩余时间vector作为状态
        self.local_state[0:self.job_size] = self.operations[:, 2]
        self.local_state[self.job_size:(self.job_size*2)] = self.job_init_arrived_time
        self.local_state[self.job_size*2] = self.clock
        # 将没有前驱的工序初始化添加到action space中
        self.action_space = self.initActions.copy()
        self.is_terminal = False

        self.waiting_time = 0

    def _step(self, action):
        if len(self.action_space) == 1:
            self.waiting_time += 1
            # time.sleep(1)
        else:
            self.waiting_time = 0

        if action == self.idle_action:
            if len(self.action_space) != 1:  # 在机器还有可选工序时，选择了空闲action，应给出惩罚
                reward = -100
            else:
                reward = 0
                # 看看更新后的时钟是否可以激活提前到达的作业
                self._activate_waiting_jobs()
            return self.local_state, reward, self.is_terminal, {}
        if action not in self.action_space: # 若选择的工序不在可选工序范围内，应给出惩罚
            reward = -1000
            return self.local_state, reward, self.is_terminal, {}
        duration = self.operations[action, 2]
        if self.local_state[self.job_size+action] > self.clock:
            reward = -(self.local_state[self.job_size+action, 0] - self.clock + duration)
            self.clock = self.local_state[self.job_size+action, 0] + duration
        else:
            self.clock += duration
            reward = -duration
        self.local_state[self.job_size*2] = self.clock

        self.action_space.remove(action)  # 将加工完的工序从action space中移除
        # 通知被移除工序的下一道工序可以启动
        if self.init_operations[action][1] + 1 != self.idle_action:
            next_operation_index = [self.init_operations[action][0], self.init_operations[action][1] + 1]
            next_machine, next_operation = get_machine_and_job_by_job_index(next_operation_index)
            self.arrived_jobs[next_machine]\
                .append(next_operation + [self.clock])
        self.operations[action, 2] = 0    # 加工完一个operation后，将其剩余时间设置为0
        self.local_state[action] = 0
        # 判断是否终止
        if np.sum(self.local_state[0:self.job_size]) == 0:
            self.is_terminal = True
        else:
            self.is_terminal = False
        # 看看更新后的时钟是否可以激活提前到达的作业
        self._activate_waiting_jobs()
        return self.local_state, reward, self.is_terminal, {}

    def _activate_waiting_jobs(self):
        # 看看更新后的时钟是否可以激活提前到达的作业
        arrived_job_num = len(self.arrived_jobs[self.machine_index])
        if arrived_job_num > 0:
            for job in self.arrived_jobs[self.machine_index]:
                if len(self.action_space) == 1:
                    if job[3] <= self.clock + self.waiting_time:
                        # self.clock = max(self.clock, job[3])
                        self.waiting_time = 0
                        job_index = self.init_operations.index([job[0], job[1], job[2]])
                        self.action_space.append(job_index)
                        self.arrived_jobs[self.machine_index].remove(job)
                        self.local_state[self.job_size+job_index] = job[3]
                else:
                    if job[3] <= self.clock:
                        job_index = self.init_operations.index([job[0], job[1], job[2]])
                        self.action_space.append(job_index)
                        self.arrived_jobs[self.machine_index].remove(job)
                        self.local_state[self.job_size + job_index] = job[3]

    # operations = dict()  # key为a_b形式，表示第a个job的第b道工序，value为每道工序的duration
    # initActions = dict()
    # is_terminal = False
    # clock = 0  # 用来同步的时钟
    # advanced_arrived_jobs = dict()  # key为a_b形式，表示第a个job的第b道工序，value为抵达时间
    #
    # def __init__(self, operations):
    #     self.init_operations = operations
    #
    #     # 保存没有前驱的工序
    #     for i in operations.keys():
    #         if i.endswith('-0'):
    #             self.initActions[i] = operations.get(i)
    #
    #     # 用operations的剩余时间vector作为状态
    #     temp = list()
    #     for i in  operations.copy().values():
    #         temp.append(i)
    #     self.local_state = tuple(temp)
    #
    #     self.reset()
    #
    # def _step(self, action):
    #     duration = self.action_space[action]
    #     self.clock += duration
    #     reward = -duration
    #     self.operations[action] = 0  # 加工完一个operation后，将其剩余时间设置为0
    #     self.local_state = np.stack(self.operations.copy().values())
    #     self.action_space.pop(action)  # 将加工完的工序从action space中移除
    #     # 判断是否终止
    #     if np.sum(self.local_state) == 0:
    #         self.is_terminal = True
    #     else:
    #         self.is_terminal = False
    #     # 看看更新后的时钟是否可以激活提前到达的作业
    #     for i in self.advanced_arrived_jobs.keys():
    #         if self.advanced_arrived_jobs.get(i) >= self.clock:
    #             self.action_space[i] = self.operations.get(i)
    #     return self.local_state, reward, self.is_terminal, {}
    #
    # def _reset(self):
    #     self.operations = self.init_operations
    #     # 将没有前驱的工序初始化添加到action space中
    #     self.action_space = self.initActions.copy()
    #     self.is_terminal = False









