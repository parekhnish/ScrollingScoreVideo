import tty
import sys
import termios

import time

from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio


class BarDemarcator:

    def __init__(self,
                 audio_filename):

        self.rel_bar_start_timestamps = []
        self.num_bars = 0
        self.start_time = None
        self.end_time = None

        self.audio_segment = AudioSegment.from_file(audio_filename)
        self.playback = None

    def actual_loop(self):
        # ----------------------------------------------------------------------
        # Inspired from https://stackoverflow.com/a/34497639/6862058
        # ----------------------------------------------------------------------
        print("<z>: Start/stop the audio")
        print("<m>: Mark bar")
        print("Press <z> to start!:\n\n")

        orig_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)

        is_playing = False

        while True:

            x = sys.stdin.read(1)[0]
            if x == "z":
                if self.playback is None:
                    self.start_time = time.time()
                    self.playback = _play_with_simpleaudio(self.audio_segment)

                else:
                    self.end_time = time.time()
                    if self.playback.is_playing():
                        self.playback.stop()
                    break

            elif x == "m":
                curr_time = time.time()
                rel_bar_start_time = curr_time - self.start_time
                self.num_bars += 1
                self.rel_bar_start_timestamps.append(rel_bar_start_time)
                print("Bar #{:>3}: {}".format(self.num_bars, rel_bar_start_time))



        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)
        return
