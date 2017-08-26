from threading import Thread, RLock
from queue import Empty, Queue
import os.path, json
class Worker():
    OFFSET = 13 
    def __init__(self, args, log, dm):
        self._args, self._log = args, log
        self._dm = dm

    def _fail_hard(self, *msg):
        raise Exception(' '.join([ str(s) for s in msg ]))

    def _enc(self, char):
        log = self._log
        dic = self._args.dictionary
        if char not in dic:
            self._fail_hard(char,'is not in the allowed dictionary')
        i = dic.index(char)
        j = (i + Worker.OFFSET) % len(dic)
        self._log.info('enc char',char,i,j)
        return dic[j]

    def _dec(self, char):
        log = self._log
        dic = self._args.dictionary
        if char not in dic:
            self._fail_hard(char,'is not in the allowed dictionary')
        i = dic.index(char)
        j = (len(dic) + i - Worker.OFFSET) % len(dic)
        self._log.info('dec char',char,i,j)
        return dic[j]

    def process_enc(self, idx, char):
        dm = self._dm
        char = self._dec(char)
        dm.recv_char(dm.pack_char(idx, char))

    def process_clear(self, idx, char):
        dm = self._dm
        char = self._dec(self._enc(char))
        dm.recv_char(dm.pack_char(idx, char))
