# OMR Scanner - OpenCV

An **Optical Mark Recognition (OMR)** system built with Python and OpenCV. Automatically grades multiple-choice answer sheets from scanned images.

## Features

- Detects and grades filled bubbles from scanned answer sheets
- Handles skew correction and perspective transform
- Outputs scores and per-question results
- Works with standard A4 OMR sheets

## Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy&logoColor=white)

## Getting Started

```bash
git clone https://github.com/sh00von/omr-opencv
cd omr-opencv
pip install -r requirements.txt
python main.py --image path/to/sheet.jpg
```

## License

MIT
