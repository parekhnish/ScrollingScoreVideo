import os

from skimage.color import rgb2gray
from imageio import imread
import matplotlib.pyplot as plt
import matplotlib.patches as patches


SG_OVERLAY_COLOR = "teal"
SG_OVERLAY_ALPHA = 0.3

BAR_OVERLAY_EVEN_COLOR = "mediumorchid"
BAR_OVERLAY_ODD_COLOR = "seagreen"
BAR_OVERLAY_ALPHA = 0.25



class Page:

    def __init__(self, orig_image_filepath,
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

        self.num_sg = 0

        return


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
