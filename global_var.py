import threading

job_finished_count = 0  # 用来计数是不是所有机器上的job都加工完了，只有都加工完了，才能讲terminal设置为True
step_synchronization_count = 0
condition = threading.Condition()
is_global_terminal = False