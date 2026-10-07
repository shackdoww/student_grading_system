"""Execute blocking application operations without touching widgets from workers."""

from uuid import uuid4
from shiboken6 import isValid

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
            self.deliver(None, str(error))
        else:
            self.deliver(result, '')

    def deliver(self, result, error):
        try:
            self.signals.done.emit(self.token, result, error)
        except RuntimeError:
            # QApplication teardown can delete the signal source while an
            # already-started database transaction finishes. Do not abort writes.
            if isValid(self.signals):
                raise


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
