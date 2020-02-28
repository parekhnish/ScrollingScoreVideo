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


    def assign_parent_sg(self, parent_sg):
        self.parent_sg = parent_sg
        return


    def to_dict(self):

        self_dict = {
            "inner_left_col": self.inner_left_col,
            "inner_right_col": self.inner_right_col,
            "outer_left_col": self.outer_left_col,
            "outer_right_col": self.outer_right_col
        }

        return self_dict
