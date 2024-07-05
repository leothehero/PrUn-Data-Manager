from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

ROWNAME = 0
ROWLABELS = 1

class MaterialDisplay(QWidget):

    def __init__(self,columns):
        super().__init__()
        layout = QGridLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0,0,0,0)
        layout.setVerticalSpacing(0)
        layout.setHorizontalSpacing(0)

        self.rows = list()
        self.columns = columns

        for i in range(1,self.columns,1):
            layout.setColumnStretch(i,1)
    
    def clearRows(self):
        for row in range(len(self.rows)):
            for column in range(self.columns):
                self.rows[row][ROWLABELS][column].deleteLater()
        self.rows.clear()
        return

    def _addEmptyRow(self,entryTitle):
        rowData = list("-")*self.columns
        rowData[0] = entryTitle
        self._addPresetRow(rowData)

        """row = len(self.rows)
        self.rows.append(list())
        self.rows[row].append(entryTitle)
        self.rows[row].append(list())
        for i in range(self.columns):
            label = QLabel("-")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("border: 1px solid black")
            label.setMargin(10)
            self.rows[row][ROWLABELS].append(label)
            self.layout().addWidget(label,row,i)
        self.rows[row][ROWLABELS][0].setText(entryTitle)"""

    def _addPresetRow(self,rowData):
        row = len(self.rows)
        self.rows.append(list())
        self.rows[row].append(rowData[0])
        self.rows[row].append(list())
        for i in range(self.columns):
            label = QLabel(rowData[i])
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("border: 1px solid black")
            label.setMargin(10)
            self.rows[row][ROWLABELS].append(label)
            self.layout().addWidget(label,row,i)

    def addRows(self,materials): #TODO: Rename to addEmptyRows
        if not type(materials) == tuple:
            materials = tuple(materials)
        for mat in materials:
            self._addEmptyRow(mat)
        return self

    def addPresetRows(self,data):
        if not type(data) == tuple:
            data = tuple(data)
        for row in data:
            self._addPresetRow(row)
        return self
    
    def getSizeHints(self):
        materialSize = 0
        for label in self.rows:
            height = label[ROWLABELS][0].sizeHint().height()
            width = label[ROWLABELS][0].sizeHint().width()
            materialSize = max(materialSize,max(height,width))
        return materialSize
    
    def setColumnMinSize(self,column,x,y):
        for label in self.rows:
            label[ROWLABELS][column].setMinimumSize(x,y)
    
    def getLabelAt(self,row,column):
        return self.rows[row][ROWLABELS][column]