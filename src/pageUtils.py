import os
import traceback

import numpy as np
from skimage.color import rgb2gray
from imageio import imread, imwrite
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from staveUtils import StaveGroup


SG_OVERLAY_COLOR = "teal"
SG_OVERLAY_ALPHA = 0.3

BAR_OVERLAY_EVEN_COLOR = "mediumorchid"
BAR_OVERLAY_ODD_COLOR = "seagreen"
BAR_OVERLAY_ALPHA = 0.25



class Page:

    def __init__(self, orig_image_filepath=None,
                 sg_list=None):

        self.orig_image_filename = os.path.basename(orig_image_filepath)
        self.orig_image = imread(orig_image_filepath)
        self.bin_image = binarize_image(self.orig_image, thresh=254)

        self.page_height = self.orig_image.shape[0]
        self.page_width = self.orig_image.shape[1]

        if sg_list is None:
            self.sg_list = []
        else:
            self.sg_list = sg_list

        self.num_sg = len(self.sg_list)

        return

    @classmethod
    def make_object_from_dict(cls, input_dir, page_dict):
        try:
            are_variables_present = cls.verify_variable_presence_in_dict(page_dict)
            if not are_variables_present:
                print("Variable Presence Verification failed for Page dict")
                return None

            orig_image_filepath = os.path.join(input_dir, page_dict["orig_image_filename"])
            if not os.path.exists(orig_image_filepath):
                print("Image {} not found".format(orig_image_filepath))
                return None

            page_obj = cls(orig_image_filepath)

            for sg_dict in page_dict["sg_list"]:
                sg_obj = StaveGroup.make_object_from_dict(page_obj, sg_dict)
                if sg_obj is not None:
                    page_obj.add_stave_group(sg_obj)
                else:
                    return None

            # -----
            # TODO: Check if Page obj is consistent with its child SG elements
            # -----
            return page_obj

        except Exception:
            print("Error when making Page Object from dict")
            print(traceback.format_exc())
            return None



    @staticmethod
    def verify_variable_presence_in_dict(page_dict):
        try:
            key_list = ["orig_image_filename",
                        "sg_list"]

            for k in key_list:
                if k not in page_dict:
                    print("Key \"{}\" not found in Page dict".format(k))
                    return False

        except Exception:
            print("Error when verifying Page dict")
            return False

        return True





    def to_dict(self, json_compatible=False):

        self_dict = {}

        self_dict["orig_image_filename"] = self.orig_image_filename

        if json_compatible:
            self_dict["page_height"] = int(self.page_height)
            self_dict["page_width"] = int(self.page_width)

        else:
            self_dict["page_height"] = self.page_height
            self_dict["page_width"] = self.page_width

        self_dict["sg_list"] = [sg.to_dict(json_compatible=json_compatible)
                                for sg in self.sg_list]

        return self_dict


    def add_stave_group(self, new_sg):

        if self.num_sg == 0:
            insert_pos = 0

        else:
            existing_sg_top_rows = [ex_sg.top_lim_row for ex_sg in self.sg_list]
            existing_sg_bottom_rows = [ex_sg.bottom_lim_row for ex_sg in self.sg_list]

            new_sg_top_row = new_sg.top_lim_row
            new_sg_bottom_row = new_sg.bottom_lim_row

            # Check that the new stave does not overlap with existing staves!
            for ex_top, ex_bottom in zip(existing_sg_top_rows, existing_sg_bottom_rows):
                if ((ex_top <= new_sg_top_row <= ex_bottom) or
                    (ex_top <= new_sg_bottom_row <= ex_bottom)):
                    raise Exception("New stave group ({}, {}) overlaps existing stave group ({}, {})!".format(
                        new_sg_top_row, new_sg_bottom_row,
                        ex_top, ex_bottom
                    ))

            insert_pos = 0
            for ex_top in existing_sg_top_rows:
                if new_sg_top_row < ex_top:
                    break
                else:
                    insert_pos += 1


        self.sg_list.insert(insert_pos, new_sg)
        new_sg.assign_parent_page(self)
        self.num_sg += 1

        return


    def delete_sg_list(self):
        self.sg_list = []
        self.num_sg = 0
        return


    def adjust_page_width(self, target_page_width):
        if self.page_width > target_page_width:
            self.decrease_page_width(target_page_width)

        elif self.page_width < target_page_width:
            self.increase_page_width(target_page_width)

        self.page_width = target_page_width

        return


    def increase_page_width(self, target_page_width):

        width_diff = target_page_width - self.page_width

        excess_color_array = np.zeros((self.page_height, width_diff, 3), dtype="uint8")
        self.orig_image = np.concatenate([self.orig_image, excess_color_array], axis=1)

        excess_bin_array = np.zeros((self.page_height, width_diff), dtype="bool")
        self.bin_image = np.concatenate([self.bin_image, excess_bin_array], axis=1)

        return


    def decrease_page_width(self, target_page_width):

        self.orig_image = self.orig_image[:, :target_page_width, :]
        self.bin_image = self.bin_image[:, :target_page_width]

        self.adjust_lims_for_new_page_width(target_page_width)

        return


    def adjust_lims_for_new_page_width(self, target_page_width):

        for sg in self.sg_list:
            sg.adjust_lims_for_new_page_width(target_page_width)

        return


    def offset_row_lims(self, offset):

        for sg in self.sg_list:
            sg.offset_row_lims(offset)

        return


    def show_overlays(self):

        overlay_image = self.orig_image.copy()

        figure = plt.figure()
        ax = plt.gca()
        ax.imshow(overlay_image)

        for sg in self.sg_list:

            top_row = sg.top_lim_row
            bottom_row = sg.bottom_lim_row

            if sg.num_bars > 0:
                for bar_idx, bar in enumerate(sg.bar_list):
                    left_col = bar.inner_left_col
                    right_col = bar.inner_right_col

                    if (bar_idx % 2) == 0:
                        curr_color = BAR_OVERLAY_EVEN_COLOR
                    else:
                        curr_color = BAR_OVERLAY_ODD_COLOR

                    curr_bar_overlay = patches.Rectangle((left_col - 1, top_row - 1),
                                                         right_col - left_col + 1,
                                                         bottom_row - top_row + 1,
                                                         color=curr_color,
                                                         alpha=BAR_OVERLAY_ALPHA)
                    ax.add_patch(curr_bar_overlay)

            else:
                if sg.left_lim_col is None:
                    left_col = 0
                else:
                    left_col = sg.left_lim_col

                if sg.right_lim_col is None:
                    right_col = self.page_width - 1
                else:
                    right_col = sg.right_lim_col

                curr_sg_overlay = patches.Rectangle((left_col-1, top_row-1),
                                                    right_col-left_col + 1,
                                                    bottom_row-top_row + 1,
                                                    color=SG_OVERLAY_COLOR,
                                                    alpha=SG_OVERLAY_ALPHA)
                ax.add_patch(curr_sg_overlay)

        plt.show()
        plt.close()

        return



def binarize_image(sample_img, thresh):
    sample_grayscale_img = (rgb2gray(sample_img) * 255).astype("uint8")
    sample_bin_img = sample_grayscale_img <= thresh
    return sample_bin_img



def combine_pages_into_one_page(single_page_obj_list,
                                target_page_width,
                                single_page_image_folder,
                                combined_page_image_folder):

    new_single_page_image_list = []
    new_single_page_obj_list = []
    running_height = 0

    for page_obj in single_page_obj_list:
        curr_page_obj = Page.make_object_from_dict(single_page_image_folder,
                                                   page_obj.to_dict())
        orig_width = curr_page_obj.page_width
        orig_height = curr_page_obj.page_height

        if orig_width != target_page_width:
            curr_page_obj.adjust_page_width(target_page_width)

        curr_page_obj.offset_row_lims(running_height)

        new_single_page_image_list.append(curr_page_obj.orig_image)
        new_single_page_obj_list.append(curr_page_obj)

        running_height += orig_height


    combined_image = np.concatenate(new_single_page_image_list, axis=0)
    combined_image_filepath = os.path.join(combined_page_image_folder, "combined_page.png")
    imwrite(combined_image_filepath,
            combined_image)

    combined_page_obj = Page(combined_image_filepath)
    for new_single_page_obj in new_single_page_obj_list:
        for new_sg in new_single_page_obj.sg_list:
            combined_page_obj.add_stave_group(new_sg)


    return combined_page_obj
