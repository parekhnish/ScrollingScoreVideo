from copy import deepcopy

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from staveUtils import Stave, StaveGroup


INSIDE_STAVE_GAP_DEVIATION = 5
GUI_CONFIDENT_COLOR = "C0"
GUI_DOUBTFUL_COLOR = "C1"


class StaveLineSelectorGUI:

    def __init__(self,
                 page_obj,
                 existing_gui_obj=None):

        self.orig_img = page_obj.orig_image
        self.bin_img = page_obj.bin_image

        self.img_height = self.bin_img.shape[0]
        self.img_width = self.bin_img.shape[1]

        self.figure = plt.figure()
        self.ax = plt.gca()

        self.ax.imshow(self.orig_img)
        self.figure.canvas.mpl_connect("button_press_event", self.on_click)

        if existing_gui_obj is None:
            self.auto_determine_lines()
        else:
            self.copy_lines_from_existing_obj(existing_gui_obj)

        return



    def copy_lines_from_existing_obj(self, existing_obj):

        self.num_lines = existing_obj.num_lines
        self.visible_row_list = deepcopy(existing_obj.visible_row_list)

        self.valid_line_list = [None] * self.img_height
        self.line_to_row_map = {}

        for existing_line in existing_obj.line_to_row_map.keys():
            existing_line_y = existing_line.get_y()
            existing_line_height = existing_line.get_height()
            existing_line_color = existing_line.get_facecolor()

            curr_line = patches.Rectangle((0, existing_line_y), self.img_width, existing_line_height,
                                          color=existing_line_color)

            self.line_to_row_map[curr_line] = deepcopy(existing_obj.line_to_row_map[existing_line])
            for r in self.line_to_row_map[curr_line]:
                self.valid_line_list[r] = curr_line

            self.ax.add_patch(curr_line)

        return


    def auto_determine_lines(self):

        top_edge_row_indices, bottom_edge_row_indices = weak_filter_stave_lines(self.bin_img)
        self.num_lines = len(top_edge_row_indices)

        confident_indices, doubtful_indices = get_stave_lines_confidence(top_edge_row_indices,
                                                                         bottom_edge_row_indices)

        self.visible_row_list = [False] * self.img_height
        self.valid_line_list = [None] * self.img_height
        self.line_to_row_map = {}

        for idx, (tr, br) in enumerate(zip(top_edge_row_indices, bottom_edge_row_indices)):
            if idx in confident_indices:
                curr_color = GUI_CONFIDENT_COLOR
            else:
                curr_color = GUI_DOUBTFUL_COLOR

            curr_line = patches.Rectangle((0, tr - 1), self.img_width, br - tr + 1,
                                          color=curr_color)
            self.ax.add_patch(curr_line)

            for r in range(tr, br + 1):
                self.visible_row_list[r] = True
                self.valid_line_list[r] = curr_line

            self.line_to_row_map[curr_line] = [r for r in range(tr, br + 1)]

        return


    def get_line_row_indices(self):

        visible_row_bool_arr = np.array(self.visible_row_list)
        line_top_edge_rows = np.nonzero(np.logical_and(visible_row_bool_arr[1:], np.invert(visible_row_bool_arr[:-1])))[0] + 1
        line_bottom_edge_rows = np.nonzero(np.logical_and(visible_row_bool_arr[:-1], np.invert(visible_row_bool_arr[1:])))[0]

        return line_top_edge_rows, line_bottom_edge_rows



    def on_click(self, event):
        toolbar_state = event.canvas.manager.toolbar.toolmanager.active_toggle["default"]
        if toolbar_state is not None:
            return

        x_pos = event.xdata
        y_pos = event.ydata
        if (x_pos is None) or (y_pos is None):
            return

        row_click = int(round(y_pos))
        has_valid_line_curr_row = self.valid_line_list[row_click]

        if has_valid_line_curr_row:
            self.toggle_line_visibility(row_click)

        else:
            if row_click == 0:
                if self.valid_line_list[row_click + 1] is not None:
                    self.add_to_line(row_click, row_click + 1)
                else:
                    self.create_new_line(row_click)

            elif row_click == (self.img_height-1):
                if self.valid_line_list[row_click - 1]:
                    self.add_to_line(row_click, row_click - 1)
                else:
                    self.create_new_line(row_click)

            else:
                has_valid_prev_line_row = self.valid_line_list[row_click - 1]
                has_valid_next_line_row = self.valid_line_list[row_click + 1]

                if (not has_valid_prev_line_row) and (not has_valid_next_line_row):
                    self.create_new_line(row_click)
                elif has_valid_prev_line_row and has_valid_next_line_row:
                    self.merge_two_lines(row_click)
                else:
                    if has_valid_prev_line_row:
                        self.add_to_line(row_click, row_click - 1)
                    else:
                        self.add_to_line(row_click, row_click + 1)

        event.canvas.draw()
        return


    def toggle_line_visibility(self, row_click):

        curr_line = self.valid_line_list[row_click]
        curr_visibility = curr_line.get_visible()
        new_visibility = not curr_visibility
        curr_line.set_visible(new_visibility)

        line_row_list = self.line_to_row_map[curr_line]
        for row in line_row_list:
            self.visible_row_list[row] = new_visibility

        return


    def create_new_line(self, row_click):

        tr = row_click
        br = row_click

        curr_line = patches.Rectangle((0, tr - 1), self.img_width, br - tr + 1,
                                      color=GUI_CONFIDENT_COLOR)
        self.ax.add_patch(curr_line)

        for r in range(tr, br + 1):
            self.visible_row_list[r] = True
            self.valid_line_list[r] = curr_line

        self.line_to_row_map[curr_line] = [row_click]
        self.num_lines += 1

        return


    def add_to_line(self, row_click, existing_row):

        curr_line = self.valid_line_list[existing_row]

        prev_height = curr_line.get_height()
        new_height = prev_height + 1

        prev_y = curr_line.get_y()
        if row_click < existing_row:
            new_y = prev_y - 1
        else:
            new_y = prev_y

        curr_line.set_height(new_height)
        curr_line.set_y(new_y)
        curr_line.set_visible(True)

        line_row_list = self.line_to_row_map[curr_line]
        for row in line_row_list:
            self.visible_row_list[row] = True

        self.visible_row_list[row_click] = True
        self.valid_line_list[row_click] = curr_line
        self.line_to_row_map[curr_line] = sorted(self.line_to_row_map[curr_line] + [row_click])

        return


    def merge_two_lines(self, row_click):

        line_above = self.valid_line_list[row_click - 1]
        line_below = self.valid_line_list[row_click + 1]

        merged_tr = self.line_to_row_map[line_above][0]
        merged_br = self.line_to_row_map[line_below][-1]

        merged_line = patches.Rectangle((0, merged_tr - 1), self.img_width, merged_br - merged_tr + 1,
                                        color=GUI_CONFIDENT_COLOR)
        self.ax.add_patch(merged_line)

        for r in range(merged_tr, merged_br + 1):
            self.visible_row_list[r] = True
            self.valid_line_list[r] = merged_line

        self.line_to_row_map[merged_line] = list(np.arange(merged_tr, merged_br+1))
        self.num_lines -= 1

        line_above.remove()
        del self.line_to_row_map[line_above]
        del line_above

        line_below.remove()
        del self.line_to_row_map[line_below]
        del line_below

        return


def weak_filter_stave_lines(bin_img):

    # --------------------------------------------------------------------------
    # The binary image will contain white/TRUE pixels where there is
    # "ink"; i.e. white/TRUE pixels represent items on a black/FALSE background.
    # Thus, the binary image should ideally "look" like the inverted image of
    # the score page!
    # --------------------------------------------------------------------------

    # Count the number of TRUE pixels in each row, and make a sorted array of
    # those counts
    count_arr = np.count_nonzero(bin_img, axis=1)
    sorted_count_arr = np.sort(count_arr)

    # --------------------------------------------------------------------------
    # Main logic:
    # In a score page, the staff lines will be the longest horizontal lines,
    # thus summing over those horizontal lines will return a large number.
    # Also, all staff lines should be ROUGHLY the same length.
    # Summing over any other horizontal line in the image will return a much
    # smaller number, because all other items in a score are usually not
    # as horizontal and as long as staff lines.
    # Thus, a quick way to decide the threshold, of what value of this sum
    # depicts a staff line, is by finding what is the smallest "long" line.
    # This can be done by finding the largest "jump" in in a sorted array of
    # horizontal counts; the largest jump occurs will correspond
    # to the jump between the length smallest "long" line, and some other line.
    # --------------------------------------------------------------------------

    # Find the jumps between each item in the sorted array, and find where the
    # maximum jump occurs; that becomes the count threshold
    diff_arr = sorted_count_arr[1:] - sorted_count_arr[:-1]
    max_diff_ind = np.argmax(diff_arr)
    min_count_thresh = sorted_count_arr[max_diff_ind]

    # Any line that has a count above this threshold, is a staff line!
    raw_valid_row_bool_arr = count_arr > min_count_thresh

    # --------------------------------------------------------------------------
    # Due to the nature of the binary image, a single staff line may be "thick",
    # i.e. it may consist of more than one pixel rows in the image; Thus,
    # we need to find the top and bottom rows corresponding to each staff line
    # --------------------------------------------------------------------------

    # Find the top and bottom edges of each staff line
    line_top_edge_rows = np.nonzero(np.logical_and(raw_valid_row_bool_arr[1:], np.invert(raw_valid_row_bool_arr[:-1])))[0] + 1
    line_bottom_edge_rows = np.nonzero(np.logical_and(raw_valid_row_bool_arr[:-1], np.invert(raw_valid_row_bool_arr[1:])))[0]

    return line_top_edge_rows, line_bottom_edge_rows


def get_stave_lines_confidence(line_top_edge_rows, line_bottom_edge_rows):

    # --------------------------------------------------------------------------
    # MAIN LOGIC
    #
    # Given all lines, it is assumed that a very small number of lines will be
    # false positives, and there will be no false negatives.
    # Given the nature of stave lines, lines in one stave (i.e. a 5-group)
    # will be roughly equidistant from each other. Any line that is not a stave
    # line will most probably be either too close or too far from its nearest
    # stave.
    #
    # Thus, any line that is not within this "distnace" will be classified as
    # a doubtful line; the others are "confident" lines
    # --------------------------------------------------------------------------

    # Make a sorted list of line gaps
    num_lines = len(line_top_edge_rows)
    line_gaps = line_top_edge_rows[1:] - line_bottom_edge_rows[:-1]
    sorted_line_gaps = np.sort(line_gaps)

    # Find the median of such gaps (this should correspond to the median
    # inter-stave line gap)
    # Make a rough range of "acceptable" line gaps
    median_inside_stave_gap = sorted_line_gaps[int(num_lines/2)]
    min_inside_gap = median_inside_stave_gap - INSIDE_STAVE_GAP_DEVIATION
    max_inside_gap = median_inside_stave_gap + INSIDE_STAVE_GAP_DEVIATION


    confident_line_indices = []
    doubtful_line_indices = []

    for idx in range(num_lines):

        # Use only the lower gap for the first line on the page
        if idx == 0:
            gap_above = median_inside_stave_gap
        else:
            gap_above = line_top_edge_rows[idx] - line_bottom_edge_rows[idx-1]

        # Use only the upper gap for the first line on the page
        if idx == (num_lines-1):
            gap_below = median_inside_stave_gap
        else:
            gap_below = line_top_edge_rows[idx+1] - line_bottom_edge_rows[idx]


        # Check if either the lower or the upper gap falls outside the
        # acceptable range
        if ((gap_above >= min_inside_gap) and (gap_above <= max_inside_gap) or
            (gap_below >= min_inside_gap) and (gap_below <= max_inside_gap)):
            confident_line_indices.append(idx)
        else:
            doubtful_line_indices.append(idx)

    confident_line_indices = np.array(confident_line_indices)
    doubtful_line_indices = np.array(doubtful_line_indices)

    return confident_line_indices, doubtful_line_indices


def open_and_close_interactive_gui(page_obj,
                                   existing_gui_obj=None):

    orig_tb_manager = plt.rcParams["toolbar"]
    plt.rcParams["toolbar"] = "toolmanager"

    stave_gui = StaveLineSelectorGUI(page_obj,
                                     existing_gui_obj=existing_gui_obj)

    if existing_gui_obj is not None:
        del existing_gui_obj

    plt.show()
    plt.close()
    plt.rcParams["toolbar"] = orig_tb_manager

    return stave_gui


def check_stave_line_validity(line_top_edge_rows, line_bottom_edge_rows,
                              stave_group_size):

    if len(line_top_edge_rows) != len(line_bottom_edge_rows):
        return False

    num_lines = len(line_top_edge_rows)
    if (num_lines % (5*stave_group_size)) != 0:
        return False

    return True



def interactive_stave_line_process(page_obj, stave_group_size=1):

    while True:
        stave_gui = open_and_close_interactive_gui(page_obj)
        line_top_edge_rows, line_bottom_edge_rows = stave_gui.get_line_row_indices()
        are_lines_valid = check_stave_line_validity(line_top_edge_rows, line_bottom_edge_rows,
                                                    stave_group_size)

        if not are_lines_valid:
            resp = input("Number of Stave lines are not in accordance with the number of staves in a group! Do you want to try again? (Y/N): ")
            if resp == "Y":
                continue
            else:
                break


        num_lines = len(line_top_edge_rows)
        num_staves = int(num_lines / 5)
        num_sg = int(num_staves / stave_group_size)

        list_staves = []
        for stave_idx in range(num_staves):
            curr_stave_top_row_list = line_top_edge_rows[stave_idx*5: (stave_idx+1)*5]
            curr_stave_bottom_row_list = line_bottom_edge_rows[stave_idx*5: (stave_idx+1) * 5]
            list_staves.append(Stave(curr_stave_top_row_list, curr_stave_bottom_row_list,
                                     left_lim_col=0, right_lim_col=page_obj.page_width))

        if page_obj.num_sg > 0:
            page_obj.delete_sg_list()

        for sg_idx in range(num_sg):
            curr_stave_list = list_staves[sg_idx*stave_group_size: (sg_idx+1)*stave_group_size]
            page_obj.add_stave_group(StaveGroup(curr_stave_list,
                                                parent_page=page_obj))

        page_obj.show_overlays()

        resp = input("Do the stave groups look good?"
                     "(Y): Continue"
                     "(N): Go back to the stave line selection screen"
                     "-------- Your Response: ")
        if resp == "N":
            continue
        else:
            break


    if are_lines_valid:
        return True

    else:
        return False
