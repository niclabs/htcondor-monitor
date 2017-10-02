
class CondorJob:

    def __init__(self, job_id):
        self.job_id = job_id
        self.state = None
        self.execute_machine = None
        self.running_time = 0

    def reset_state(self):
        self.state = None
