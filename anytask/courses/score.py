class TaskInfo(object):
    def __init__(self, is_shown, is_hidden, task_id, task_title, scores, can_scored, max_score, comment):
        self.is_shown = is_shown
        self.is_hidden = is_hidden
        self.task_id = task_id
        self.task_title = task_title
        self.scores = scores
        self.can_scored = can_scored
        self.max_score = max_score
        self.comment = comment
