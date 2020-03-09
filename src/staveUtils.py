class Stave:

    def __init__(self,
                 line_top_edge_rows, line_bottom_edge_rows,
                 left_lim_col=None, right_lim_col=None,
                 parent_group=None):

        self.line_top_edge_rows = line_top_edge_rows
        self.line_bottom_edge_rows = line_bottom_edge_rows

        self.assign_parent_group(parent_group)


        self.top_lim_row = self.line_top_edge_rows[0]
        self.bottom_lim_row = self.line_bottom_edge_rows[-1]

        self.left_lim_col = left_lim_col
        self.right_lim_col = right_lim_col

        return


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
