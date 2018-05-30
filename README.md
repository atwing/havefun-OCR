# havefun-OCR
OCR for E&amp;P by Have Fun, written in Python 3  

## Required tools
- Python 3
- Pytesser https://github.com/RobinDavid/Pytesser (tesseract OCR engine)
- Premium membership in Have Fun alliance

## Usage
1. $ python3 main.py \<path-to-image>/\<image>
2. $ python3 main.py -s \<path-to-previous-output-file>

#### Other operating modes
###### Process image batch (example processes images 1.png, 2.png, 3.png)
$ for i in {1..3}; do python3 main.py \<path-to-image>/$i.png; done
###### Overwrite previous output (does not work with batch mode yet)
$ python3 main.py -w \<path-to-image>/\<image>

## Notes
Works best on PNG files. Don't use lossy formats such as JPEG.