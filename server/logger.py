""" Server queued logger.
"""

import logging
import os
from multiprocessing import Queue, Process, Event
from queue import Empty
from config import CONFIG

LOGGERS = {}


class QueueHandler(logging.Handler):
    """ This handler sends events to a queue. Typically, it would be used together with a multiprocessing
    Queue to centralise logging to file in one process (in a multi-process application), so as to avoid
    file write contention between processes.
    """

    def __init__(self, queue):
        """ Initialise an instance, using the passed queue.
        """
        super(QueueHandler, self).__init__()
        self.queue = queue

    def enqueue(self, record):
        """ Enqueue a record. The base implementation uses put_nowait. You may want to override this method
        if you want to use blocking, timeouts or custom queue implementations.
        """
        self.queue.put_nowait(record)

    def prepare(self, record):
        """ Prepares a record for queuing. The object returned by this method is enqueued.
        The base implementation formats the record to merge the message and arguments, and removes unpickleable
        items from the record in-place. You might want to override this method if you want to convert the record
        to a dict or JSON string, or send a modified copy of the record while leaving the original intact.
        """
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), and also puts the message into
        # record.message. We can then use this to replace the original
        # msg + args, as these might be unpickleable. We also zap the
        # exc_info attribute, as it's no longer needed and, if not None,
        # will typically not be pickleable.
        self.format(record)
        record.msg = record.message
        record.args = None
        record.exc_info = None
        return record

    def emit(self, record):
        """ Emit a record. Writes the LogRecord to the queue, preparing it for pickling first.
        """
        try:
            self.enqueue(self.prepare(record))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class QueueListener(object):
    """ This class implements a listener with internal process which watches for LogRecords being added to a queue,
    removes them and passes them to a list of handlers for processing.
    """
    _sentinel = None

    def __init__(self, queue, *handlers):
        """ Initialise an instance with the specified queue and handlers.
        """
        self.queue = queue
        self.handlers = handlers
        self._stop = Event()
        self._process = None

    def dequeue(self, block, timeout=None):
        """ Dequeue a record and return it, optionally blocking. The base implementation uses get.
        You may want to override this method if you want to use timeouts or work with custom queue implementations.
        """
        return self.queue.get(block, timeout=timeout)

    def start(self):
        """ Start the listener. This starts up a background process to monitor the queue for LogRecords to handle.
        """
        self._process = p = Process(target=self._monitor)
        p.daemon = True
        p.start()

    def prepare(self, record):
        """ Prepare a record for handling. This method just returns the passed-in record. You may want to
        override this method if you need to do any custom marshalling or manipulation of the record before
        passing it to the handlers.
        """
        return record

    def handle(self, record):
        """ Handle a record. This just loops through the handlers offering them the record to handle.
        """
        record = self.prepare(record)
        for handler in self.handlers:
            if record.levelno >= handler.level:
                handler.handle(record)

    def _monitor(self):
        """ Monitor the queue for records, and ask the handler to deal with them. This method runs on a separate,
        internal process. The process will terminate if it sees a sentinel object in the queue.
        """
        q = self.queue
        has_task_done = hasattr(q, 'task_done')
        try:
            while not self._stop.is_set():
                try:
                    record = self.dequeue(True)
                    if record is self._sentinel:
                        break
                    self.handle(record)
                    if has_task_done:
                        q.task_done()
                except Empty:
                    pass
        except KeyboardInterrupt:
            pass
        # There might still be records in the queue.
        while True:
            try:
                record = self.dequeue(True, 1)
                if record is self._sentinel:
                    break
                self.handle(record)
                if has_task_done:
                    q.task_done()
            except Empty:
                break

    def stop(self):
        """ Stop the listener. This asks the process to terminate, and then waits for it to do so.
        Note that if you don't call this before your application exits, there may be some records still left
        on the queue, which won't be processed.
        """
        self._stop.set()
        self.queue.put_nowait(self._sentinel)
        self._process.join()
        self._process = None


class QueuedLogger(logging.Logger):
    """ This class represents logger which uses queue for messages and separated process to handle this messages.
    """

    def __init__(self, name, queue_listener):
        super(QueuedLogger, self).__init__(name)
        self.is_queued = True
        self.queue_listener = queue_listener
        self.is_started = False

    def start(self):
        if not self.is_started:
            self.debug('Starting logger name={0}'.format(self.name))
            self.queue_listener.start()
            self.is_started = True

    def stop(self):
        if self.is_started:
            self.debug('Stopping logger name={0}'.format(self.name))
            self.queue_listener.stop()
            self.is_started = False


def get_logger(name=None, level=logging.INFO, queued=False, log_file=None, use_stream=True):
    """ Return logger by its name or create logger if it doesn't exist.

    name: logger's name to get/create
    level: logging level of the logger
    queued: set True in order to use logger with queue and separated process for handling or
            set False to use regular logger
    log_file: file name to log to
    use_stream: set True in order to use StreamHandler
    """
    if name in LOGGERS:
        return LOGGERS[name]

    if not os.path.exists(CONFIG.LOG_DIR):
        os.makedirs(CONFIG.LOG_DIR)

    formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s')

    logger_handlers = []

    if use_stream:
        # Carriage return ('\r') is needed when terminal is in raw/cbreak mode
        logging.StreamHandler.terminator = '\r\n'
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger_handlers.append(stream_handler)

    log_file_name = log_file or name or CONFIG.DEFAULT_LOG_FILE_NAME
    file_handler = logging.FileHandler(os.path.join(CONFIG.LOG_DIR, '{}.log'.format(log_file_name)))
    file_handler.setFormatter(formatter)
    logger_handlers.append(file_handler)

    if queued:
        queue = Queue(-1)
        queue_handler = QueueHandler(queue)
        queue_listener = QueueListener(queue, *logger_handlers)
        logger = QueuedLogger(name, queue_listener)
        logger.setLevel(level)
        logger.addHandler(queue_handler)
        logger.start()
    else:
        logger = logging.getLogger(name)
        logger.is_queued = False
        logger.setLevel(level)
        for handler in logger_handlers:
            logger.addHandler(handler)

    if name is None:
        logging.basicConfig(level=level, handlers=logger.handlers)

    LOGGERS[name] = logger
    return logger


log = get_logger('tcpserver', queued=True)
