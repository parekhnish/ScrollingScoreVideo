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




class StaveGroup:

    def __init__(self,
                 stave_list=None,
                 parent_page=None):

        self.assign_parent_page(parent_page)

        if stave_list is None:
            self.stave_list = []
        else:
            self.stave_list = stave_list

        self.num_staves = len(self.stave_list)

        self.assign_parent_to_all_child_staves()
        self.determine_left_right_cols()
        self.determine_top_bottom_rows()


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

        if self.num_staves > 0:
            self.left_lim_col = min([stave.left_lim_col for stave in self.stave_list])
            self.right_lim_col = max([stave.right_lim_col for stave in self.stave_list])
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
