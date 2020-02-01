import subprocess
import os

import numpy as np
import imageio


def get_page_size(input_pdf_filepath):

    width = None
    height = None

    # Run the `pdfinfo` program on the given PDF file, and return if there are
    # any errors
    proc_obj = subprocess.run(["pdfinfo", input_pdf_filepath],
                              capture_output=True)
    if proc_obj.returncode != 0:
        print("Error when running `pdfinfo` on given PDF")
        return width, height

    # Make a list from the `pdfinfo` output lines
    info_list = proc_obj.stdout.decode("utf-8").split("\n")

    # Loop over each line ...
    for line in info_list:

        # ... find the line that says "Page size"
        if "Page size" in line:

            # Split the line into tokens, and iterate throught them
            tokens = line.split()
            for idx, t in enumerate(tokens):

                # We are looking for a string that matches the pattern:
                # "<width> x <height>"; thus, by searching for the token "x",
                # we can extract this data
                if t == "x":
                    width = int(tokens[idx-1])
                    height = int(tokens[idx+1])
                    break

    if (width is None) or (height is None):
        print("Could not get original page height and width")

    return height, width


def convert_pdf_to_single_page_images(input_pdf_filepath,
                                      output_page_width_px,
                                      temp_output_dir,
                                      single_page_prefix="single_page"):

    single_page_image_fp_list = None

    # Note: `pdfinfo` returns height and width in points
    orig_height, orig_width = get_page_size(input_pdf_filepath)

    # Calculate output resolution of pdf-to-image conversion
    # 72 pixels = 1 inch; that's the PDF standard
    new_resolution = (output_page_width_px * 72.0) / float(orig_width)

    # Run the `pdftocairo` program on the given PDF with the calculated
    # resolution
    proc_obj = subprocess.run(["pdftocairo", "-png",
                               "-r", str(new_resolution),
                               input_pdf_filepath,
                               os.path.join(temp_output_dir, single_page_prefix)],
                              capture_output=True)

    # If `pdftocairo` is successful ...
    if proc_obj.returncode == 0:

        # Get the filenames of the produced images.
        # `pdftocairo` output filenames are lexicographically ordered as per
        # the page order of the original PDF, so using Python's regular `sort()`
        # is sufficient
        single_page_fn_list = sorted([fn for fn in os.listdir(temp_output_dir)
                                      if fn.startswith(single_page_prefix)])

        single_page_image_fp_list = [os.path.join(temp_output_dir, fn)
                                     for fn in single_page_fn_list]

    else:
        print("Error when running `pdfcairo` on given PDF")


    return single_page_image_fp_list


def concatenate_single_page_images(image_fp_list,
                                   output_page_width_px):

    list_of_images = []

    # For each image:
    #     Read it from disk
    #     Crop/Expand it to conform to the `output_page_width_px` shape
    #     Add it to the list
    for fp in image_fp_list:
        raw_image = imageio.imread(fp)
        raw_width = raw_image.shape[1]

        # If raw width is larger, crop the rightmost column(s)
        if raw_width > output_page_width_px:
            num_extra = raw_width - output_page_width_px
            raw_image = raw_image[:, :-num_extra, :]

        # If raw width is smaller, replicate the rightmost column(s)
        if raw_width < output_page_width_px:
            num_extra = output_page_width_px - raw_width
            rightmost_col = np.expand_dims(raw_image[:, -1, :], axis=1)
            replicated_rightmost_col = np.tile(rightmost_col, (1, num_extra, 1))
            raw_image = np.concatenate([raw_image, replicated_rightmost_col], axis=1)

        list_of_images.append(raw_image)


    # Concatenate the images, vertically, to form one giant image
    concat_image = np.concatenate(list_of_images, axis=0)

    return concat_image
