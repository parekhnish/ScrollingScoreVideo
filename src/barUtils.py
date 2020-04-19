import traceback

import numpy as np


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




class VizBar(Bar):

    def __init__(self,
                 inner_left_col, inner_right_col,
                 outer_left_col, outer_right_col,
                 parent_viz_sg,
                 start_frame, end_frame,
                 bar_color, bar_alpha):

        super().__init__(inner_left_col, inner_right_col,
                         outer_left_col, outer_right_col,
                         parent_viz_sg)

        self.start_frame = start_frame
        self.end_frame = end_frame

        self.bar_color = bar_color
        self.bar_alpha = bar_alpha

        return

    @staticmethod
    def verify_variable_presence_in_dict(viz_bar_dict):

        try:
            base_variables_present = super(VizBar, VizBar).verify_variable_presence_in_dict(viz_bar_dict)
            if not base_variables_present:
                return False

            key_list = ["start_frame", "end_frame",
                        "bar_color", "bar_alpha"]

            for k in key_list:
                if k not in viz_bar_dict:
                    print("Key \"{}\" not found in Bar dict".format(k))
                    raise

        except Exception:
            print("Error when verifying Viz Bar dict")
            return False

        return True


    @classmethod
    def make_object_from_dict(cls, viz_sg_obj, viz_bar_dict):
        try:
            are_variables_present = cls.verify_variable_presence_in_dict(viz_bar_dict)
            if not are_variables_present:
                print("Variable Presence Verification failed for Viz Bar dict")
                return None

            viz_bar_obj = cls(viz_bar_dict["inner_left_col"],
                              viz_bar_dict["inner_right_col"],
                              viz_bar_dict["outer_left_col"],
                              viz_bar_dict["outer_right_col"],
                              viz_sg_obj,
                              viz_bar_dict["start_frame"],
                              viz_bar_dict["end_frame"],
                              viz_bar_dict["bar_color"],
                              viz_bar_dict["bar_alpha"])

            return viz_bar_obj

        except Exception:
            print("Error when making Viz Bar Object from dict")
            print(traceback.format_exc())
            return None


    def to_dict(self, json_compatible=False):

        output_dict = super().to_dict(json_compatible)

        output_dict["bar_color"] = self.bar_color

        if json_compatible:
            output_dict["start_frame"] = int(self.start_frame)
            output_dict["end_frame"] = int(self.end_frame)

            output_dict["bar_alpha"] = float(self.bar_alpha)

        else:
            output_dict["start_frame"] = self.start_frame
            output_dict["end_frame"] = self.end_frame

            output_dict["bar_alpha"] = self.bar_alpha


        return output_dict


    @staticmethod
    def make_viz_bar_from_bar(bar_obj,
                              start_frame=0, end_frame=1,
                              bar_color=None, bar_alpha=None,
                              parent_viz_sg=None):

        viz_bar_dict = bar_obj.to_dict()

        viz_bar_dict["start_frame"] = start_frame
        viz_bar_dict["end_frame"] = end_frame

        if bar_color is not None:
            viz_bar_dict["bar_color"] = bar_color
        else:
            hex_char_str = "0123456789abcdef"
            random_color = "#"
            for i in range(6):
                random_char = hex_char_str[int(np.random.rand() * 16)]
                random_color += random_char
            viz_bar_dict["bar_color"] = random_color


        if bar_alpha is not None:
            viz_bar_dict["bar_alpha"] = bar_alpha
        else:
            viz_bar_dict["bar_alpha"] = np.random.rand()

        viz_bar_obj = VizBar.make_object_from_dict(parent_viz_sg, viz_bar_dict)

        return viz_bar_obj
