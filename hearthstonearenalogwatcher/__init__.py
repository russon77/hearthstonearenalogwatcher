from time import sleep

import os


class LogLocationInvalid(Exception):
    pass


class ArenaDraft(object):
    def __init__(self, hero, drafted, draft_over):
        self.hero = hero
        self.drafted = drafted
        self.draft_over = draft_over


class HearthstoneArenaLogWatcher(object):
    """
    todo documentations
    """
    class Event(object):
        """
        enumerated event types
        """
        ENTERED_ARENA = 0
        EXITED_ARENA = 1
        HERO_SELECTED = 2
        CARD_DRAFTED = 3
        DRAFT_ENDED = 4

        def __init__(self, _type, data):
            self.type = _type
            self.data = data

    def __init__(self,
                 log_folder=r"D:\Program Files\Hearthstone\Logs"):
        self.log_location = os.path.join(log_folder, "Arena.log")
        self.loading_screen_log_location = os.path.join(log_folder, "LoadingScreen.log")
        self.initial_state = self.get_state_of_current_log(self.log_location)

    @staticmethod
    def get_state_of_current_screen(loading_screen_log_location):
        """
        this method is static in order to be tested easily
        :param loading_screen_log_location:
        :return:
        """
        last_curr_mode = ""
        with open(loading_screen_log_location) as handle:
            for line in handle:
                if "currMode" in line:
                    last_curr_mode = line.split("currMode=")[1].replace("\n", "")

        return last_curr_mode

    @staticmethod
    def get_state_of_current_log(log_location):
        """
        this method is static in order to be tested easily
        :param log_location:
        :return:
        """
        hero_id_to_our_id = {
            "HERO_09": "priest",
            "HERO_08": "mage",
            "HERO_07": "warlock",
            "HERO_06": "druid",
            "HERO_05": "hunter",
            "HERO_04": "paladin",
            "HERO_03": "rogue",
            "HERO_02": "shaman",
            "HERO_01": "warrior"
        }

        hero = None
        draft_over = False
        cards = []

        with open(log_location) as log_file:
            for line in log_file:
                # resumed draft
                if "DraftManager.OnChoicesAndContents - Draft deck contains card" in line:
                    cards.append(line.rsplit(" ", 1)[1].replace("\n", ""))
                elif "DraftManager.OnChoicesAndContents" in line and "Hero Card = " in line:
                    hero = hero_id_to_our_id[line.rsplit(" ", 1)[1].replace("\n", "")]
                    # if the hero is set this way, reset the drafted cards array as well
                    cards = []
                # current draft actions
                elif "Client chooses: " in line:
                    cards.append(line.rsplit(" ", 1)[1].replace("\n", "")[1:-1])
                # check if draft has completed
                elif "SetDraftMode - ACTIVE_DRAFT_DECK" in line:
                    draft_over = True
                # on the converse, check if draft is not yet completed
                elif "SetDraftMode - DRAFTING" in line:
                    draft_over = False

        return ArenaDraft(hero, cards, draft_over)

    def event_generator(self, speed=1):
        """
        generator for hearthstone events
        :param speed: integer representing how long to sleep between checking the log file. higher is faster
        :return:
        """
        prev_mode = None
        previous_state = None
        full_draft_emitted = False

        while True:

            if not os.path.isfile(self.log_location):
                previous_state = None
                sleep(1 / speed)
                continue

            current_state = self.get_state_of_current_log(self.log_location)

            if full_draft_emitted and current_state.draft_over:
                sleep(1 / speed)
                continue

            cur_mode = self.get_state_of_current_screen(self.loading_screen_log_location)

            if prev_mode != cur_mode:
                if cur_mode == "DRAFT":
                    yield \
                        HearthstoneArenaLogWatcher.Event(HearthstoneArenaLogWatcher.Event.ENTERED_ARENA, current_state)

                    previous_state = current_state
                    prev_mode = cur_mode
                    continue
                elif prev_mode == "DRAFT":
                    yield \
                        HearthstoneArenaLogWatcher.Event(HearthstoneArenaLogWatcher.Event.EXITED_ARENA, current_state)

                    previous_state = current_state
                    prev_mode = cur_mode
                    continue

            if cur_mode == "DRAFT":

                if len(current_state.drafted) != len(previous_state.drafted):
                    yield \
                        HearthstoneArenaLogWatcher.Event(HearthstoneArenaLogWatcher.Event.CARD_SELECTED, current_state)

                if len(current_state.drafted) == 30:
                    full_draft_emitted = True

                    yield \
                        HearthstoneArenaLogWatcher.Event(HearthstoneArenaLogWatcher.Event.DRAFT_ENDED, current_state)

            previous_state = current_state
            prev_mode = cur_mode
            sleep(1 / speed)

if __name__ == '__main__':
    # todo real testing... in the testing folder?
    y = HearthstoneArenaLogWatcher.get_state_of_current_log(r"D:\Program Files\Hearthstone\Logs\Arena.log")

    print(y)