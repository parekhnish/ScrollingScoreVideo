from skimage.color import rgb2gray

import matplotlib.pyplot as plt
import matplotlib.patches as patches


SG_OVERLAY_COLOR = "teal"
SG_OVERLAY_ALPHA = 0.3


class Page:

    def __init__(self, orig_image,
                 sg_list=None):

        self.orig_image = orig_image
        self.bin_image = binarize_image(self.orig_image, thresh=254)

        self.page_height = self.orig_image.shape[0]
        self.page_width = self.orig_image.shape[1]

        if sg_list is None:
            self.sg_list = []
        else:
            self.sg_list = sg_list

        self.num_sg = 0

        return

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

            if sg.left_lim_col is None:
                left_col = 0
            else:
                left_col = sg.left_lim_col

            if sg.right_lim_col is None:
                right_col = self.page_width - 1
            else:
                right_col = sg.right_lim_col

            top_row = sg.top_lim_row
            bottom_row = sg.bottom_lim_row

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
