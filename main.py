#!/usr/bin/env python3
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, FileType
from threading import Thread, Event
from queue import Empty, Queue
from lib.pastlylogger import PastlyLogger
from lib.worker import Worker
from lib.datamanager import DataManager
import time, sys
def fail_hard(*msg):
    if msg: print(*msg, file=sys.stderr)
    exit(1)

class WorkerFeeder():
    def __init__(self, args, log, dm, end_event, name):
        self._args, self._dm = args, dm
        self._end_event = end_event
        self._name = name
        self.input = Queue(maxsize=1)
        self.thread = Thread(target=self._enter)
        self.thread.name = self._name
        self.thread.start()

    def wait(self):
        assert self.thread != None
        self.thread.join()

    def _enter(self):
        log('Starting WorkerFeeder',self._name)
        self._worker = Worker(self._args, log, self._dm)
        while not self.input.empty() or not self._end_event.is_set():
            item = None
            try: item = self.input.get(timeout=0.01)
            except Empty: continue
            if item:
                direction, item = item
                if direction == 'enc':
                    self._worker.process_enc(*item)
                else:
                    self._worker.process_clear(*item)
        log('Ending WorkerFeeder',self._name)

# block until one of the threads is available to take work, and return it
def get_next_worker_thread(threads):
    while True:
        for thr in threads:
            if not thr.input.full():
                return thr
        time.sleep(0.01)

def wait_for_threads(threads):
    for thr in threads:
        while not thr.input.empty():
            time.sleep(0.01)

def main(args):
    global log
    if args.debug:
        log = PastlyLogger(info='/dev/stderr', overwrite=['info'],
                log_threads=True)
    else:
        log = PastlyLogger(info='/dev/null', overwrite=['info'],
                log_threads=True)
    kill_worker_threads = Event()
    kill_data_manager_thread = Event()
    dm = DataManager(args, log, kill_data_manager_thread)
    workers = [ WorkerFeeder(args, log, dm, kill_worker_threads,
            'Worker-{}'.format(i)) for i in range(0, args.threads) ]
    for enc in args.encrypted:
        dm.init_data(l=len(enc))
        for idx, char in enumerate(enc):
            thr = get_next_worker_thread(workers)
            thr.input.put( ('enc',(idx, char)) )
        wait_for_threads(workers)
        dm.print_data(times=args.times)
    for clear in args.clear:
        dm.init_data(l=len(clear))
        for idx, char in enumerate(clear):
            thr = get_next_worker_thread(workers)
            thr.input.put( ('clear',(idx, char)) )
        wait_for_threads(workers)
        dm.print_data(times=args.times)
    wait_for_threads(workers)
    kill_worker_threads.set()
    for thr in workers: thr.wait()
    kill_data_manager_thread.set()

if __name__=='__main__':
    DEF_ENC = ['Uryy1MQn6nMN0ny@6vp5M{Mc@6u10']
    DEF_CLEAR = []
    ALPHA, NUM = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '0123456789',
    ALPHA += ALPHA.lower()
    SPECIAL = '!@#$%^&*()_-+=\|]}[{\'";:/?.>,< '
    parser = ArgumentParser(
            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r','--times', metavar='NUM', type=int,
            help='Number of times to repeat phrases', default=10)
    parser.add_argument('-t','--threads', metavar='NUM', type=int,
            help='Number of worker threads', default=8)
    parser.add_argument('--debug', action='store_true',
            help='Debug development')
    parser.add_argument('-e','--encrypted', metavar='STR', type=str,
            help='An encrypted string to decrypt and securely print',
            action='append', default=DEF_ENC)
    parser.add_argument('-c','--clear', metavar='STR', type=str,
            help='A plain-text string to securely print',
            action='append', default=DEF_CLEAR)
    parser.add_argument('-d','--dictionary', metavar='STR', type=str,
            help='A list of all possible characters',
            default=ALPHA+NUM+SPECIAL)
    args = parser.parse_args()
    if args.encrypted != DEF_ENC or args.clear != DEF_CLEAR:
        args.encrypted = args.encrypted[len(DEF_ENC):]
        args.clear = args.clear[len(DEF_CLEAR):]
    args.dictionary = [ c for c in args.dictionary ]
    if args.threads < 1: fail_hard('Don\'t be stupid')
    if args.times < 1: fail_hard('Don\'t be stupid')
    exit(main(args))
