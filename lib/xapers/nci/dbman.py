from thread import Thread

class FillPipeProcess(multiprocessing.Process):
    def __init__(self, it, stdout, stderr, pipe, fun=(lambda x: x)):
        multiprocessing.Process.__init__(self)
        self.it = it
        self.pipe = pipe[1]
        self.fun = fun
        self.keep_going = True
        self.stdout = stdout
        self.stderr = stderr

    def handle_sigterm(self, signo, frame):
        # this is used to suppress any EINTR errors at interpreter
        # shutdown
        self.keep_going = False

        # raises SystemExit to shut down the interpreter from the
        # signal handler
        sys.exit()

    def run(self):
        # replace filedescriptors 1 and 2 (stdout and stderr) with
        # pipes to the parent process
        os.dup2(self.stdout, 1)
        os.dup2(self.stderr, 2)

        # register a signal handler for SIGTERM
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        for a in self.it:
            try:
                self.pipe.send(self.fun(a))
            except IOError as e:
                # suppress spurious EINTR errors at interpreter
                # shutdown
                if e.errno != errno.EINTR or self.keep_going:
                    raise

        self.pipe.close()


class DBManager(object):

    def async(self, cbl, fun):
        """
        return a pair (pipe, process) so that the process writes
        `fun(a)` to the pipe for each element `a` in the iterable returned
        by the callable `cbl`.

        :param cbl: a function returning something iterable
        :type cbl: callable
        :param fun: an unary translation function
        :type fun: callable
        :rtype: (:class:`multiprocessing.Pipe`,
                :class:`multiprocessing.Process`)
        """
        # create two unix pipes to redirect the workers stdout and
        # stderr
        stdout = os.pipe()
        stderr = os.pipe()

        # create a multiprocessing pipe for the results
        pipe = multiprocessing.Pipe(False)
        receiver, sender = pipe

        process = FillPipeProcess(cbl(), stdout[1], stderr[1], pipe, fun)
        process.start()
        self.processes.append(process)
        logging.debug('Worker process {0} spawned'.format(process.pid))

        def threaded_wait():
            # wait(2) for the process to die
            process.join()

            if process.exitcode < 0:
                msg = 'received signal {0}'.format(-process.exitcode)
            elif process.exitcode > 0:
                msg = 'returned error code {0}'.format(process.exitcode)
            else:
                msg = 'exited successfully'

            logging.debug('Worker process {0} {1}'.format(process.pid, msg))
            self.processes.remove(process)

        # spawn a thread to collect the worker process once it dies
        # preventing it from hanging around as zombie
        reactor.callInThread(threaded_wait)

        def threaded_reader(prefix, fd):
            with os.fdopen(fd) as handle:
                for line in handle:
                    logging.debug('Worker process {0} said on {1}: {2}'.format(
                            process.pid, prefix, line.rstrip()))

        # spawn two threads that read from the stdout and stderr pipes
        # and write anything that appears there to the log
        reactor.callInThread(threaded_reader, 'stdout', stdout[0])
        os.close(stdout[1])
        reactor.callInThread(threaded_reader, 'stderr', stderr[0])
        os.close(stderr[1])

        # closing the sending end in this (receiving) process guarantees
        # that here the apropriate EOFError is raised upon .recv in the walker
        sender.close()
        return receiver, process

    def get_threads(self, querystring, sort='newest_first'):
        """
        asynchronously look up thread ids matching `querystring`.

        :param querystring: The query string to use for the lookup
        :type querystring: str.
        :param sort: Sort order. one of ['oldest_first', 'newest_first',
                     'message_id', 'unsorted']
        :type query: str
        :returns: a pipe together with the process that asynchronously
                  writes to it.
        :rtype: (:class:`multiprocessing.Pipe`,
                :class:`multiprocessing.Process`)
        """
        assert sort in self._sort_orders.keys()
        q = self.query(querystring)
        q.set_sort(self._sort_orders[sort])
        return self.async(q.search_threads, (lambda a: a.get_thread_id()))
