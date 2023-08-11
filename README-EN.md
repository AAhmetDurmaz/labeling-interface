# Image Labeling Interface

This project includes a simple PyQt5 based interface for marking pictures and storing data. Users can mark images as "Yes" or "No", the marked data is saved in a SQLite database and the name, group ID and marking status entered by the users are stored.

## Requirements

- Python 3.x
- PyQt5
- SQLite3

You can use the following commands to install the necessary libraries:

```
pip install PyQt5
```

## Usage

- There is a field where you need to enter your name and surname.
- You can choose from group IDs such as "ACİL", "RADYOLOJİ", "PEDİATRİ", "KBB".
- You can mark the pictures by clicking the "Yes" or "No" buttons.
- The pictures and data you have marked are saved in the SQLite database.
- When you select the image before marking, the image preview is displayed.

## Licence

This project is licensed under the [MIT Licence](LICENSE).