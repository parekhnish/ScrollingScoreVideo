import traceback

import numpy as np

from barUtils import Bar


class Stave:

    def __init__(self,
                 line_top_edge_rows, line_bottom_edge_rows,
                 left_lim_col=None, right_lim_col=None,
                 parent_group=None):

        self.line_top_edge_rows = np.array(line_top_edge_rows, dtype="int")
        self.line_bottom_edge_rows = np.array(line_bottom_edge_rows, dtype="int")

        self.assign_parent_group(parent_group)


        self.top_lim_row = self.line_top_edge_rows[0]
        self.bottom_lim_row = self.line_bottom_edge_rows[-1]

        self.left_lim_col = left_lim_col
        self.right_lim_col = right_lim_col

        return


    @classmethod
    def make_object_from_dict(cls, sg_obj, stave_dict):
        try:
            are_variables_present = cls.verify_variable_presence_in_dict(stave_dict)
            if not are_variables_present:
                print("Variable Presence Verification failed for SG dict")
                return None

            stave_obj = cls(stave_dict["line_top_edge_rows"],
                            stave_dict["line_bottom_edge_rows"],
                            stave_dict["left_lim_col"],
                            stave_dict["right_lim_col"],
                            sg_obj)
            return stave_obj

        except Exception:
            print("Error when making Stave Object from dict")
            print(traceback.format_exc())
            return None


    @staticmethod
    def verify_variable_presence_in_dict(stave_dict):

        try:
            key_list = ["line_top_edge_rows", "line_bottom_edge_rows",
                        "left_lim_col", "right_lim_col"]

            for k in key_list:
                if k not in stave_dict:
                    print("Key \"{}\" not found in Stave dict".format(k))
                    raise

        except Exception:
            print("Error when verifying Stave dict")
            return False

        return True



    def assign_parent_group(self, pg):
        self.parent_group = pg
        return


    def to_dict(self, json_compatible=False):

        self_dict = {}

        if json_compatible:
            self_dict["line_top_edge_rows"] = [int(r) for r in self.line_top_edge_rows]
            self_dict["line_bottom_edge_rows"] = [int(r) for r in self.line_bottom_edge_rows]
            self_dict["left_lim_col"] = int(self.left_lim_col)
            self_dict["right_lim_col"] = int(self.right_lim_col)

        else:
            self_dict["line_top_edge_rows"] = self.line_top_edge_rows
            self_dict["line_bottom_edge_rows"] = self.line_bottom_edge_rows
            self_dict["left_lim_col"] = self.left_lim_col
            self_dict["right_lim_col"] = self.right_lim_col

        return self_dict


    def offset_row_lims(self, offset):

        # Offset each line's row lims
        self.line_top_edge_rows = [r+offset for r in self.line_top_edge_rows]
        self.line_bottom_edge_rows = [r+offset for r in self.line_bottom_edge_rows]

        # Update overall limits
        self.top_lim_row = self.line_top_edge_rows[0]
        self.bottom_lim_row = self.line_bottom_edge_rows[-1]

        return


    def adjust_lims_for_new_page_width(self, target_page_width):

        if self.right_lim_col > (target_page_width - 1):
            self.right_lim_col = target_page_width - 1

        return




class StaveGroup:

    def __init__(self,
                 stave_list=None,
                 bar_list=None,
                 parent_page=None):

        self.assign_parent_page(parent_page)

        if stave_list is None:
            self.stave_list = []
        else:
            self.stave_list = stave_list

        if bar_list is None:
            self.bar_list = []
        else:
            self.bar_list = bar_list

        self.num_staves = len(self.stave_list)
        self.num_bars = len(self.bar_list)

        self.assign_parent_to_all_child_staves()
        self.determine_left_right_cols()
        self.determine_top_bottom_rows()


        return


    @classmethod
    def make_object_from_dict(cls, page_obj, sg_dict):

        try:
            are_variables_present = cls.verify_variable_presence_in_dict(sg_dict)
            if not are_variables_present:
                print("Variable Presence Verification failed for SG dict")
                return None

            sg_obj = cls(parent_page=page_obj)

            for stave_dict in sg_dict["stave_list"]:
                stave_obj = Stave.make_object_from_dict(sg_obj, stave_dict)
                if stave_obj is not None:
                    sg_obj.add_stave(stave_obj)
                else:
                    return None

            for bar_dict in sg_dict["bar_list"]:
                bar_obj = Bar.make_object_from_dict(sg_obj, bar_dict)
                if bar_obj is not None:
                    sg_obj.add_bar(bar_obj)
                else:
                    return None

            # -----
            # TODO: Check if SG obj is consistent with its child Stave and Bar
            #       elements
            # -----
            return sg_obj

        except Exception:
            print("Error when making Stave Group Object from dict")
            print(traceback.format_exc())
            return None



    @staticmethod
    def verify_variable_presence_in_dict(sg_dict):

        try:
            key_list = ["stave_list", "bar_list"]

            for k in key_list:
                if k not in sg_dict:
                    print("Key \"{}\" not found in Stave Group dict".format(k))
                    return False

        except Exception:
            print("Error when verifying Stave Group dict")
            print(traceback.format_exc())
            return False

        return True




    def to_dict(self, json_compatible=False):

        self_dict = {}

        if json_compatible:
            self_dict["top_lim_row"] = int(self.top_lim_row)
            self_dict["bottom_lim_row"] = int(self.bottom_lim_row)
            self_dict["left_lim_col"] = int(self.left_lim_col)
            self_dict["right_lim_col"] = int(self.right_lim_col)

            self_dict["num_staves"] = int(self.num_staves)
            self_dict["num_bars"] = int(self.num_bars)

        else:
            self_dict["top_lim_row"] = self.top_lim_row
            self_dict["bottom_lim_row"] = self.bottom_lim_row
            self_dict["left_lim_col"] = self.left_lim_col
            self_dict["right_lim_col"] = self.right_lim_col

            self_dict["num_staves"] = self.num_staves
            self_dict["num_bars"] = self.num_bars

        self_dict["stave_list"] = [stave.to_dict(json_compatible=json_compatible)
                                   for stave in self.stave_list]
        self_dict["bar_list"] = [bar.to_dict(json_compatible=json_compatible)
                                 for bar in self.bar_list]

        return self_dict


    def offset_row_lims(self, offset):

        # Offset the individual staves
        for stave in self.stave_list:
            stave.offset_row_lims(offset)

        # Update own limits
        self.determine_top_bottom_rows()

        return


    def delete_bar_list(self):

        self.bar_list = []
        self.num_bars = 0
        self.determine_top_bottom_rows()
        self.determine_left_right_cols()

        return


    def assign_parent_to_all_child_staves(self):

        for stave in self.stave_list:
            stave.assign_parent_group(self)
        return


    def determine_top_bottom_rows(self):

        if self.num_staves > 0:
            self.top_lim_row = self.stave_list[0].top_lim_row
            self.bottom_lim_row = self.stave_list[-1].bottom_lim_row
        else:
            self.top_lim_row = None
            self.bottom_lim_row = None

        return


    def determine_left_right_cols(self):

        # If bars are available, use them
        if self.num_bars > 0:
            self.left_lim_col = self.bar_list[0].outer_left_col
            self.right_lim_col = self.bar_list[-1].outer_right_col

        # Else, if staves are available, use them
        elif self.num_staves > 0:
            self.left_lim_col = self.stave_list[0].left_lim_col
            self.right_lim_col = self.stave_list[-1].right_lim_col

        # Else, use the defaults
        else:
            self.left_lim_col = None
            self.right_lim_col = None

        return


    def assign_parent_page(self, page):
        self.parent_page = page
        return


    def add_stave(self, new_stave):

        if self.num_staves == 0:
            insert_pos = 0

        else:
            existing_stave_top_rows = [ex_stave.top_lim_row for ex_stave in self.stave_list]
            existing_stave_bottom_rows = [ex_stave.bottom_lim_row for ex_stave in self.stave_list]

            new_stave_top_row = new_stave.top_lim_row
            new_stave_bottom_row = new_stave.bottom_lim_row

            # Check that the new stave does not overlap with existing staves!
            for ex_top, ex_bottom in zip(existing_stave_top_rows, existing_stave_bottom_rows):
                if ((ex_top <= new_stave_top_row <= ex_bottom) or
                    (ex_top <= new_stave_bottom_row <= ex_bottom)):
                    raise Exception("New stave ({}, {}) overlaps existing stave ({}, {})!".format(
                        new_stave_top_row, new_stave_bottom_row,
                        ex_top, ex_bottom
                    ))

            insert_pos = 0
            for ex_top in existing_stave_top_rows:
                if new_stave_top_row < ex_top:
                    break
                else:
                    insert_pos += 1


        self.stave_list.insert(insert_pos, new_stave)
        new_stave.assign_parent_group(self)
        self.determine_left_right_cols()
        self.determine_top_bottom_rows()
        self.num_staves += 1

        return


    def add_bar(self, new_bar):

        if self.num_bars == 0:
            insert_pos = 0

        else:
            existing_bar_inner_left_cols = [ex_bar.inner_left_col for ex_bar in self.bar_list]
            existing_bar_inner_right_cols = [ex_bar.inner_right_col for ex_bar in self.bar_list]

            new_bar_inner_left_col = new_bar.inner_left_col
            new_bar_inner_right_col = new_bar.inner_right_col

            # Check that the new bar does not overlap with existing bar!
            for ex_inner_left, ex_inner_right in zip(existing_bar_inner_left_cols, existing_bar_inner_right_cols):
                if ((ex_inner_left <= new_bar_inner_left_col <= ex_inner_right) or
                    (ex_inner_left <= new_bar_inner_right_col <= ex_inner_right)):
                    raise Exception("New bar ({}, {}) overlaps existing bar ({}, {})!".format(
                        new_bar_inner_left_col, new_bar_inner_right_col,
                        ex_inner_left, ex_inner_right
                    ))

            insert_pos = 0
            for ex_inner_left in existing_bar_inner_left_cols:
                if new_bar_inner_left_col < ex_inner_left:
                    break
                else:
                    insert_pos += 1


        self.bar_list.insert(insert_pos, new_bar)
        new_bar.assign_parent_sg(self)
        self.determine_left_right_cols()
        self.determine_top_bottom_rows()
        self.num_bars += 1

        return


    def adjust_lims_for_new_page_width(self, target_page_width):

        for stave in self.stave_list:
            stave.adjust_lims_for_new_page_width(target_page_width)

        for bar in self.bar_list:
            bar.adjust_lims_for_new_page_width(target_page_width)

        self.determine_left_right_cols()
        return



class VizStaveGroup:

    def __init__(self,
                 orig_sg,
                 offset_top_row,
                 offset_bottom_row,
                 viz_bar_list=None):

        self.orig_sg = orig_sg
        self.offset_top_row = offset_top_row
        self.offset_bottom_row = offset_bottom_row

        self.top_row = self.orig_sg.top_lim_row - self.offset_top_row
        self.bottom_row = self.orig_sg.bottom_lim_row + self.offset_top_row


        if viz_bar_list is None:
            self.viz_bar_list = []
        else:
            self.viz_bar_list = viz_bar_list


        return


    def add_viz_bar(self, viz_bar):
        viz_bar.assign_parent(self)
        self.viz_bar_list.append(viz_bar)
