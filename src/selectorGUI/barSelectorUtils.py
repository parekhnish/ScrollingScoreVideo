from copy import deepcopy

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches


BAR_LINE_GUI_CONFIDENT_COLOR = "mediumblue"
BAR_LINE_GUI_DOUBTFUL_COLOR = "coral"

OVERLAY_GUI_EVEN_COLOR = "mediumorchid"
OVERLAY_GUI_ODD_COLOR = "seagreen"
OVERLAY_GUI_ALPHA = 0.25


class StaveGroupWithBarsGUI:

    def __init__(self,
                 ax,
                 page_bin_img,
                 stave_group,
                 existing_obj=None):

        self.ax = ax
        self.stave_group = stave_group

        self.stave_group_top_row = self.stave_group.top_lim_row
        self.stave_group_bottom_row = self.stave_group.bottom_lim_row
        self.stave_group_height = self.stave_group_bottom_row - self.stave_group_top_row + 1
        self.page_width = page_bin_img.shape[1]

        if existing_obj is None:
            self.auto_determine_bar_lines(page_bin_img)
        else:
            self.copy_bar_lines_from_existing_obj(page_bin_img, existing_obj)

        self.create_bar_overlays()

        return


    def auto_determine_bar_lines(self,
                                 page_bin_img):

        num_staves = self.stave_group.num_staves

        indi_bar_line_left_edge_list = []
        indi_bar_line_right_edge_list = []
        indi_bar_line_confident_list = []
        indi_bar_line_doubtful_list = []

        for stave in self.stave_group.stave_list:
            left_edge_list, right_edge_list = weak_filter_bar_lines_in_single_stave(
                page_bin_img,
                stave.top_lim_row, stave.bottom_lim_row
            )

            confident_lines, doubtful_lines = get_bar_lines_confidence_in_single_stave(
                page_bin_img,
                stave.line_top_edge_rows, stave.line_bottom_edge_rows,
                left_edge_list, right_edge_list
            )

            indi_bar_line_left_edge_list.append(left_edge_list)
            indi_bar_line_right_edge_list.append(right_edge_list)
            indi_bar_line_confident_list.append(confident_lines)
            indi_bar_line_doubtful_list.append(doubtful_lines)

        if num_staves == 1:
            group_bar_line_left_edge_list = indi_bar_line_left_edge_list[0]
            group_bar_line_right_edge_list = indi_bar_line_right_edge_list[0]
            group_bar_line_confident_list = indi_bar_line_confident_list[0]
            group_bar_line_doubtful_list = indi_bar_line_doubtful_list[0]

        else:
            group_bar_line_left_edge_list = []
            group_bar_line_right_edge_list = []
            group_bar_line_confident_list = []
            group_bar_line_doubtful_list = []

            num_indi_bar_lines = [len(ll) for ll in indi_bar_line_left_edge_list]
            indi_ptr_list = [0 for _ in range(num_staves)]
            curr_group_bar_idx = 0

            reached_end = False
            while True:

                # Check if any pointer has gone beyond its individual last "line"
                for curr_indi_ptr, curr_num_indi_bar_lines in zip(indi_ptr_list, num_indi_bar_lines):
                    if curr_indi_ptr >= curr_num_indi_bar_lines:
                        reached_end = True
                        break

                if reached_end:
                    break


                curr_indi_bar_line_left_edges = [indi_bar_line_left_edge_list[idx][ptr]
                                                 for (idx, ptr) in enumerate(indi_ptr_list)]
                curr_indi_bar_line_right_edges = [indi_bar_line_right_edge_list[idx][ptr]
                                                  for (idx, ptr) in enumerate(indi_ptr_list)]

                (are_overlapping,
                 overlap_left_edge, overlap_right_edge) = combine_indi_bar_lines(
                    curr_indi_bar_line_left_edges,
                    curr_indi_bar_line_right_edges
                )

                # All indi bar lines overlap; hence this IS a group bar-line
                if are_overlapping:
                    curr_left_edge = min(curr_indi_bar_line_left_edges)
                    curr_right_edge = max(curr_indi_bar_line_right_edges)

                    is_confident = all([(ptr in confident_list)
                                        for (ptr, confident_list) in zip(indi_ptr_list, indi_bar_line_confident_list)])

                    group_bar_line_left_edge_list.append(curr_left_edge)
                    group_bar_line_right_edge_list.append(curr_right_edge)
                    if is_confident:
                        group_bar_line_confident_list.append(curr_group_bar_idx)
                    else:
                        group_bar_line_doubtful_list.append(curr_group_bar_idx)

                    curr_group_bar_idx += 1

                    # Increment all indi bar line ptrs
                    for idx in range(num_staves):
                        indi_ptr_list[idx] += 1


                # There is at least one non-overlapping indi bar line.
                # Just increment the leftmost ptr and continue
                else:
                    leftmost_ptr_idx = np.argmin(curr_indi_bar_line_left_edges)
                    indi_ptr_list[leftmost_ptr_idx] += 1


        num_bar_lines = len(group_bar_line_left_edge_list)

        if num_bar_lines < 2:
            group_bar_line_left_edge_list = [5, self.page_width-7]
            group_bar_line_right_edge_list = [6, self.page_width-6]
            group_bar_line_confident_list = []
            group_bar_line_doubtful_list = [0, 1]


        self.num_lines = len(group_bar_line_left_edge_list)

        self.visible_col_list = [False] * self.page_width
        self.valid_line_list = [None] * self.page_width
        self.line_to_col_map = {}

        for idx, (lc, rc) in enumerate(zip(group_bar_line_left_edge_list, group_bar_line_right_edge_list)):
            if idx in group_bar_line_confident_list:
                curr_color = BAR_LINE_GUI_CONFIDENT_COLOR
            else:
                curr_color = BAR_LINE_GUI_DOUBTFUL_COLOR

            curr_line = patches.Rectangle((lc-1, self.stave_group_top_row-1), rc-lc+1, self.stave_group_height,
                                          color=curr_color)
            self.ax.add_patch(curr_line)

            for c in range(lc, rc + 1):
                self.visible_col_list[c] = True
                self.valid_line_list[c] = curr_line

            self.line_to_col_map[curr_line] = [c for c in range(lc, rc + 1)]

        return


    def copy_bar_lines_from_existing_obj(self, page_bin_img, existing_obj):

        self.num_lines = existing_obj.num_lines
        self.visible_row_list = deepcopy(existing_obj.visible_row_list)

        page_width = page_bin_img.shape[1]
        self.valid_line_list = [None] * page_width
        self.line_to_col_map = {}

        for existing_line in existing_obj.line_to_col_map.keys():
            existing_line_x = existing_line.get_x()
            existing_line_y = existing_line.get_y()
            existing_line_width = existing_line.get_width()
            existing_line_height = existing_line.get_height()
            existing_line_color = existing_line.get_facecolor()
            existing_visibility = existing_line.get_visible()

            curr_line = patches.Rectangle((existing_line_x, existing_line_y),
                                          existing_line_width, existing_line_height,
                                          color=existing_line_color,
                                          visible=existing_visibility)

            self.line_to_col_map[curr_line] = deepcopy(existing_obj.line_to_col_map[existing_line])
            for c in self.line_to_col_map[curr_line]:
                self.valid_line_list[c] = curr_line

            self.ax.add_patch(curr_line)

        return


    def create_bar_overlays(self):

        self.bar_overlay_list = []
        self.add_bar_overlays()

        return


    def update_bar_overlays(self):

        for bo in self.bar_overlay_list:
            bo.remove()
            del bo

        self.bar_overlay_list = []
        self.add_bar_overlays()

        return


    def add_bar_overlays(self):

        left_cols, right_cols = self.get_bar_line_col_indices()
        num_visible_lines = len(left_cols)

        for idx in range(num_visible_lines - 1):
            bar_overlay_left_col = right_cols[idx] + 1
            bar_overlay_right_col = left_cols[idx + 1] - 1

            if (idx % 2) == 0:
                bar_overlay_color = OVERLAY_GUI_EVEN_COLOR
            else:
                bar_overlay_color = OVERLAY_GUI_ODD_COLOR

            curr_bar_overlay = patches.Rectangle((bar_overlay_left_col - 1, self.stave_group_top_row - 1),
                                                 bar_overlay_right_col - bar_overlay_left_col + 1,
                                                 self.stave_group_height,
                                                 color=bar_overlay_color,
                                                 alpha=OVERLAY_GUI_ALPHA)

            self.ax.add_patch(curr_bar_overlay)
            self.bar_overlay_list.append(curr_bar_overlay)

        return


    def get_bar_line_col_indices(self):
        visible_col_bool_arr = np.array(self.visible_col_list)
        line_left_edge_cols = np.nonzero(np.logical_and(visible_col_bool_arr[1:], np.invert(visible_col_bool_arr[:-1])))[0] + 1
        line_right_edge_cols = np.nonzero(np.logical_and(visible_col_bool_arr[:-1], np.invert(visible_col_bool_arr[1:])))[0]

        return line_left_edge_cols, line_right_edge_cols


    def process_click_event(self, col_click):

        has_valid_line_curr_col = self.valid_line_list[col_click]

        if has_valid_line_curr_col:
            self.toggle_line_visibility(col_click)

        else:
            if col_click == 0:
                if self.valid_line_list[col_click + 1] is not None:
                    self.add_to_line(col_click, col_click + 1)
                else:
                    self.create_new_line(col_click)

            elif col_click == (self.page_width - 1):
                if self.valid_line_list[col_click - 1]:
                    self.add_to_line(col_click, col_click - 1)
                else:
                    self.create_new_line(col_click)

            else:
                has_valid_prev_line_col = self.valid_line_list[col_click - 1]
                has_valid_next_line_col = self.valid_line_list[col_click + 1]

                if (not has_valid_prev_line_col) and (not has_valid_next_line_col):
                    self.create_new_line(col_click)
                elif has_valid_prev_line_col and has_valid_next_line_col:
                    self.merge_two_lines(col_click)
                else:
                    if has_valid_prev_line_col:
                        self.add_to_line(col_click, col_click - 1)
                    else:
                        self.add_to_line(col_click, col_click + 1)

        return


    def toggle_line_visibility(self, col_click):

        num_visible_lines = np.count_nonzero([line.get_visible()
                                              for line in self.line_to_col_map.keys()])
        curr_line = self.valid_line_list[col_click]
        curr_visibility = curr_line.get_visible()

        # Do not allow toggling OFF a line, if the number of currently visible
        # lines is <= 2
        if (curr_visibility is True) and (num_visible_lines <= 2):
            return

        new_visibility = not curr_visibility
        curr_line.set_visible(new_visibility)

        line_col_list = self.line_to_col_map[curr_line]
        for col in line_col_list:
            self.visible_col_list[col] = new_visibility

        self.update_bar_overlays()

        return


    def create_new_line(self, col_click):

        lc = col_click
        rc = col_click

        curr_line = patches.Rectangle((lc - 1, self.stave_group_top_row - 1), rc - lc + 1, self.stave_group_height,
                                      color=BAR_LINE_GUI_CONFIDENT_COLOR)
        self.ax.add_patch(curr_line)

        for c in range(lc, rc + 1):
            self.visible_col_list[c] = True
            self.valid_line_list[c] = curr_line

        self.line_to_col_map[curr_line] = [col_click]
        self.num_lines += 1

        self.update_bar_overlays()

        return


    def add_to_line(self, col_click, existing_col):

        curr_line = self.valid_line_list[existing_col]

        prev_width = curr_line.get_width()
        new_width = prev_width + 1

        prev_x = curr_line.get_x()
        if col_click < existing_col:
            new_x = prev_x - 1
        else:
            new_x = prev_x

        curr_line.set_width(new_width)
        curr_line.set_x(new_x)
        curr_line.set_visible(True)

        line_col_list = self.line_to_col_map[curr_line]
        for col in line_col_list:
            self.visible_row_list[col] = True

        self.visible_col_list[col_click] = True
        self.valid_line_list[col_click] = curr_line
        self.line_to_col_map[curr_line] = sorted(self.line_to_col_map[curr_line] + [col_click])

        self.update_bar_overlays()

        return


    def merge_two_lines(self, col_click):

        # Disallow merge if number of visible lines is <= 2!
        num_visible_lines = np.count_nonzero([line.get_visible()
                                              for line in self.line_to_col_map.keys()])
        if num_visible_lines <= 2:
            return


        line_to_left = self.valid_line_list[col_click - 1]
        line_to_right = self.valid_line_list[col_click + 1]

        merged_lc = self.line_to_col_map[line_to_left][0]
        merged_rc = self.line_to_col_map[line_to_right][-1]

        merged_line = patches.Rectangle((merged_lc-1, self.stave_group_top_row-1), merged_rc-merged_lc+1, self.stave_group_height,
                                        color=BAR_LINE_GUI_CONFIDENT_COLOR)
        self.ax.add_patch(merged_line)

        for c in range(merged_lc, merged_rc + 1):
            self.visible_col_list[c] = True
            self.valid_line_list[c] = merged_line

        self.line_to_col_map[merged_line] = list(np.arange(merged_lc, merged_rc+1))
        self.num_lines -= 1

        line_to_left.remove()
        del self.line_to_col_map[line_to_left]
        del line_to_left

        line_to_right.remove()
        del self.line_to_col_map[line_to_right]
        del line_to_right

        self.update_bar_overlays()

        return



def combine_indi_bar_lines(left_edges, right_edges):

    min_left_edge = min(left_edges)
    max_left_edge = max(left_edges)
    min_right_edge = min(right_edges)
    max_right_edge = max(right_edges)

    if max_left_edge < min_right_edge:
        are_overlapping = True
    else:
        are_overlapping = False

    return are_overlapping, min_left_edge, max_right_edge



class BarSelectorGUI:

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

        self.sg_gui_list = []
        self.valid_sg_gui_list = [None] * self.img_height

        if existing_gui_obj is None:
            self.add_sg_gui_objects(page_obj)
        else:
            self.copy_sg_gui_objects_from_existing_obj(page_obj, existing_gui_obj)

        return


    def add_sg_gui_objects(self, page_obj):
        for sg in page_obj.sg_list:
            curr_sg_gui_obj = StaveGroupWithBarsGUI(self.ax, self.bin_img, sg)
            self.sg_gui_list.append(curr_sg_gui_obj)
            for r in range(curr_sg_gui_obj.stave_group_top_row, curr_sg_gui_obj.stave_group_bottom_row):
                self.valid_sg_gui_list[r] = curr_sg_gui_obj

    def copy_sg_gui_objects_from_existing_obj(self, page_obj, existing_gui_obj):
        for sg, existing_sg_gui_obj in zip(page_obj.sg_list, existing_gui_obj.sg_gui_list):
            new_sg_gui_obj = StaveGroupWithBarsGUI(self.ax, self.bin_img, sg, existing_sg_gui_obj)
            self.sg_gui_list.append(new_sg_gui_obj)
            for r in range(new_sg_gui_obj.stave_group_top_row, new_sg_gui_obj.stave_group_bottom_row):
                self.valid_sg_gui_list[r] = new_sg_gui_obj


    def get_bar_line_col_indices(self):

        list_of_left_edge_arrays = []
        list_of_right_edge_arrays = []

        for sg_gui_obj in self.sg_gui_list:
            left_edge_array, right_edge_array = sg_gui_obj.get_bar_line_col_indices()
            list_of_left_edge_arrays.append(left_edge_array)
            list_of_right_edge_arrays.append(right_edge_array)

        return list_of_left_edge_arrays, list_of_right_edge_arrays


    def on_click(self, event):
        toolbar_state = event.canvas.manager.toolbar.toolmanager.active_toggle["default"]
        if toolbar_state is not None:
            return

        x_pos = event.xdata
        y_pos = event.ydata
        if (x_pos is None) or (y_pos is None):
            return

        row_click = int(round(y_pos))
        col_click = int(round(x_pos))

        curr_sg_gui = self.valid_sg_gui_list[row_click]
        if curr_sg_gui is None:
            return

        curr_sg_gui.process_click_event(col_click)

        event.canvas.draw()
        return


def weak_filter_bar_lines_in_single_stave(bin_img,
                                          stave_top_lim_row, stave_bottom_lim_row):

    # Get the cropped image corresponding to the rows of the staff
    stave_img = bin_img[stave_top_lim_row: stave_bottom_lim_row+1, :]
    stave_height = stave_img.shape[0]

    # Count the number of TRUE pixels in each column
    count_arr = np.count_nonzero(stave_img, axis=0)

    # --------------------------------------------------------------------------
    # Main logic:
    # A bar line will span the whole height of the stave.
    # NOTE --- This doesn't work the other way round; not every vertical line
    #          that spans the stave height is a bar line!
    #          Thus, this function returns a list of good, possible bar lines;
    #          it is not perfect.
    # --------------------------------------------------------------------------

    # Find the columns that span the whole height with TRUE pixels
    valid_bar_line_bool_arr = (count_arr == stave_height)

    # --------------------------------------------------------------------------
    # A bar line may be "thick" i.e. it may span multiple adjoining columns
    # Thus, get the left and right edge of each such bar line
    # --------------------------------------------------------------------------
    left_edge_col_indices = np.nonzero(np.logical_and(valid_bar_line_bool_arr[1:], np.invert(valid_bar_line_bool_arr[:-1])))[0] + 1
    right_edge_col_indices = np.nonzero(np.logical_and(valid_bar_line_bool_arr[:-1], np.invert(valid_bar_line_bool_arr[1:])))[0]

    return left_edge_col_indices, right_edge_col_indices


def get_bar_lines_confidence_in_single_stave(bin_img,
                                             stave_line_top_row_indices, stave_line_bottom_row_indices,
                                             bar_line_left_edge_indices, bar_line_right_edge_indices):

    # Get the cropped image corresponding to the rows of the staff
    stave_top_lim_row = stave_line_top_row_indices[0]
    stave_bottom_lim_row = stave_line_bottom_row_indices[-1]
    stave_img = bin_img[stave_top_lim_row: stave_bottom_lim_row+1, :]

    # Count the number of pixels in the staff image, that belong to the staff
    # lines. Essentially, this is the sum of (bottom-top+1) for all 5 staff lines
    total_staff_line_pixels = np.sum(stave_line_bottom_row_indices - stave_line_top_row_indices) + 5

    # Get the number of candidate bar lines
    num_candidate_bar_lines = len(bar_line_left_edge_indices)

    # The bar lines will be separated into confident and doubtful candidates
    confident_candidates = []
    doubtful_candidates = []

    # Loop over every candidate ...
    for i in range(num_candidate_bar_lines):

        # Default: Left edge and right edge is invalid
        is_left_valid = False
        is_right_valid = False

        # Get the left and right edge of the candidate bar line
        left_edge_index = bar_line_left_edge_indices[i]
        right_edge_index = bar_line_right_edge_indices[i]

        # Get the row pixel counts of the columns left of the left edge and
        # right of the right edge
        left_minus_one_row_sum = np.count_nonzero(stave_img[:, left_edge_index - 1])
        right_plus_one_row_sum = np.count_nonzero(stave_img[:, right_edge_index + 1])

        # ----------------------------------------------------------------------
        # Main logic:
        # Definite bar lines will have "empty" space on either sides of them,
        # except for the staff lines themselves;
        # (Slip-up: What about tie-lines crossing a bar line?)
        # Also, The first and last bar lines will have their left and right
        # sides empty, respectively;
        # So bar edges not meeting these conditions will be considered "doubtful"
        # ----------------------------------------------------------------------

        # Find if the bar line edges meet the "requirements"
        if (i == 0) or (left_minus_one_row_sum <= total_staff_line_pixels):
            is_left_valid = True
        if (i == (num_candidate_bar_lines - 1)) or (right_plus_one_row_sum <= total_staff_line_pixels):
            is_right_valid = True

        # Append the id to the respective list
        if is_left_valid and is_right_valid:
            confident_candidates.append(i)
        else:
            doubtful_candidates.append(i)

    # Convert the lists to arrays
    confident_candidates = np.array(confident_candidates)
    doubtful_candidates = np.array(doubtful_candidates)

    return confident_candidates, doubtful_candidates



def open_and_close_interactive_gui(page_obj,
                                   existing_gui_obj=None):

    orig_tb_manager = plt.rcParams["toolbar"]
    plt.rcParams["toolbar"] = "toolmanager"

    bar_selector_gui = BarSelectorGUI(page_obj,
                                      existing_gui_obj=existing_gui_obj)

    if existing_gui_obj is not None:
        del existing_gui_obj

    plt.show()
    plt.close()
    plt.rcParams["toolbar"] = orig_tb_manager

    return bar_selector_gui


def interactive_bar_selector_process(page_obj):

    bar_selector_gui = None

    while True:
        bar_selector_gui = open_and_close_interactive_gui(page_obj, bar_selector_gui)
        list_of_bar_line_left_edge_col_arrays, list_of_bar_line_right_edge_col_arrays = bar_selector_gui.get_bar_line_col_indices()
        print("NUM BARS: ")
        for idx, arr in enumerate(list_of_bar_line_left_edge_col_arrays):
            print("{}:\t{}".format(idx, len(arr)))
        print("\n\n")

        # if not are_lines_valid:
        #     resp = input("Number of Stave lines are not in accordance with the number of staves in a group! Do you want to try again? (Y/N): ")
        #     if resp == "Y":
        #         continue
        #     else:
        #         break
        #
        #
        # num_lines = len(line_top_edge_rows)
        # num_staves = int(num_lines / 5)
        # num_sg = int(num_staves / stave_group_size)
        #
        # list_staves = []
        # for stave_idx in range(num_staves):
        #     curr_stave_top_row_list = line_top_edge_rows[stave_idx*5: (stave_idx+1)*5]
        #     curr_stave_bottom_row_list = line_bottom_edge_rows[stave_idx*5: (stave_idx+1) * 5]
        #     list_staves.append(Stave(curr_stave_top_row_list, curr_stave_bottom_row_list,
        #                              left_lim_col=0, right_lim_col=page_obj.page_width))
        #
        # if page_obj.num_sg > 0:
        #     page_obj.delete_sg_list()
        #
        # for sg_idx in range(num_sg):
        #     curr_stave_list = list_staves[sg_idx*stave_group_size: (sg_idx+1)*stave_group_size]
        #     page_obj.add_stave_group(StaveGroup(curr_stave_list,
        #                                         parent_page=page_obj))
        #
        # page_obj.show_overlays()

        resp = input("Do the bars look good?"
                     "(Y): Continue"
                     "(N): Go back to the bar line selection screen"
                     "-------- Your Response: ")
        if resp == "N":
            continue
        else:
            break


    return
