import traceback

import numpy as np

from window_filters import ALL_FILTERS_DICT


class Bar:

    def __init__(self,
                 inner_left_col, inner_right_col,
                 outer_left_col, outer_right_col,
                 parent_sg=None):

        self.inner_left_col = inner_left_col
        self.inner_right_col = inner_right_col
        self.outer_left_col = outer_left_col
        self.outer_right_col = outer_right_col

        self.assign_parent_sg(parent_sg)

        return


    @classmethod
    def make_object_from_dict(cls, sg_obj, bar_dict):
        try:
            are_variables_present = cls.verify_variable_presence_in_dict(bar_dict)
            if not are_variables_present:
                print("Variable Presence Verification failed for Bar dict")
                return None

            bar_obj = cls(bar_dict["inner_left_col"],
                          bar_dict["inner_right_col"],
                          bar_dict["outer_left_col"],
                          bar_dict["outer_right_col"],
                          sg_obj)

            return bar_obj

        except Exception:
            print("Error when making Bar Object from dict")
            print(traceback.format_exc())
            return None


    @staticmethod
    def verify_variable_presence_in_dict(bar_dict):

        try:
            key_list = ["inner_left_col", "inner_right_col",
                        "outer_left_col", "outer_right_col"]

            for k in key_list:
                if k not in bar_dict:
                    print("Key \"{}\" not found in Bar dict".format(k))
                    raise

        except Exception:
            print("Error when verifying Bar dict")
            return False

        return True


    def assign_parent_sg(self, parent_sg):
        self.parent_sg = parent_sg
        return


    def to_dict(self, json_compatible=False):

        self_dict = {}

        if json_compatible:
            self_dict["inner_left_col"] = int(self.inner_left_col)
            self_dict["inner_right_col"] = int(self.inner_right_col)
            self_dict["outer_left_col"] = int(self.outer_left_col)
            self_dict["outer_right_col"] = int(self.outer_right_col)

        else:
            self_dict["inner_left_col"] = self.inner_left_col
            self_dict["inner_right_col"] = self.inner_right_col
            self_dict["outer_left_col"] = self.outer_left_col
            self_dict["outer_right_col"] = self.outer_right_col

        return self_dict


    def adjust_lims_for_new_page_width(self, target_page_width):


        if self.outer_right_col > (target_page_width - 1):
            self.outer_right_col = target_page_width - 1
            if self.inner_right_col > self.outer_right_col:
                self.inner_right_col = self.outer_right_col

        return



class VizBar:

    def __init__(self,
                 orig_bar,
                 musical_start_frame, musical_end_frame,
                 parent_sg=None):

        self.parent_sg = parent_sg

        self.orig_bar = orig_bar
        self.musical_start_frame = musical_start_frame
        self.musical_end_frame = musical_end_frame

        self.actual_start_frame = self.musical_start_frame
        self.actual_end_frame = self.musical_end_frame

        self.left_lim = self.orig_bar.outer_left_col
        self.right_lim = self.orig_bar.outer_right_col

        self.compute_bar_dimensions()

        self.filter_obj_list = []


    def assign_parent(self, parent_sg):
        self.parent_sg = parent_sg
        self.compute_bar_dimensions()
        return


    def compute_bar_dimensions(self):

        self.bar_left_col = self.left_lim
        self.bar_right_col = self.right_lim
        self.bar_width = self.bar_right_col - self.bar_left_col + 1

        if self.parent_sg is None:
            self.bar_top_row = None
            self.bar_bottom_row = None
            self.bar_height = None
        else:
            self.bar_top_row = self.parent_sg.top_row
            self.bar_bottom_row = self.parent_sg.bottom_row
            self.bar_height = self.bar_bottom_row - self.bar_top_row + 1

        return


    def add_filter_obj(self, filter_name, filter_args_dict):

        filter_class = ALL_FILTERS_DICT[filter_name]
        filter_obj = filter_class(self, **filter_args_dict)
        self.filter_obj_list.append(filter_obj)
        self.actual_start_frame = min(self.actual_start_frame, filter_obj.frame_anchor_list[0])
        self.actual_end_frame = max(self.actual_end_frame, filter_obj.frame_anchor_list[-1])

        return


    def get_bar_image_at_frame(self, frame_number):

        output_color_image = np.ones((self.bar_height, self.bar_width, 3), dtype="uint8") * 255
        output_opacity_mask = np.zeros((self.bar_height, self.bar_width), dtype="float")

        # If it is the first or the last frame, let all outputs be the default
        if (frame_number > self.actual_start_frame) and (frame_number < self.actual_end_frame):

            for filter_obj in self.filter_obj_list:
                filter_obj.apply_filter(output_color_image, output_opacity_mask, frame_number)


        return output_color_image, output_opacity_mask
