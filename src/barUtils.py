import traceback

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

            stave_obj = cls(bar_dict["inner_left_col"],
                            bar_dict["inner_right_col"],
                            bar_dict["outer_left_col"],
                            bar_dict["outer_right_col"],
                            sg_obj)

            return stave_obj

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
