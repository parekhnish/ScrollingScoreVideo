import time

import numpy as np
import scipy.interpolate as spinterp
import skimage.draw as skdraw

from hsluv import rgb_to_hsluv, hsluv_to_rgb



class BaseFilter:

    def __init__(self,
                 parent_viz_bar,
                 relative_beat_str_list):

        self.parent_viz_bar = parent_viz_bar
        self.relative_beat_str_list = relative_beat_str_list

        self.total_musical_frames = int(self.parent_viz_bar.musical_end_frame -
                                        self.parent_viz_bar.musical_start_frame + 1)

        self.frame_anchor_list = sorted([self.frame_from_relative_beat_string(b_str)
                                         for b_str in self.relative_beat_str_list])

        return


    def frame_from_relative_beat_string(self, beat_str):

        split_str = beat_str.split("/")
        num = float(split_str[0])
        den = float(split_str[1])

        relative_frame = ((num-1)/den) * self.total_musical_frames
        absolute_frame = int(round(self.parent_viz_bar.musical_start_frame + relative_frame))

        return absolute_frame


    def apply_filter(self, color_image, opacity_image, frame_number):
        # NOTE:
        # Since this is the base class, this function does nothing; it just
        # serves as a placeholder for the function definition. In practice,
        # it should be overridden by the actual child class
        return




class FilterOpacityRoundedRectangle(BaseFilter):

    def __init__(self,
                 parent_viz_bar,
                 relative_beat_str_list,
                 circle_radius_ratio):

        super().__init__(parent_viz_bar,
                         relative_beat_str_list)

        self.relative_beat_str_list = relative_beat_str_list
        self.circle_radius_ratio = circle_radius_ratio


        self.mask = self.configure_mask()
        self.is_filter_active_func = self.configure_filter_valid_func()

        return


    def configure_mask(self):

        mask = np.ones((self.parent_viz_bar.bar_height, self.parent_viz_bar.bar_width), dtype="bool")
        actual_circle_radius = int(round(self.parent_viz_bar.bar_height * self.circle_radius_ratio))
        circle_coords_tl_rr, circle_coords_tl_cc = skdraw.circle(actual_circle_radius - 1, actual_circle_radius - 1,
                                                                 actual_circle_radius)

        circle_coords_bl_rr = circle_coords_tl_rr + self.parent_viz_bar.bar_height - (2 * actual_circle_radius) + 1
        circle_coords_bl_cc = circle_coords_tl_cc.copy()

        circle_coords_br_rr = circle_coords_bl_rr.copy()
        circle_coords_br_cc = circle_coords_bl_cc + self.parent_viz_bar.bar_width - (2 * actual_circle_radius) + 1

        circle_coords_tr_rr = circle_coords_tl_rr.copy()
        circle_coords_tr_cc = circle_coords_br_cc.copy()

        all_circle_coords_rr = np.concatenate((circle_coords_tl_rr, circle_coords_bl_rr, circle_coords_br_rr, circle_coords_tr_rr))
        all_circle_coords_cc = np.concatenate((circle_coords_tl_cc, circle_coords_bl_cc, circle_coords_br_cc, circle_coords_tr_cc))

        mask[all_circle_coords_rr, all_circle_coords_cc] = False
        mask[actual_circle_radius - 1: self.parent_viz_bar.bar_height - actual_circle_radius + 1, :] = False
        mask[:, actual_circle_radius - 1: self.parent_viz_bar.bar_width - actual_circle_radius + 1] = False

        return mask


    def configure_filter_valid_func(self):

        bool_array = []
        for idx in range(len(self.frame_anchor_list)):
            if (idx % 2) == 0:
                bool_array.append(True)
            else:
                bool_array.append(False)

        func = spinterp.interp1d(self.frame_anchor_list, bool_array,
                                 kind="previous",
                                 bounds_error=False,
                                 fill_value=(False, bool_array[-1]))

        return func


    def apply_filter(self, color_image, opacity_image, frame_number):

        if bool(self.is_filter_active_func(frame_number)):
            opacity_image[self.mask] = 0.0

        return


################################################################################
################################################################################
################################################################################

class FilterSmoothColorAndOpacity(BaseFilter):

    def __init__(self,
                 parent_viz_bar,
                 relative_beat_str_list,
                 color_hex_str_list,
                 opacity_list):

        super().__init__(parent_viz_bar,
                         relative_beat_str_list)


        self.rgb_array_list, self.hsluv_array_list = self.convert_hex_color_strings_to_rgb_and_hsluv_arrays(color_hex_str_list)

        (self.color_h_interp_func,
         self.color_s_interp_func,
         self.color_l_interp_func) = self.configure_color_interp_func()



        self.opacity_list = opacity_list
        self.opacity_interp_func = self.configure_opacity_interp_func()

        return


    @staticmethod
    def convert_hex_color_strings_to_rgb_and_hsluv_arrays(color_hex_str_list):

        rgb_array_list = []
        hsluv_array_list = []

        for hex_color_str in color_hex_str_list:

            # Remove leading '#', if any
            hex_color_str = hex_color_str.lstrip("#")

            r = int(hex_color_str[0:2], 16)
            g = int(hex_color_str[2:4], 16)
            b = int(hex_color_str[4:6], 16)

            rgb_array = np.array([r, g, b], dtype="uint8").reshape((1, 1, 3))
            rgb_array_list.append(rgb_array)

            hsluv_tuple = rgb_to_hsluv((r/255.0, g/255.0, b/255.0))
            hsluv_array = np.array([hsluv_tuple[0], hsluv_tuple[1], hsluv_tuple[2]], dtype="float").reshape((1, 1, 3))
            hsluv_array_list.append(hsluv_array)


        return rgb_array_list, hsluv_array_list


    def configure_color_interp_func(self):

        h_func = spinterp.interp1d(self.frame_anchor_list, [c[0, 0, 0] for c in self.hsluv_array_list],
                                   kind="linear",
                                   bounds_error=False,
                                   fill_value=(self.hsluv_array_list[0][0, 0, 0], self.hsluv_array_list[-1][0, 0, 0]))

        s_func = spinterp.interp1d(self.frame_anchor_list, [c[0, 0, 1] for c in self.hsluv_array_list],
                                   kind="linear",
                                   bounds_error=False,
                                   fill_value=(self.hsluv_array_list[0][0, 0, 1], self.hsluv_array_list[-1][0, 0, 1]))

        l_func = spinterp.interp1d(self.frame_anchor_list, [c[0, 0, 2] for c in self.hsluv_array_list],
                                   kind="linear",
                                   bounds_error=False,
                                   fill_value=(self.hsluv_array_list[0][0, 0, 2], self.hsluv_array_list[-1][0, 0, 2]))

        return h_func, s_func, l_func


    def configure_opacity_interp_func(self):

        func = spinterp.interp1d(self.frame_anchor_list, self.opacity_list,
                                 kind="linear",
                                 bounds_error=False,
                                 fill_value=(self.opacity_list[0], self.opacity_list[-1]))

        return func


    def apply_filter(self, color_image, opacity_image, frame_number):

        curr_opacity = self.opacity_interp_func(frame_number)

        curr_h = self.color_h_interp_func(frame_number)
        curr_s = self.color_s_interp_func(frame_number)
        curr_l = self.color_l_interp_func(frame_number)

        curr_rgb_tuple = hsluv_to_rgb((curr_h, curr_s, curr_l))
        curr_rgb_array = np.clip(np.array([curr_rgb_tuple[0], curr_rgb_tuple[1], curr_rgb_tuple[2]]) * 255, 0, 255).astype("uint8").reshape((1, 1, 3))

        opacity_image[:, :] = curr_opacity
        color_image[:, :, 0] = curr_rgb_array[0, 0, 0]
        color_image[:, :, 1] = curr_rgb_array[0, 0, 1]
        color_image[:, :, 2] = curr_rgb_array[0, 0, 2]

        return


################################################################################
################################################################################
################################################################################

class FilterRandomOpacityHoles(BaseFilter):

    def __init__(self,
                 parent_viz_bar,
                 relative_beat_str_list,
                 opacity_list,
                 hole_radius_ratio,
                 random_seed=None):

        super().__init__(parent_viz_bar,
                         relative_beat_str_list)

        self.opacity_list = opacity_list
        self.hole_radius_ratio = hole_radius_ratio

        self.num_holes = len(self.relative_beat_str_list) - 1

        if random_seed is None:
            self.random_seed = int(time.time())
        else:
            self.random_seed = random_seed

        self.hole_index_func = self.configure_hole_index_func()
        self.hole_mask_list = self.configure_hole_mask_list()



        return


    def configure_hole_index_func(self):

        hole_index_list = list(range(self.num_holes + 1))

        index_func = spinterp.interp1d(self.frame_anchor_list, hole_index_list,
                                       kind="previous",
                                       bounds_error=False,
                                       fill_value=(-1, self.num_holes))

        return index_func


    def configure_hole_mask_list(self):

        hole_radius = int(round(self.parent_viz_bar.bar_height * self.hole_radius_ratio))

        hole_mask_list = [np.zeros((self.parent_viz_bar.bar_height, self.parent_viz_bar.bar_width), dtype="bool")
                          for _ in range(self.num_holes)]

        prng = np.random.default_rng(self.random_seed)
        self.hole_center_r_list = (prng.random((self.num_holes,)) * self.parent_viz_bar.bar_height).astype("int")
        self.hole_center_c_list = (prng.random((self.num_holes,)) * self.parent_viz_bar.bar_width).astype("int")

        for i in range(self.num_holes):
            circle_coords_rr, circle_coords_cc = skdraw.circle(self.hole_center_r_list[i], self.hole_center_c_list[i],
                                                               hole_radius,
                                                               shape=(self.parent_viz_bar.bar_height, self.parent_viz_bar.bar_width))

            hole_mask_list[i][circle_coords_rr, circle_coords_cc] = True

        return hole_mask_list


    def apply_filter(self, color_image, opacity_image, frame_number):

        curr_hole_index = int(np.floor(self.hole_index_func(frame_number)))

        if curr_hole_index < 0:
            return
        if curr_hole_index >= self.num_holes:
            return

        curr_hole_opacity_mult = self.opacity_list[curr_hole_index]
        curr_hole_mask = self.hole_mask_list[curr_hole_index]

        opacity_image[curr_hole_mask] = opacity_image[curr_hole_mask] * curr_hole_opacity_mult

        return


# ------------------------------------------------------------------------------
# Declare all names here for reference
ALL_FILTERS_DICT = {
    "BaseFilter": BaseFilter,
    "FilterOpacityRoundedRectangle": FilterOpacityRoundedRectangle,
    "FilterSmoothColorAndOpacity": FilterSmoothColorAndOpacity,
    "FilterRandomOpacityHoles": FilterRandomOpacityHoles
}
# ------------------------------------------------------------------------------
