import cv2
import numpy as np

def preprocess_image(image_path, grayscale_output="grayscale_omr.png", binary_output="binary_omr.png"):
    """Loads an image, converts it to grayscale, applies Gaussian blur, and applies a fixed threshold."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Error: Could not load image from path: {image_path}")

    cv2.imwrite(grayscale_output, img)
    blurred_img = cv2.GaussianBlur(img, (5, 5), 0)
    _, binary_img = cv2.threshold(blurred_img, 40, 255, cv2.THRESH_BINARY_INV)
    cv2.imwrite(binary_output, binary_img)
    return binary_img

def detect_filled_bubbles(img_thresh, sections, img_shape):
    """
    Detects filled bubbles based on predefined sections and unique fill ratio per section.
    For each section, it records tuples of the form (question_number, option).
    """
    height, width = img_shape
    filled_bubbles = {}

    for section_name, x1_perc, x2_perc, y1_perc, y2_perc, options, num_questions, min_fill_ratio in sections:
        x1 = int(x1_perc / 100 * width)
        x2 = int(x2_perc / 100 * width)
        y1 = int(y1_perc / 100 * height)
        y2 = int(y2_perc / 100 * height)
        row_height = (y2 - y1) / num_questions
        col_width = (x2 - x1) / len(options)

        for q in range(num_questions):
            for o, option in enumerate(options):
                cx1 = int(x1 + o * col_width)
                cx2 = int(x1 + (o + 1) * col_width)
                cy1 = int(y1 + q * row_height)
                cy2 = int(y1 + (q + 1) * row_height)
                cell = img_thresh[cy1:cy2, cx1:cx2]
                total_pixels = cell.size
                black_pixels = np.sum(cell == 255)
                fill_ratio = black_pixels / total_pixels
                if fill_ratio > min_fill_ratio:
                    filled_bubbles.setdefault(section_name, []).append((q + 1, option))
    return filled_bubbles

def draw_detected_areas(image, filled_bubbles, sections, img_shape):
    """Draws bounding boxes around detected filled bubbles and overlays grid lines."""
    height, width = img_shape

    for section_name, x1_perc, x2_perc, y1_perc, y2_perc, options, num_questions, _ in sections:
        x1 = int(x1_perc / 100 * width)
        x2 = int(x2_perc / 100 * width)
        y1 = int(y1_perc / 100 * height)
        y2 = int(y2_perc / 100 * height)
        row_height = (y2 - y1) / num_questions
        col_width = (x2 - x1) / len(options)

        for q in range(num_questions):
            for o, option in enumerate(options):
                cx1 = int(x1 + o * col_width)
                cx2 = int(x1 + (o + 1) * col_width)
                cy1 = int(y1 + q * row_height)
                cy2 = int(y1 + (q + 1) * row_height)
                cv2.rectangle(image, (cx1, cy1), (cx2, cy2), (255, 0, 0), 1)
                if (q + 1, option) in filled_bubbles.get(section_name, []):
                    cv2.rectangle(image, (cx1, cy1), (cx2, cy2), (0, 255, 0), 2)
    return image

def scan_omr(image_path, output_path="scanned_omr.png", show=False):
    """Processes an OMR sheet, detects filled bubbles, and saves the scanned result."""
    sections = [
        # (Section name, x1%, x2%, y1%, y2%, options, number of questions, min fill ratio)
        ("MCQ Section 1", 8, 24, 19, 90.5, ["A", "B", "C", "D"], 25, 0.05),
        ("MCQ Section 2", 31, 46.5, 19, 90.5, ["A", "B", "C", "D"], 25, 0.05),
        ("Roll Number", 49, 61.5, 24, 38.5, list(range(1, 7)), 10, 0.3),
        ("Registration", 49, 61.5, 45.5, 60.2, list(range(1, 7)), 10, 0.3),
        ("Subject Code", 67.5, 74, 45.5, 60.2, list(range(1, 4)), 10, 0.25),
        ("Set Code", 67.5, 74, 24, 34, ["Set"], 4, 0.01),
    ]

    original_img = cv2.imread(image_path)
    if original_img is None:
        raise ValueError(f"Error: Unable to read image at path {image_path}")
    img_thresh = preprocess_image(image_path)
    filled_bubbles = detect_filled_bubbles(img_thresh, sections, img_thresh.shape)
    result_img = draw_detected_areas(original_img, filled_bubbles, sections, img_thresh.shape)
    cv2.imwrite(output_path, result_img)
    print(f"Scanned OMR saved as {output_path}")
    if show:
        cv2.imshow("Scanned OMR", result_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return filled_bubbles

def process_missing_section(filled_bubbles, section_name, expected_columns):
    """
    For sections like Roll Number, Registration, and Subject Code,
    ensure that for each expected column there is one answer.
    If a column is missing, insert (None, 'X').
    Then, sort by the column number (second element).
    """
    detected = filled_bubbles.get(section_name, [])
    # Create a dictionary: key = column number, value = tuple (question, column)
    mapping = {}
    for tup in detected:
        question, col = tup
        # If multiple entries for the same column exist, choose the one with the smallest question number.
        if col in mapping:
            if question < mapping[col][0]:
                mapping[col] = tup
        else:
            mapping[col] = tup

    result = []
    for col in expected_columns:
        if col in mapping:
            result.append(mapping[col])
        else:
            result.append((None, 'X'))
    # Sorting by the column (expected_columns order is already sorted)
    return result

if __name__ == "__main__":
    try:
        results = scan_omr("omr.jpg", "scanned_omr.png", show=False)

        # For Roll Number, Registration, and Subject Code, sort by the column (second element)
        # Expected columns:
        expected_roll = list(range(1, 7))
        expected_reg  = list(range(1, 7))
        expected_subj = list(range(1, 4))

        processed_roll = process_missing_section(results, "Roll Number", expected_roll)
        processed_reg  = process_missing_section(results, "Registration", expected_reg)
        processed_subj = process_missing_section(results, "Subject Code", expected_subj)

        print("OMR Results:")
        # Print MCQ sections as detected (unchanged order)
        for section in ["MCQ Section 1", "MCQ Section 2", "Set Code"]:
            print(f"{section}: {results.get(section, [])}")

        print("\nRoll Number (sorted by column and with missing replaced by X):")
        print(processed_roll)
        print("\nRegistration (sorted by column and with missing replaced by X):")
        print(processed_reg)
        print("\nSubject Code (sorted by column and with missing replaced by X):")
        print(processed_subj)

    except Exception as e:
        print(f"Error: {e}")
