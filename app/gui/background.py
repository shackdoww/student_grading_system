"""Execute blocking application operations without touching widgets from workers."""

from uuid import uuid4

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class JobSignals(QObject):
    done = Signal(str, object, str)


class Job(QRunnable):
    def __init__(self, token, operation):
        super().__init__()
        self.token = token
        self.operation = operation
        self.signals = JobSignals()

    def run(self):
        try:
            result = self.operation()
        except Exception as error:
            self.signals.done.emit(self.token, None, str(error))
        else:
            self.signals.done.emit(self.token, result, '')


class BackgroundJobs(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.jobs = {}

    def submit(self, operation, success, failure):
        token = uuid4().hex
        job = Job(token, operation)
        self.jobs[token] = (job, success, failure)
        job.signals.done.connect(self.complete)
        QThreadPool.globalInstance().start(job)

    @Slot(str, object, str)
    def complete(self, token, result, error):
        entry = self.jobs.pop(token, None)
        if entry is None:
            return
        job, success, failure = entry
        if error:
            failure(error)
        else:
            success(result)

    def detach(self):
        # Let already-started database transactions finish, without calling closed widgets.
        for job, _, _ in self.jobs.values():
            job.signals.done.disconnect(self.complete)
        self.jobs.clear()
