import sys
import sqlite3
import os
import datetime
from PyQt5.QtCore import Qt, pyqtSlot, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QTransform, QIcon
from PyQt5.QtWidgets import QAbstractItemView, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView, QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QRadioButton, QHeaderView, QLabel, QDialog, QMessageBox


def get_image_paths(folder):
    image_paths = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                image_path = os.path.join(root, file)
                image_paths.append(image_path)
    return image_paths


class ImageWindow(QDialog):
    factor = 1.5

    def __init__(self, parent=None):
        super().__init__(parent)
        global sqlcursor
        global connection

        self.setWindowTitle("Resim Penceresi")
        self.setWindowIcon(QIcon('icons/icon.ico'))
        self.setGeometry(800, 100, 800, 800)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.selected_corner = None
        self.bounding_box_item = None
        self.points = []
        self.current_image_path = None

        self.scene.setSceneRect(0, 0, 0, 0)

        self.scene.mousePressEvent = self.on_scene_mouse_press

        fullscreen_icon = QPixmap("icons/fullscreen.svg")
        zoom_in_icon = QPixmap("icons/zoom_in.svg")
        zoom_out_icon = QPixmap("icons/zoom_out.svg")
        clear_icon = QPixmap("icons/clear.svg")
        self.fullscreen_button = QPushButton("Tam Ekran", self)
        self.fullscreen_button.setIcon(QIcon(fullscreen_icon))
        self.clear_button = QPushButton("Temizle", self)
        self.clear_button.setIcon(QIcon(clear_icon))
        self.zoom_in_button = QPushButton("Yaklaştır", self)
        self.zoom_in_button.setIcon(QIcon(zoom_in_icon))
        self.zoom_out_button = QPushButton("Uzaklaştır", self)
        self.zoom_out_button.setIcon(QIcon(zoom_out_icon))

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.view)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.fullscreen_button)
        button_layout.addWidget(self.clear_button)
        self.layout.addLayout(button_layout)
        zoom_button_layout = QHBoxLayout()
        zoom_button_layout.addWidget(self.zoom_in_button)
        zoom_button_layout.addWidget(self.zoom_out_button)
        self.layout.addLayout(zoom_button_layout)

        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.clear_button.clicked.connect(self.clear_labelings)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.is_fullscreen = False
        self.scale_factor = 1.0


    def clear_labelings(self, event):
        sqlcursor.execute("UPDATE veriler SET x1=NULL, y1=NULL, x2=NULL, y2=NULL WHERE image_path=?", (self.current_image_path,))
        connection.commit()

        self.bounding_box_item = None
        self.update_image(self.current_image_path)


    @pyqtSlot()
    def zoom_in(self):
        scale_tr = QTransform()
        scale_tr.scale(ImageWindow.factor, ImageWindow.factor)

        tr = self.view.transform() * scale_tr
        self.view.setTransform(tr)

    @pyqtSlot()
    def zoom_out(self):
        scale_tr = QTransform()
        scale_tr.scale(1 / ImageWindow.factor, 1 / ImageWindow.factor)

        tr = self.view.transform() * scale_tr
        self.view.setTransform(tr)

    def update_image(self, path, x1=None, y1=None, x2=None, y2=None):
        pixmap = QPixmap(path)
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.view.setTransform(QTransform())
        self.current_image_path = path
        
        if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
            corner1 = QPointF(x1, y1)
            corner2 = QPointF(x2, y2)
            self.draw_bounding_box(corner1, corner2, save=False)
        
        self.view.viewport().update()

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showFullScreen()
            self.fullscreen_button.setText("Küçült")
        else:
            self.showNormal()
            self.fullscreen_button.setText("Tam Ekran")
        self.is_fullscreen = not self.is_fullscreen

    def on_scene_mouse_press(self, event):
        if event.button() == Qt.RightButton:
            pos = event.scenePos()

            if self.bounding_box_item is not None:
                self.add_point(pos, Qt.GlobalColor.red)
                self.bounding_box_item = None
            if self.selected_corner is None:
                self.add_point(pos, Qt.GlobalColor.red)
                self.selected_corner = pos
            else:
                self.draw_bounding_box(self.selected_corner, pos, save=True)
                self.selected_corner = None

    def draw_bounding_box(self, corner1, corner2, save: bool):
        rect = QRectF(corner1, corner2)

        self.bounding_box_item = QGraphicsRectItem(rect)
        self.scene.addItem(self.bounding_box_item)

        self.add_point(corner1, Qt.GlobalColor.green)
        self.add_point(corner2, Qt.GlobalColor.green)

        if save:
            self.save_bbox(corner1, corner2, self.current_image_path)
            self.update_image(self.current_image_path, corner1.x(), corner1.y(), corner2.x(), corner2.y())
        self.view.viewport().update()

    def save_bbox(self, corner1, corner2, image_path):
        global gTableWidget
        sqlcursor.execute("UPDATE veriler SET x1 = ?, y1=?, x2=?, y2=? WHERE image_path = ?", (int(corner1.x()), int(corner1.y()), int(corner2.x()), int(corner2.y()), image_path))
        connection.commit()

        row_count = gTableWidget.rowCount()
        for row in range(row_count):
            item_name = gTableWidget.item(row, 0)
            item_name_text = item_name.text()
            if item_name_text == image_path:
                gTableWidget.setItem(row, 2, QTableWidgetItem("İşaretlendi"))
                gTableWidget.item(row, 2).setBackground(Qt.green)

    def add_point(self, pos, color: Qt.GlobalColor):
        point = QGraphicsEllipseItem(QRectF(pos.x() - 5, pos.y() - 5, 10, 10))
        point.setBrush(color)
        self.scene.addItem(point)
        self.points.append(point)


class SimpleUI(QMainWindow):
    def __init__(self):
        global connection
        global sqlcursor
        global gTableWidget
        super().__init__()

        self.setWindowTitle("Arayüz")
        self.setWindowIcon(QIcon('icons/icon.ico'))
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.label = QLabel("İsim, Soyisim:", self)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("İsim, Soyisim girin")
        try:
            f = open('lastuser.txt', 'r')
            last_name = f.readlines()
            f.close()
            self.name_input.setText(last_name[0])
        except FileNotFoundError:
            pass
        except IndexError:
            os.remove('lastuser.txt')

        self.radio_layout = QHBoxLayout()
        self.radio_label = QLabel("İnceleyen Birim:", self)
        self.radio_layout.addWidget(self.radio_label)
        self.radio_buttons = []
        for label in ["ACİL", "RADYOLOJİ", "PEDİATRİ", "KBB"]:
            radio_button = QRadioButton(label)
            self.radio_buttons.append(radio_button)
            self.radio_layout.addWidget(radio_button)

        self.button_layout = QHBoxLayout()
        self.question_label = QLabel("Nazal Fraktür var mı?", self)
        self.button_layout.addWidget(self.question_label)
        self.yes_button = QPushButton("Evet", self)
        self.no_button = QPushButton("Hayır", self)
        self.button_layout.addWidget(self.yes_button)
        self.button_layout.addWidget(self.no_button)

        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(3)  # 3 sütun ekliyoruz
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setHorizontalHeaderLabels(["İsim", "Durum", "Burun İşaretlemesi"])
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        self.table_widget.setRowCount(0)
        gTableWidget = self.table_widget


        label_and_input_layout = QHBoxLayout()
        label_and_input_layout.addWidget(self.label)
        label_and_input_layout.addWidget(self.name_input)

        lower_layout = QVBoxLayout()
        lower_layout.addLayout(label_and_input_layout)
        lower_layout.addLayout(self.radio_layout)
        lower_layout.addLayout(self.button_layout)
        lower_layout.addWidget(self.table_widget)

        self.layout.addLayout(lower_layout)

        self.yes_button.clicked.connect(self.on_yes_clicked)
        self.no_button.clicked.connect(self.on_no_clicked)
        self.table_widget.cellClicked.connect(self.on_cell_clicked)

        self.image_window = ImageWindow(self)
        self.image_window.show()

        self.create_database()
        self.load_data()

    def closeEvent(self, event):
        self.save_username()
        event.accept()

    def save_username(self):
        username = str(self.name_input.text()).strip()
        if username != '' and username != None:
            f = open('lastuser.txt', 'w')
            f.write(username)
            f.close()

    def update_image(self, path, x1=None, y1=None, x2=None, y2=None):
        self.image_window.update_image(path, x1, y1, x2, y2)

    def on_yes_clicked(self):
        if self.validate_input():
            selected_rows = self.table_widget.selectionModel().selectedRows()
            if len(selected_rows) > 0:
                row = selected_rows[0].row()
                item_name = self.table_widget.item(row, 0)
                item_name_text = item_name.text()
                item_status = self.table_widget.item(row, 1)
                item_status.setText("Evet")
                item_status.setBackground(Qt.green)
                who_labeled = self.name_input.text()
                who_labeled_group_id = ""
                for radio_button in self.radio_buttons:
                    if radio_button.isChecked():
                        who_labeled_group_id = radio_button.text()
                        break
                value = 1
                image_path = item_name_text
                self.save_to_database(
                    who_labeled, who_labeled_group_id, value, image_path)
                self.table_widget.selectRow(row + 1)
                if row + 1 < self.table_widget.rowCount():
                    next_item_name = self.table_widget.item(row + 1, 0)
                    next_item_name_text = next_item_name.text()
                    image_path = next_item_name_text
                    x1, y1, x2, y2 = self.get_bbox_values(image_path)
                    self.update_image(image_path, x1, y1, x2, y2)
                else:
                    self.update_image("", None, None, None, None)

    def on_no_clicked(self):
        if self.validate_input():
            selected_rows = self.table_widget.selectionModel().selectedRows()
            if len(selected_rows) > 0:
                row = selected_rows[0].row()
                item_name = self.table_widget.item(row, 0)
                item_name_text = item_name.text()
                item_status = self.table_widget.item(row, 1)
                item_status.setText("Hayır")
                item_status.setBackground(Qt.green)
                who_labeled = self.name_input.text()
                who_labeled_group_id = ""
                for radio_button in self.radio_buttons:
                    if radio_button.isChecked():
                        who_labeled_group_id = radio_button.text()
                        break
                value = 0
                image_path = item_name_text
                self.save_to_database(
                    who_labeled, who_labeled_group_id, value, image_path)
                self.table_widget.selectRow(row + 1)
                if row + 1 < self.table_widget.rowCount():
                    next_item_name = self.table_widget.item(row + 1, 0)
                    next_item_name_text = next_item_name.text()
                    image_path = next_item_name_text
                    x1, y1, x2, y2 = self.get_bbox_values(image_path)
                    self.update_image(image_path, x1, y1, x2, y2)
                else:
                    self.update_image("", None, None, None, None)

    def on_cell_clicked(self, row, column):
        if column == 0:
            item_name = self.table_widget.item(row, 0)
            item_name_text = item_name.text()
            item_status = self.table_widget.item(row, 1)
            item_status_text = item_status.text()

            if item_status_text != "İşaretlenmedi":
                QMessageBox.warning(self, "Uyarı", "Bu resim daha önce işaretlenmiş, değiştirmek istiyorsanız tekrar işaretleme yapın.")

            image_path = item_name_text
            x1, y1, x2, y2 = self.get_bbox_values(image_path)
            self.update_image(image_path, x1, y1, x2, y2)

    def create_database(self):
        data_folder = "data"

        sqlcursor.execute(f"CREATE TABLE IF NOT EXISTS veriler (id INTEGER PRIMARY KEY, who_labeled TEXT, who_labeled_group_id TEXT, value INTEGER DEFAULT -1, image_path TEXT, created_at DATETIME DEFAULT '{str(datetime.datetime.now())}', updated_at DATETIME DEFAULT NULL, deleted_at DATETIME DEFAULT NULL, x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER)")
        connection.commit()

        image_paths = get_image_paths(data_folder)

        sqlcursor.execute("SELECT image_path FROM veriler WHERE deleted_at IS NULL")
        db_image_paths = [row[0] for row in sqlcursor.fetchall()]

        for db_image_path in db_image_paths:
            if db_image_path not in image_paths:
                sqlcursor.execute(f"UPDATE veriler SET deleted_at = '{str(datetime.datetime.now())}' WHERE image_path = ?", (db_image_path,))
                connection.commit()

        for image_path in image_paths:
            sqlcursor.execute("SELECT * FROM veriler WHERE image_path = ? AND deleted_at IS NULL", (image_path,))
            existing_data = sqlcursor.fetchone()

            if existing_data is None:
                sqlcursor.execute("INSERT INTO veriler (who_labeled, who_labeled_group_id, image_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",("", "", image_path, str(datetime.datetime.now()), str(datetime.datetime.now())))
                connection.commit()

    def load_data(self):
        sqlcursor.execute("SELECT * FROM veriler WHERE deleted_at IS NULL ORDER BY value ASC")
        data = sqlcursor.fetchall()
        for row in data:
            self.add_row_to_table(row)
            if row[8] is not None and row[9] is not None and row[10] is not None and row[11] is not None:
                self.update_image(row[4], row[8], row[9], row[10], row[11])

    def add_row_to_table(self, data):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        item_name = QTableWidgetItem(data[4])
        item_status = QTableWidgetItem("İşaretlenmedi")
        if data[3] == 1:
            item_status.setText("Evet")
            item_status.setBackground(Qt.green)
        elif data[3] == 0:
            item_status.setText("Hayır")
            item_status.setBackground(Qt.green)
        else:
            item_status.setBackground(Qt.yellow)
        self.table_widget.setItem(row_position, 0, item_name)
        self.table_widget.setItem(row_position, 1, item_status)
        if data[8] is not None or data[9] is not None or data[10] is not None or data[11] is not None:
            self.table_widget.setItem(row_position, 2, QTableWidgetItem("İşaretlendi"))
            self.table_widget.item(row_position, 2).setBackground(Qt.green)
        else:
            self.table_widget.setItem(row_position, 2, QTableWidgetItem("İşaretleme Yok"))
            self.table_widget.item(row_position, 2).setBackground(Qt.yellow)

    def save_to_database(self, who_labeled, who_labeled_group_id, value, image_path):
        sqlcursor.execute("UPDATE veriler SET who_labeled = ?, who_labeled_group_id = ?, value = ?, updated_at = ? WHERE image_path = ?", (who_labeled, who_labeled_group_id, value, str(datetime.datetime.now()), image_path))
        connection.commit()

    def get_bbox_values(self, image_path):
        sqlcursor.execute("SELECT x1, y1, x2, y2 FROM veriler WHERE image_path = ?", (image_path,))
        bbox_data = sqlcursor.fetchone()
        if bbox_data:
            return bbox_data
        return None, None, None, None

    def validate_input(self):
        if not self.name_input.text():
            QMessageBox.warning(self, "Uyarı", "İsim girmelisiniz.")
            return False

        group_id_selected = False
        for radio_button in self.radio_buttons:
            if radio_button.isChecked():
                group_id_selected = True
                break
        if not group_id_selected:
            QMessageBox.warning(self, "Uyarı", "Grup ID seçmelisiniz.")
            return False

        if self.table_widget.selectionModel().selectedRows():
            return True
        else:
            QMessageBox.warning(self, "Uyarı", "Bir resim seçmelisiniz.")
            return False


if __name__ == "__main__":
    global connection
    global sqlcursor
    db_path = "labels.db"
    connection = sqlite3.connect(db_path)
    sqlcursor = connection.cursor()

    app = QApplication(sys.argv)
    window = SimpleUI()
    window.show()
    sys.exit(app.exec_())
