import json

import numpy as np
import scipy.interpolate as spinterp
import skimage.color as skcolor

from staveUtils import VizStaveGroup
from barUtils import VizBar


class CurrPagePosition:

    def __init__(self,
                 page_height,
                 window_height,
                 viz_sg_top_row_indices,
                 viz_sg_top_row_frames):

        self.furthest_row_index = page_height - window_height
        self.raw_interp_func = spinterp.interp1d(viz_sg_top_row_frames, viz_sg_top_row_indices,
                                                 kind="linear")

        return


    def get_curr_top_row_position(self, frame_index):
        return int(min(self.raw_interp_func(frame_index), self.furthest_row_index))




class FullSizeImageIterator:

    def __init__(self,
                 full_page_image,
                 viz_bar_list,
                 start_frame, end_frame):

        self.viz_bar_list = viz_bar_list
        self.num_bars = len(self.viz_bar_list)

        self.start_frame = start_frame
        self.end_frame = end_frame

        self.curr_valid_bar_indices = []
        self.update_curr_valid_bar_indices(self.start_frame, search_all=True)

        self.full_background_image = full_page_image.copy()

        self.black_portions_bool_image = (skcolor.rgb2gray(self.full_background_image) * 255) < 32

        self.full_overlay_color_image = np.zeros(self.full_background_image.shape, dtype="uint8")
        self.full_overlay_opacity_image = np.zeros((self.full_background_image.shape[0],
                                                    self.full_background_image.shape[1],
                                                    1), dtype="float")

        self.full_output_image = ((self.full_overlay_opacity_image * self.full_overlay_color_image) +
                                  ((1.0 - self.full_overlay_opacity_image) * self.full_background_image)).astype("uint8")



        return


    def update_curr_valid_bar_indices(self, frame_index,
                                      search_all=False):

        if len(self.curr_valid_bar_indices) == 0:
            search_start_idx = 0
        else:
            search_start_idx = self.curr_valid_bar_indices[-1] + 1

        for b_idx in range(search_start_idx, self.num_bars):
            b = self.viz_bar_list[b_idx]
            if (frame_index >= b.actual_start_frame) and (frame_index <= b.actual_end_frame):
                self.curr_valid_bar_indices.append(b_idx)
            else:
                if search_all:
                    continue
                else:
                    break


        for b_idx in self.curr_valid_bar_indices:
            b = self.viz_bar_list[b_idx]
            if (frame_index < b.actual_start_frame) or (frame_index > b.actual_end_frame):
                self.curr_valid_bar_indices.remove(b_idx)
            else:
                if search_all:
                    continue
                else:
                    break

        return



    def update_images(self, frame_index):

        for b_idx in self.curr_valid_bar_indices:
            b = self.viz_bar_list[b_idx]

            tr = b.bar_top_row
            br = b.bar_bottom_row
            lc = b.bar_left_col
            rc = b.bar_right_col

            corresponding_bg_image = self.full_background_image[tr: br+1,
                                                                lc: rc+1]

            corresponding_black_portions_bool_image = self.black_portions_bool_image[tr: br+1,
                                                                                     lc: rc+1]

            bar_color_image, bar_opacity_image = b.get_bar_image_at_frame(frame_index)

            bar_opacity_image[corresponding_black_portions_bool_image] = 0.0
            bar_opacity_image = bar_opacity_image[..., np.newaxis]


            self.full_overlay_color_image[tr: br+1,
                                          lc: rc+1] = bar_color_image

            self.full_overlay_opacity_image[tr: br+1,
                                            lc: rc+1] = bar_opacity_image

            self.full_output_image[tr: br+1,
                                   lc: rc+1] = ((bar_opacity_image * bar_color_image) +
                                                ((1.0 - bar_opacity_image) * corresponding_bg_image)).astype("uint8")

        return


    def __iter__(self):
        for frame_index in range(self.start_frame, self.end_frame+1):
            self.update_curr_valid_bar_indices(frame_index, search_all=False)
            self.update_images(frame_index)

            yield frame_index

        return



def create_viz_items(page_obj,
                     fps,
                     bar_start_timestamp_array,
                     filter_list_filename):

    num_sg = page_obj.num_sg

    all_viz_sg_list = []
    all_viz_bar_list = []

    running_bar_index = 0

    for sg_idx in range(num_sg):
        orig_sg_obj = page_obj.sg_list[sg_idx]

        if sg_idx == 0:
            offset_bottom_row = int((page_obj.sg_list[sg_idx+1].top_lim_row - orig_sg_obj.bottom_lim_row) / 2)
            offset_top_row = min(offset_bottom_row,
                                 orig_sg_obj.top_lim_row)

        elif sg_idx == (num_sg-1):
            offset_top_row = int((orig_sg_obj.top_lim_row - page_obj.sg_list[sg_idx-1].bottom_lim_row) / 2)
            offset_bottom_row = min(offset_top_row,
                                    page_obj.page_height - orig_sg_obj.bottom_lim_row - 1)

        else:
            offset_top_row = int((orig_sg_obj.top_lim_row - page_obj.sg_list[sg_idx-1].bottom_lim_row) / 2)
            offset_bottom_row = int((page_obj.sg_list[sg_idx+1].top_lim_row - orig_sg_obj.bottom_lim_row) / 2)

        viz_sg_obj = VizStaveGroup(orig_sg_obj,
                                   offset_top_row, offset_bottom_row)

        curr_num_bars = orig_sg_obj.num_bars
        for curr_bar_idx in range(curr_num_bars):
            curr_orig_bar_obj = orig_sg_obj.bar_list[curr_bar_idx]


            curr_bar_musical_start_time = bar_start_timestamp_array[running_bar_index]
            curr_bar_musical_end_time = bar_start_timestamp_array[running_bar_index + 1]

            curr_bar_musical_start_frame = int(curr_bar_musical_start_time * fps)
            curr_bar_musical_end_frame = int(curr_bar_musical_end_time * fps) - 1

            curr_viz_bar_obj = VizBar(curr_orig_bar_obj,
                                      curr_bar_musical_start_frame, curr_bar_musical_end_frame)


            viz_sg_obj.add_viz_bar(curr_viz_bar_obj)
            all_viz_bar_list.append(curr_viz_bar_obj)

            running_bar_index += 1


        all_viz_sg_list.append(viz_sg_obj)


    # --------------------------------------------------------------------------
    # INIT FILTERS
    with open(filter_list_filename, "r") as fp:
        all_filter_dict_list = json.load(fp)


    for curr_viz_bar_obj, curr_filter_list_dict in zip(all_viz_bar_list, all_filter_dict_list):
        curr_filter_list = curr_filter_list_dict["filter_list"]
        for f in curr_filter_list:
            if f["name"] == "RoundedRectangle":
                del f["name"]
                curr_viz_bar_obj.add_filter_obj("FilterOpacityRoundedRectangle",
                                                f)

            elif f["name"] == "FilterSmoothColorAndOpacity":
                del f["name"]
                curr_viz_bar_obj.add_filter_obj("FilterSmoothColorAndOpacity",
                                                f)

            elif f["name"] == "FilterRandomOpacityHoles":
                del f["name"]
                curr_viz_bar_obj.add_filter_obj("FilterRandomOpacityHoles",
                                                f)
    # --------------------------------------------------------------------------



    return all_viz_sg_list, all_viz_bar_list
