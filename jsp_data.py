from jobshop import readJobs
from jobshop import printJobs
# from constants import DATA_PATH
DATA_PATH = "/home/peter/hfut/sourceCode/jsp-rl/dataset/ft10"  # 数据路径
is_data_loaded = False
all_jobs = tuple()

def get_data_by_machine(machine_index):
    operations = list()
    global is_data_loaded
    global all_jobs
    if not is_data_loaded:
        load_data()
    for i in range(len(all_jobs)):
        for j in range(len(all_jobs[0])):
            if all_jobs[i][j][0] == machine_index:
                operations.append([i, j, all_jobs[i][j][1]])
    return operations
    # operations = dict()
    # global is_data_loaded
    # global all_jobs
    # if not is_data_loaded:
    #     load_data()
    # for i in range(len(all_jobs)):
    #     for j in range(len(all_jobs[0])):
    #         if all_jobs[i][j][0] == machine_index:
    #             operations[str(i) + "-" + str(j)] = all_jobs[i][j][1]
    # return operations

# job[0] job[1] 分别表示第几个job的第几道工序
def get_machine_and_job_by_job_index(job):
    global is_data_loaded
    global all_jobs
    if not is_data_loaded:
        load_data()
    return all_jobs[job[0]][job[1]][0], job + [all_jobs[job[0]][job[1]][1]]

def get_jobs_size():
    global is_data_loaded
    global all_jobs
    if not is_data_loaded:
        load_data()
    return len(all_jobs)

def get_machine_size():
    global is_data_loaded
    global all_jobs
    if not is_data_loaded:
        load_data()
    return len(all_jobs[0])

def load_data(path=DATA_PATH):
    global is_data_loaded
    global all_jobs
    all_jobs = readJobs(DATA_PATH)
    print("Instance from " + DATA_PATH + "is loaded:")
    printJobs(all_jobs)
    is_data_loaded = True