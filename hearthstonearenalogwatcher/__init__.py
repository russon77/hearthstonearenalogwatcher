from time import sleep

import os


class ArenaDraft(object):
    """
    mostly POPO - plain ol python object for hero, drafted, and draft_over
    """
    def __init__(self, hero, drafted, draft_over):
        self.hero = hero
        self.drafted = drafted
        # draft is over when the player has drafted 30 cards
        self.draft_over = draft_over


class ArenaEvent(object):
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


class HearthstoneArenaLogWatcher(object):
    """
    contains logic for generating python events with a generator. also contains static methods for
    getting the current "mode" or state of the screen, and another static method for parsing the Arena.log file
    """

    def __init__(self,
                 log_folder=r"D:\Program Files\Hearthstone\Logs"):
        self.arena_log_location = os.path.join(log_folder, "Arena.log")
        self.loading_screen_log_location = os.path.join(log_folder, "LoadingScreen.log")

    @staticmethod
    def get_state_of_current_screen(loading_screen_log_location):
        """
        this method is static in order to be tested easily
        :param loading_screen_log_location: location of Hearthstone's LoadingScreen.log
        :return: String representing current 'mode' of screen
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
        :param log_location: location of Hearthstone's Arena.log
        :return: ArenaDraft object representing current state of draft
        """
        # table for converting log's HERO_<ID> to a friendlier representation
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

        # initialize our state
        hero = None
        cards = []
        draft_over = False

        # perform main operation: loop over each line in the file (from first to last) and update the state
        # appropriately
        with open(log_location) as log_file:
            for line in log_file:
                # first check for "SetDraftMode - %s"
                # if line matches DRAFTING, then a new draft has begun, so our state should be reset
                if "SetDraftMode - DRAFTING" in line:
                    # hero = None
                    cards = []
                    draft_over = False
                # no active draft means a blank slate
                elif "SetDraftMode - NO_ACTIVE_DRAFT" in line:
                    hero = None
                    cards = []
                    draft_over = False
                elif "SetDraftMode - ACTIVE_DRAFT_DECK" in line or "SetDraftMode - IN_REWARDS" in line:
                    hero = None
                    cards = []
                    draft_over = True
                # current draft actions
                # client chooses is used for both temporary hero selection and regular card drafting.
                # if the hero has not been selected, then cards can not have been drafted.
                elif "Client chooses: " in line:
                    if hero is not None:
                        cards.append(line.rsplit(" ", 1)[1].replace("\n", "")[1:-1])

                        draft_over = False
                # next we check for hero selection. this occurs in live-drafting on the following match.
                elif "DraftManager.OnChosen(): hero" in line:
                    hero = hero_id_to_our_id[line.rsplit(" ", 2)[1].split("=")[1]]
                # resumed draft: process drafted cards and selected hero.
                # if hero is selected, that precedes the listing of all currently drafted cards, so it is necessary
                # to reset the currently drafted cards
                elif "DraftManager.OnChoicesAndContents - Draft deck contains card" in line:
                    cards.append(line.rsplit(" ", 1)[1].replace("\n", ""))

                    draft_over = False
                elif "DraftManager.OnChoicesAndContents" in line and "Hero Card = " in line:
                    hero = hero_id_to_our_id[line.rsplit(" ", 1)[1].replace("\n", "")]
                    # if the hero is set this way, reset the drafted cards array as well because
                    # the draft must have been paused / resumed at a later time
                    cards = []

                    draft_over = False
                # check to see if the draft has been reset while our watcher is open: if so, reset the draft state
                elif "SetDraftMode - NO_ACTIVE_DRAFT" in line or "SetDraftMode - ACTIVE_DRAFT_DECK" in line or \
                        "SetDraftMode - IN_REWARDS" in line:
                    hero = None
                    cards = []

        return ArenaDraft(hero, cards, draft_over)

    def event_generator(self, speed=1):
        """
        generator for hearthstone events
        :param speed: integer representing how long to sleep between checking the log file. higher is faster
        :return:
        """
        previous_mode = None
        previous_draft_state = None

        while True:
            # with the existence of Arena.log, parse the log to find the current draft state
            current_draft_state = self.get_state_of_current_log(self.arena_log_location)

            # if the ArenaDraft object is completely empty, player is probably not even in Hearthstone yet.
            # thus the previous draft state and previous mode should be reset.
            if current_draft_state.draft_over is None and len(current_draft_state.drafted) == 0:
                previous_draft_state = None
                previous_mode = None
                sleep(1 / speed)
                continue

            # parse LoadingScreen.log to find the current "mode" or screen state
            current_mode = self.get_state_of_current_screen(self.loading_screen_log_location)

            # check for Entered_Arena event
            if previous_mode != "DRAFT" and current_mode == "DRAFT":
                yield ArenaEvent(ArenaEvent.ENTERED_ARENA, current_draft_state)

            # likewise, check for Exited_Arena event
            elif previous_mode == "DRAFT" and current_mode != "DRAFT":
                yield ArenaEvent(ArenaEvent.EXITED_ARENA, current_draft_state)

            # to reach this portion, current mode and previous mode are both set to "DRAFT"
            elif previous_mode == "DRAFT" and current_mode == "DRAFT":

                # draft has ended when thirty (30) cards have been drafted. this would make the other events impossible
                # todo correct this
                if current_draft_state.draft_over and not previous_draft_state.draft_over:
                    yield ArenaEvent(ArenaEvent.DRAFT_ENDED, current_draft_state)

                # prevent Draft_Over event duplication / repeated emission
                elif previous_draft_state.draft_over and current_draft_state.draft_over:
                    pass

                # if hero has changed, it has changed from None to being selected by the player
                elif current_draft_state.hero is not None and previous_draft_state.hero != current_draft_state.hero:
                    yield ArenaEvent(ArenaEvent.HERO_SELECTED, current_draft_state)

                # to reach this branch, the hero has been selected and now we check if a card has been drafted
                elif len(previous_draft_state.drafted) != len(current_draft_state.drafted):
                    yield ArenaEvent(ArenaEvent.CARD_DRAFTED, current_draft_state)

            # finally, set our previous to current and sleep at rate of (1 / speed)
            previous_draft_state = current_draft_state
            previous_mode = current_mode
            sleep(1 / speed)
