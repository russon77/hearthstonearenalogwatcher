from unittest import TestCase
from hearthstonearenalogwatcher import HearthstoneArenaLogWatcher

import json
import os


class TestArenaLogParser(TestCase):
    def test_ArenaLogParser(self):
        master = json.load(open(os.path.join(os.path.dirname(__file__), "arena_log_data/master.json")))
        for key in master:
            draft_state = HearthstoneArenaLogWatcher.get_state_of_current_log(
                os.path.join(os.path.dirname(__file__), "arena_log_data/%s.log" % key))

            for subkey in master[key]:
                self.assertEqual(getattr(draft_state, subkey), master[key][subkey],
                                 msg="\nLogfile %s.log\tKey %s\tReceived: %s\tExpected: %s\n" %
                                     (key, subkey, getattr(draft_state, subkey), master[key][subkey]))


class TestLoadingScreenLogParser(TestCase):
    def test_LoadingScreenLogParser(self):
        master = json.load(open(os.path.join(os.path.dirname(__file__), "loading_screen_log_data/master.json")))
        for key in master:
            current_mode = \
                HearthstoneArenaLogWatcher.get_state_of_current_screen("loading_screen_log_data/%s.log" % key)

            self.assertEqual(current_mode, master[key])
