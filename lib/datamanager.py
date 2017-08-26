from threading import Thread, RLock
from queue import Empty, Queue
import os.path, json
class DataManager():
    def __init__(self, args, log, end_event):
        self._args, self._log, self._end_event = args, log, end_event

        self._char_input = Queue(maxsize=5)
        self._char_thread = Thread(target=self._char_enter,
                name='data-char').start()
        self._char_data = None
        self._char_data_lock = RLock()

    def _char_enter(self):
        log = self._log
        log('Starting DataManager char')
        while not self._end_event.is_set():
            item = None
            try: item = self._char_input.get(timeout=0.01)
            except Empty: continue
            idx, char = self._unpack_char(item)
            with self._char_data_lock:
                self._char_data[idx] = char
                log.info('Adding',char,'at index',idx,'makes',
                        ''.join([ str(c) for c in self._char_data ]))
        log('Ending DataManager char')

    def init_data(self, l):
        with self._char_data_lock:
            self._char_data = [None] * l

    def print_data(self, times):
        with self._char_data_lock:
            s = [ str(c) for c in self._char_data if c != None ]
            for _ in range(0, times): print(''.join(s))

    def recv_char(self, char): self._char_input.put(char)
    def pack_char(self, idx, char): return { 'index': idx, 'char': char }
    def _unpack_char(self, char): return char['index'], char['char']    

