import os
import sys
import math

import numpy as np
from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt, QSize

from Orange.canvas.utils import environ
from Orange.widgets import gui
from Orange.widgets.utils import colorbrewer

DefaultRGBColors = [
    (0, 0, 255), (255, 0, 0), (0, 255, 0), (255, 128, 0), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 0, 255), (0, 128, 255), (255, 223, 128),
    (127, 111, 64), (92, 46, 0), (0, 84, 0), (192, 192, 0), (0, 127, 127),
    (128, 0, 0), (127, 0, 127)]

DefaultColorBrewerPalette = {
    3: [(127, 201, 127), (190, 174, 212), (253, 192, 134)],
    4: [(127, 201, 127), (190, 174, 212), (253, 192, 134), (255, 255, 153)],
    5: [(127, 201, 127), (190, 174, 212), (253, 192, 134), (255, 255, 153),
        (56, 108, 176)],
    6: [(127, 201, 127), (190, 174, 212), (253, 192, 134), (255, 255, 153),
        (56, 108, 176), (240, 2, 127)],
    7: [(127, 201, 127), (190, 174, 212), (253, 192, 134), (255, 255, 153),
        (56, 108, 176), (240, 2, 127), (191, 91, 23)],
    8: [(127, 201, 127), (190, 174, 212), (253, 192, 134), (255, 255, 153),
        (56, 108, 176), (240, 2, 127), (191, 91, 23), (102, 102, 102)]}

ColorButtonSize = 25


#A 10X10 single color pixmap
class ColorPixmap(QIcon):
    def __init__(self, color=QColor(Qt.white), size=12):
        p = QPixmap(size, size)
        p.fill(color)
        self.color = color
        QIcon.__init__(self, p)


# a widget for selecting the colors to be used
class ColorPaletteDlg(QDialog):
    def __init__(self, parent, windowTitle="Color Palette"):
        super().__init__(parent, windowTitle=windowTitle)
        self.setLayout(QVBoxLayout())
        self.layout().setMargin(4)

        self.contPaletteNames = []
        self.exContPaletteNames = []
        self.discPaletteNames = []
        self.colorButtonNames = []
        self.colorSchemas = []
        self.selectedSchemaIndex = 0

        self.mainArea = gui.widgetBox(self, spacing=4)
        self.layout().addWidget(self.mainArea)
        self.schemaCombo = gui.comboBox(
            self.mainArea, self, "selectedSchemaIndex", box="Saved Profiles",
            callback=self.paletteSelected)

        self.hbox = gui.widgetBox(self, orientation="horizontal")
        self.okButton = gui.button(self.hbox, self, "OK", self.acceptChanges)
        self.cancelButton = gui.button(self.hbox, self, "Cancel", self.reject)
        self.setMinimumWidth(230)
        self.resize(350, 200)

    def acceptChanges(self):
        state = self.getCurrentState()
        oldState = self.colorSchemas[self.selectedSchemaIndex][1]
        if state == oldState:
            QDialog.accept(self)
        else:
            # if we change the default schema, we must save it under a new name
            if self.colorSchemas[self.selectedSchemaIndex][0] == "Default":
                if QMessageBox.information(
                        self, 'Question',
                        'The color schema has changed. Save?',
                        'Yes', 'Discard', '', 0, 1):
                    QDialog.reject(self)
                else:
                    self.selectedSchemaIndex = self.schemaCombo.count() - 1
                    self.schemaCombo.setCurrentIndex(self.selectedSchemaIndex)
                    self.paletteSelected()
                    QDialog.accept(self)
            # simply save the new users schema
            else:
                self.colorSchemas[self.selectedSchemaIndex] = \
                    [self.colorSchemas[self.selectedSchemaIndex][0], state]
                QDialog.accept(self)

    def createBox(self, boxName, boxCaption=None):
        box = gui.widgetBox(self.mainArea, boxCaption)
        box.setAlignment(Qt.AlignLeft)
        return box

    def createColorButton(self, box, buttonName, buttonCaption,
                          initialColor=Qt.black):
        self.__dict__["butt" + buttonName] = ColorButton(self, box, buttonCaption)
        self.__dict__["butt" + buttonName].setColor(QColor(initialColor))
        self.colorButtonNames.append(buttonName)

    def createContinuousPalette(self, paletteName, boxCaption,
                                passThroughBlack=0,
                                initialColor1=Qt.white, initialColor2=Qt.black):
        buttBox = gui.widgetBox(self.mainArea, boxCaption)
        box = gui.widgetBox(buttBox, orientation="horizontal")

        self.__dict__["cont" + paletteName + "Left"] = ColorButton(self, box, color=QColor(initialColor1))
        self.__dict__["cont" + paletteName + "View"] = PaletteView(box)
        self.__dict__["cont" + paletteName + "Right"] = ColorButton(self, box, color=QColor(initialColor2))

        self.__dict__["cont" + paletteName + "passThroughBlack"] = passThroughBlack
        self.__dict__["cont" + paletteName + "passThroughBlackCheckbox"] = gui.checkBox(buttBox, self,
                                                                                        "cont" + paletteName + "passThroughBlack",
                                                                                        "Pass through black",
                                                                                        callback=self.colorSchemaChange)
        self.contPaletteNames.append(paletteName)

    def createExtendedContinuousPalette(self, paletteName, boxCaption,
                                        passThroughColors=0, initialColor1=Qt.white,
                                        initialColor2=Qt.black,
                                        extendedPassThroughColors=((Qt.red, 1),
                                                                   (Qt.black, 1),
                                                                   (Qt.green, 1))):
        buttBox = gui.widgetBox(self.mainArea, boxCaption)
        box = gui.widgetBox(buttBox, orientation="horizontal")

        self.__dict__["exCont" + paletteName + "Left"] = ColorButton(self, box, color=QColor(initialColor1))
        self.__dict__["exCont" + paletteName + "View"] = PaletteView(box)
        self.__dict__["exCont" + paletteName + "Right"] = ColorButton(self, box, color=QColor(initialColor2))

        self.__dict__["exCont" + paletteName + "passThroughColors"] = passThroughColors
        self.__dict__["exCont" + paletteName + "passThroughColorsCheckbox"] = gui.checkBox(buttBox, self,
                                                                                           "exCont" + paletteName + "passThroughColors",
                                                                                           "Use pass-through colors",
                                                                                           callback=self.colorSchemaChange)

        box = gui.widgetBox(buttBox, "Pass-through colors", orientation="horizontal")
        for i, (color, check) in enumerate(extendedPassThroughColors):
            self.__dict__["exCont" + paletteName + "passThroughColor" + str(i)] = check
            self.__dict__["exCont" + paletteName + "passThroughColor" + str(i) + "Checkbox"] = cb = gui.checkBox(box,
                                                                                                                 self,
                                                                                                                 "exCont" + paletteName + "passThroughColor" + str(
                                                                                                                     i),
                                                                                                                 "",
                                                                                                                 tooltip="Use color",
                                                                                                                 callback=self.colorSchemaChange)
            self.__dict__["exCont" + paletteName + "color" + str(i)] = ColorButton(self, box, color=QColor(color))
            if i < len(extendedPassThroughColors) - 1:
                gui.rubber(box)
        self.__dict__["exCont" + paletteName + "colorCount"] = len(extendedPassThroughColors)
        self.exContPaletteNames.append(paletteName)


    # #####################################################
    # DISCRETE COLOR PALETTE
    # #####################################################
    def createDiscretePalette(self, paletteName, boxCaption, rgbColors=DefaultRGBColors):
        vbox = gui.widgetBox(self.mainArea, boxCaption, orientation='vertical')
        self.__dict__["disc" + paletteName + "View"] = PaletteView(vbox)
        self.__dict__["disc" + paletteName + "View"].rgbColors = rgbColors

        hbox = gui.widgetBox(vbox, orientation='horizontal')
        self.__dict__["disc" + paletteName + "EditButt"] = gui.button(hbox, self, "Edit palette", self.editPalette,
                                                                      tooltip="Edit the order and colors of the palette",
                                                                      toggleButton=1)
        self.__dict__["disc" + paletteName + "LoadButt"] = gui.button(hbox, self, "Load palette", self.loadPalette,
                                                                      tooltip="Load a predefined color palette",
                                                                      toggleButton=1)
        self.discPaletteNames.append(paletteName)


    def editPalette(self):
        for paletteName in self.discPaletteNames:
            if self.__dict__["disc" + paletteName + "EditButt"].isChecked():
                colors = self.__dict__["disc" + paletteName + "View"].rgbColors
                if type(colors) == dict:
                    colors = colors[max(colors.keys())]
                dlg = PaletteEditor(colors, parent=self)
                if dlg.exec_() and colors != dlg.getRgbColors():
                    self.__dict__["disc" + paletteName + "View"].setDiscPalette(dlg.getRgbColors())
                self.__dict__["disc" + paletteName + "EditButt"].setChecked(0)
                return

    def loadPalette(self):
        for paletteName in self.discPaletteNames:
            if self.__dict__["disc" + paletteName + "LoadButt"].isChecked():
                self.__dict__["disc" + paletteName + "LoadButt"].setChecked(0)
                dlg = ColorPalleteListing()
                if dlg.exec() == QDialog.Accepted:
                    colors = dlg.selectedColors
                    self.__dict__["disc" + paletteName + "View"].setDiscPalette(colors)


    # #####################################################

    def getCurrentSchemeIndex(self):
        return self.selectedSchemaIndex

    def getColor(self, buttonName):
        return self.__dict__["butt" + buttonName].getColor()

    def getContinuousPalette(self, paletteName):
        c1 = self.__dict__["cont" + paletteName + "Left"].getColor()
        c2 = self.__dict__["cont" + paletteName + "Right"].getColor()
        b = self.__dict__["cont" + paletteName + "passThroughBlack"]
        return ContinuousPaletteGenerator(c1, c2, b)

    def getExtendedContinuousPalette(self, paletteName):
        c1 = self.__dict__["exCont" + paletteName + "Left"].getColor()
        c2 = self.__dict__["exCont" + paletteName + "Right"].getColor()
        colors = self.__dict__["exCont" + paletteName + "passThroughColors"]
        if colors:
            colors = [self.__dict__["exCont" + paletteName + "color" + str(i)].getColor()
                      for i in range(self.__dict__["exCont" + paletteName + "colorCount"])
                      if self.__dict__["exCont" + paletteName + "passThroughColor" + str(i)]]
        return ExtendedContinuousPaletteGenerator(c1, c2, colors or [])

    def getDiscretePalette(self, paletteName):
        return ColorPaletteGenerator(
            rgb_colors=self.__dict__["disc" + paletteName + "View"].rgbColors)

    def getColorSchemas(self):
        return self.colorSchemas

    def getCurrentState(self):
        l1 = [(name, self.qRgbFromQColor(self.__dict__["butt" + name].getColor())) for name in self.colorButtonNames]
        l2 = [(name, (self.qRgbFromQColor(self.__dict__["cont" + name + "Left"].getColor()),
                      self.qRgbFromQColor(self.__dict__["cont" + name + "Right"].getColor()),
                      self.__dict__["cont" + name + "passThroughBlack"])) for name in self.contPaletteNames]
        l3 = [(name, self.__dict__["disc" + name + "View"].rgbColors) for name in self.discPaletteNames]
        l4 = [(name, (self.qRgbFromQColor(self.__dict__["exCont" + name + "Left"].getColor()),
                      self.qRgbFromQColor(self.__dict__["exCont" + name + "Right"].getColor()),
                      self.__dict__["exCont" + name + "passThroughColors"],
                      [(self.qRgbFromQColor(self.__dict__["exCont" + name + "color" + str(i)].getColor()),
                        self.__dict__["exCont" + name + "passThroughColor" + str(i)])
                       for i in range(self.__dict__["exCont" + name + "colorCount"])]))
              for name in self.exContPaletteNames]
        return [l1, l2, l3, l4]


    def setColorSchemas(self, schemas=None, selectedSchemaIndex=0):
        self.schemaCombo.clear()

        if not schemas or type(schemas) != list:
            schemas = [("Default", self.getCurrentState())]

        self.colorSchemas = schemas
        self.schemaCombo.addItems([s[0] for s in schemas])
        self.schemaCombo.addItem("Save current palette as...")
        self.selectedSchemaIndex = selectedSchemaIndex
        self.schemaCombo.setCurrentIndex(self.selectedSchemaIndex)
        self.paletteSelected()

    def setCurrentState(self, state):
        if len(state) > 3:
            [buttons, contPalettes, discPalettes, exContPalettes] = state
        else:
            [buttons, contPalettes, discPalettes] = state
            exContPalettes = []
        for (name, but) in buttons:
            self.__dict__["butt" + name].setColor(rgbToQColor(but))
        for (name, (l, r, chk)) in contPalettes:
            self.__dict__["cont" + name + "Left"].setColor(rgbToQColor(l))
            self.__dict__["cont" + name + "Right"].setColor(rgbToQColor(r))
            self.__dict__["cont" + name + "passThroughBlack"] = chk
            self.__dict__["cont" + name + "passThroughBlackCheckbox"].setChecked(chk)
            self.__dict__["cont" + name + "View"].setContPalette(rgbToQColor(l), rgbToQColor(r), chk)

        for (name, rgbColors) in discPalettes:
            self.__dict__["disc" + name + "View"].setDiscPalette(rgbColors)

        for name, (l, r, chk, colors) in exContPalettes:
            self.__dict__["exCont" + name + "Left"].setColor(rgbToQColor(l))
            self.__dict__["exCont" + name + "Right"].setColor(rgbToQColor(r))

            self.__dict__["exCont" + name + "passThroughColors"] = chk
            self.__dict__["exCont" + name + "passThroughColorsCheckbox"].setChecked(chk)

            colorsList = []
            for i, (color, check) in enumerate(colors):
                self.__dict__["exCont" + name + "passThroughColor" + str(i)] = check
                self.__dict__["exCont" + name + "passThroughColor" + str(i) + "Checkbox"].setChecked(check)
                self.__dict__["exCont" + name + "color" + str(i)].setColor(rgbToQColor(color))
                if check and chk:
                    colorsList.append(rgbToQColor(color))
            self.__dict__["exCont" + name + "colorCount"] = self.__dict__.get("exCont" + name + "colorCount",
                                                                              len(colors))
            self.__dict__["exCont" + name + "View"].setExContPalette(rgbToQColor(l), rgbToQColor(r),
                                                                     colorsList)

    def paletteSelected(self):
        if not self.schemaCombo.count():
            return
        self.selectedSchemaIndex = self.schemaCombo.currentIndex()

        # if we selected "Save current palette as..." option then add another option to the list
        if self.selectedSchemaIndex == self.schemaCombo.count() - 1:
            message = "Please enter a name for the current color settings.\nPressing 'Cancel' will cancel your changes and close the dialog."
            ok = 0
            while not ok:
                text, ok = QInputDialog.getText(self, "Name Your Color Settings", message)
                if (ok):
                    newName = str(text)
                    oldNames = [str(self.schemaCombo.itemText(i)).lower() for i in range(self.schemaCombo.count() - 1)]
                    if newName.lower() == "default":
                        ok = False
                        message = "The 'Default' settings cannot be changed. Please enter a different name:"
                    elif newName.lower() in oldNames:
                        index = oldNames.index(newName.lower())
                        self.colorSchemas.pop(index)

                    if ok:
                        self.colorSchemas.insert(0, (newName, self.getCurrentState()))
                        self.schemaCombo.insertItem(0, newName)
                        self.schemaCombo.setCurrentIndex(0)
                        self.selectedSchemaIndex = 0
                else:
                    ok = 1
                    state = self.getCurrentState()  # if we pressed cancel we have to select a different item than the "Save current palette as..."
                    self.selectedSchemaIndex = 0
                    self.schemaCombo.setCurrentIndex(0)
                    self.setCurrentState(state)
        else:
            schema = self.colorSchemas[self.selectedSchemaIndex][1]
            self.setCurrentState(schema)

    def qRgbFromQColor(self, qcolor):
        return qcolor.rgba()

    def createPalette(self, color1, color2, passThroughBlack, colorNumber=250):
        if passThroughBlack:
            palette = [qRgb(color1.red() - color1.red() * i * 2. / colorNumber,
                            color1.green() - color1.green() * i * 2. / colorNumber,
                            color1.blue() - color1.blue() * i * 2. / colorNumber) for i in range(colorNumber / 2)]
            palette += [qRgb(color2.red() * i * 2. / colorNumber, color2.green() * i * 2. / colorNumber,
                             color2.blue() * i * 2. / colorNumber) for i in range(colorNumber - (colorNumber / 2))]
        else:
            palette = [qRgb(color1.red() + (color2.red() - color1.red()) * i / colorNumber,
                            color1.green() + (color2.green() - color1.green()) * i / colorNumber,
                            color1.blue() + (color2.blue() - color1.blue()) * i / colorNumber) for i in
                       range(colorNumber)]
        return palette

    # this function is called if one of the color buttons was pressed or there was any other change of the color palette
    def colorSchemaChange(self):
        self.setCurrentState(self.getCurrentState())
        self.shemaChanged.emit()


class ColorPalleteListing(QDialog):
    def __init__(self, parent=None, windowTitle="Color Palette List",
                 **kwargs):
        super().__init__(parent, windowTitle=windowTitle, **kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setMargin(0)
        sa = QScrollArea(
            horizontalScrollBarPolicy=Qt.ScrollBarAlwaysOff,
            verticalScrollBarPolicy=Qt.ScrollBarAlwaysOn
        )
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sa.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.layout().addWidget(sa)

        space = QWidget(self)
        space.setLayout(QVBoxLayout())
        sa.setWidget(space)
        sa.setWidgetResizable(True)

        self.buttons = []
        self.setMinimumWidth(400)

        box = gui.widgetBox(space, "Information", addSpace=True)
        gui.widgetLabel(
            box,
            '<p align="center">This dialog shows a list of predefined '
            'color palettes <br>from colorbrewer.org that can be used '
            'in Orange.<br/>You can select a palette by clicking on it.</p>'
        )

        box = gui.widgetBox(space, "Default Palette", addSpace=True)

        butt = _ColorButton(
            DefaultRGBColors, flat=True, toolTip="Default color palette",
            clicked=self._buttonClicked
        )
        box.layout().addWidget(butt)

        self.buttons.append(butt)

        for type in ["Qualitative", "Spectral", "Diverging", "Sequential", "Pastels"]:
            colorGroup = colorbrewer.colorSchemes.get(type.lower(), {})
            if colorGroup:
                box = gui.widgetBox(space, type + " Palettes", addSpace=True)
                items = sorted(colorGroup.items())
                for key, colors in items:
                    butt = _ColorButton(colors, self, toolTip=key, flat=True,
                                        clicked=self._buttonClicked)
                    box.layout().addWidget(butt)
                    self.buttons.append(butt)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel, rejected=self.reject
        )
        self.layout().addWidget(buttons)
        self.selectedColors = None

    def sizeHint(self):
        return QSize(300, 400)

    def _buttonClicked(self):
        button = self.sender()
        self.selectedColors = button.colors
        self.accept()


class _ColorButton(QPushButton):
    def __init__(self, colors, parent=None, **kwargs):
        self.colors = colors
        super().__init__(parent, **kwargs)
        self.setIcon(self._paletteicon(colors, self.sizeHint()))

    def sizeHint(self):
        return QSize(320, 40)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.size()
        self.setIconSize(size - QSize(20, 14))
        self.setIcon(self._paletteicon(self.colors, self.iconSize()))

    def _paletteicon(self, colors, size):
        return QIcon(
            createDiscPalettePixmap(size.width(), size.height(), colors))


class PaletteEditor(QDialog):

    def __init__(self, rgbColors, parent=None, windowTitle="Palette Editor",
                 **kwargs):
        super().__init__(parent, **kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setMargin(4)

        hbox = gui.widgetBox(self, "Information", orientation='horizontal')
        gui.widgetLabel(
            hbox,
            '<p align="center">You can reorder colors in the list using the'
            '<br/>buttons on the right or by dragging and dropping the items.'
            '<br/>To change a specific color double click the item in the '
            'list.</p>')

        hbox = gui.widgetBox(self, box=True, orientation="horizontal")
        self.discListbox = gui.listBox(hbox, self, enableDragDrop=1)

        vbox = gui.widgetBox(hbox, orientation='vertical')
        buttonUPAttr = gui.button(vbox, self, "", callback=self.moveAttrUP, tooltip="Move selected colors up")
        buttonDOWNAttr = gui.button(vbox, self, "", callback=self.moveAttrDOWN, tooltip="Move selected colors down")
        buttonUPAttr.setIcon(QIcon(os.path.join(environ.widget_install_dir, "icons/Dlg_up3.png")))
        buttonUPAttr.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding))
        buttonUPAttr.setMaximumWidth(30)
        buttonDOWNAttr.setIcon(QIcon(os.path.join(environ.widget_install_dir, "icons/Dlg_down3.png")))
        buttonDOWNAttr.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding))
        buttonDOWNAttr.setMaximumWidth(30)
        self.discListbox.itemDoubleClicked.connect(self.changeDiscreteColor)

        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                               accepted=self.accept, rejected=self.reject)
        self.layout().addWidget(box)

        self.discListbox.setIconSize(QSize(25, 25))
        for ind, (r, g, b) in enumerate(rgbColors):
            item = QListWidgetItem(ColorPixmap(QColor(r, g, b), 25), "Color %d" % (ind + 1))
            item.rgbColor = (r, g, b)
            self.discListbox.addItem(item)

        self.resize(300, 300)


    def changeDiscreteColor(self, item):
        r, g, b = item.rgbColor
        color = QColorDialog.getColor(QColor(r, g, b), self)
        if color.isValid():
            item.setIcon(ColorPixmap(color, 25))
            item.rgbColor = (color.red(), color.green(), color.blue())


    # move selected attribute in "Attribute Order" list one place up
    def moveAttrUP(self):
        if len(self.discListbox.selectedIndexes()) == 0: return
        ind = self.discListbox.selectedIndexes()[0].row()
        if ind == 0: return
        iconI = self.discListbox.item(ind - 1).icon()
        iconII = self.discListbox.item(ind).icon()
        self.discListbox.item(ind - 1).setIcon(iconII)
        self.discListbox.item(ind).setIcon(iconI)
        self.discListbox.item(ind - 1).rgbColor, self.discListbox.item(ind).rgbColor = self.discListbox.item(
            ind).rgbColor, self.discListbox.item(ind - 1).rgbColor
        self.discListbox.setCurrentRow(ind - 1)


    # move selected attribute in "Attribute Order" list one place down
    def moveAttrDOWN(self):
        if len(self.discListbox.selectedIndexes()) == 0: return
        ind = self.discListbox.selectedIndexes()[0].row()
        if ind == self.discListbox.count() - 1: return
        iconI = self.discListbox.item(ind + 1).icon()
        iconII = self.discListbox.item(ind).icon()
        self.discListbox.item(ind + 1).setIcon(iconII)
        self.discListbox.item(ind).setIcon(iconI)
        self.discListbox.item(ind).rgbColor, self.discListbox.item(ind + 1).rgbColor = self.discListbox.item(
            ind + 1).rgbColor, self.discListbox.item(ind).rgbColor
        self.discListbox.setCurrentRow(ind + 1)

    def getRgbColors(self):
        return [self.discListbox.item(i).rgbColor for i in range(self.discListbox.count())]


class ContinuousPaletteGenerator:
    def __init__(self, color1, color2, passThroughBlack):
        self.c1Red, self.c1Green, self.c1Blue = color1.red(), color1.green(), color1.blue()
        self.c2Red, self.c2Green, self.c2Blue = color2.red(), color2.green(), color2.blue()
        self.passThroughBlack = passThroughBlack

    def getRGB(self, val):
        if self.passThroughBlack:
            red = np.array([self.c1Red, 0, self.c2Red])
            green = np.array([self.c1Green, 0, self.c2Green])
            blue = np.array([self.c1Blue, 0, self.c2Blue])
            cs = [0, 0.5, 1]
        else:
            red = np.array([self.c1Red, self.c2Red])
            green = np.array([self.c1Green, self.c2Green])
            blue = np.array([self.c1Blue, self.c2Blue])
            cs = [0, 1]

        r = np.interp(val, cs, red)
        g = np.interp(val, cs, green)
        b = np.interp(val, cs, blue)

        rgb = np.c_[r, g, b]
        rgb[np.isnan(rgb).any(axis=1), :] = (157, 185, 250)

        if np.isscalar(val):
            return tuple(rgb[0].tolist())
        else:
            return rgb

    # val must be between 0 and 1
    def __getitem__(self, val):
        return QColor(*self.getRGB(val))


class ExtendedContinuousPaletteGenerator:
    def __init__(self, color1, color2, passThroughColors):
        self.colors = [color1] + passThroughColors + [color2]
        self.gammaFunc = lambda x, gamma: ((math.exp(gamma * math.log(2 * x - 1)) if x > 0.5 else -math.exp(
            gamma * math.log(-2 * x + 1)) if x != 0.5 else 0.0) + 1) / 2.0

    def getRGB(self, val, gamma=1.0):
        index = int(val * (len(self.colors) - 1))
        if index == len(self.colors) - 1:
            return (self.colors[-1].red(), self.colors[-1].green(), self.colors[-1].blue())
        else:
            red1, green1, blue1 = self.colors[index].red(), self.colors[index].green(), self.colors[index].blue()
            red2, green2, blue2 = self.colors[index + 1].red(), self.colors[index + 1].green(), self.colors[
                index + 1].blue()
            x = val * (len(self.colors) - 1) - index
            if gamma != 1.0:
                x = self.gammaFunc(x, gamma)
            return [(c2 - c1) * x + c1 for c1, c2 in [(red1, red2), (green1, green2), (blue1, blue2)]]
        ##        if self.passThroughBlack:
        ##            if val < 0.5:
        ##                return (self.c1Red - self.c1Red*val*2, self.c1Green - self.c1Green*val*2, self.c1Blue - self.c1Blue*val*2)
        ##            else:
        ##                return (self.c2Red*(val-0.5)*2., self.c2Green*(val-0.5)*2., self.c2Blue*(val-0.5)*2.)
        ##        else:
        ##            return (self.c1Red + (self.c2Red-self.c1Red)*val, self.c1Green + (self.c2Green-self.c1Green)*val, self.c1Blue + (self.c2Blue-self.c1Blue)*val)

    # val must be between 0 and 1
    def __getitem__(self, val):
        return QColor(*self.getRGB(val))


class ColorPaletteGenerator:
    maxHueVal = 260

    def __init__(self, number_of_colors=None, rgb_colors=DefaultRGBColors):
        self.number_of_colors = 0
        self.rgb_colors = self.default_colors = rgb_colors
        self.rgb_array = None  # np.ndarray
        self.rgba_array = None  # np.ndarray
        if isinstance(rgb_colors, dict):
            self.rgb_colors_dict = rgb_colors
            self.set_number_of_colors(max(rgb_colors.keys()))
        else:
            self.rgb_colors_dict = None
            self.set_number_of_colors(number_of_colors)

    def set_number_of_colors(self, number_of_colors=None):
        """Change the palette if there are palettes for different number of
           colors. Else, just copy rgbColors to numpy array"""
        self.number_of_colors = number_of_colors
        if self.rgb_colors_dict is not None:
            number_of_colors = max(3, number_of_colors)
            if number_of_colors not in self.rgb_colors_dict:
                keys = [n for n in self.rgb_colors_dict
                        if n >= number_of_colors]
                if keys:
                    number_of_colors = min(keys)
                else:
                    raise ValueError("Not enough colors")

            self.rgb_colors = \
                self.rgb_colors_dict[number_of_colors]

        elif number_of_colors is None or \
                number_of_colors < len(self.rgb_colors):
            self.rgb_colors = self.default_colors
        else:
            self.rgb_colors = []
            for i in range(self.number_of_colors):
                col = QColor()
                col.setHsv(360 / number_of_colors * i, 255, 255)
                self.rgb_colors.append(col.getRgb())
        self.rgb_array = np.array(self.rgb_colors)
        self.rgba_array = np.hstack([
            self.rgb_array, np.full((len(self.rgb_colors), 1), 255)])

    def __getitem__(self, index):
        return QColor(*self.getRGB(index))

    # noinspection PyPep8Naming
    def getRGB(self, index):
        if isinstance(index, np.ndarray):
            return self.rgb_array[index.astype(int)]
        else:
            return self.rgb_colors[int(index)]

    # noinspection PyPep8Naming
    def getRGBA(self, index):
        if isinstance(index, np.ndarray):
            return self.rgba_array[index.astype(int)]
        else:
            return self.rgba_colors[int(index)]

    getColor = getRGB


# only for backward compatibility
class ColorPaletteHSV(ColorPaletteGenerator):
    pass


# black and white color palette
class ColorPaletteBW:
    def __init__(self, numberOfColors=-1, brightest=50, darkest=255):
        self.numberOfColors = numberOfColors
        self.brightest = brightest
        self.darkest = darkest
        self.hueValues = []

        if numberOfColors == -1:
            return # used for coloring continuous variables
        else:
            self.values = [int(brightest + (darkest - brightest) * x / float(numberOfColors - 1)) for x in
                           range(numberOfColors)]

    def __getitem__(self, index):
        if self.numberOfColors == -1:                # is this color for continuous attribute?
            val = int(self.brightest + (self.darkest - self.brightest) * index)
            return QColor(val, val, val)
        else:
            index = int(index)                       # get color for discrete attribute
            return QColor(self.values[index], self.values[index],
                          self.values[index])   # index must be between 0 and self.numberofColors

    # get QColor instance for given index
    def getColor(self, index):
        return self[index]


class ColorSchema:
    def __init__(self, name, palette, additionalColors, passThroughBlack):
        self.name = name
        self.palette = palette
        self.additionalColors = additionalColors
        self.passThroughBlack = passThroughBlack

    def getName(self):
        return self.name

    def getPalette(self):
        return self.palette

    def getAdditionalColors(self):
        return self.additionalColors

    def getPassThroughBlack(self):
        return self.passThroughBlack


class PaletteView(QGraphicsView):
    def __init__(self, parent=None):
        self.canvas = QGraphicsScene(0, 0, 1000, ColorButtonSize)
        QGraphicsView.__init__(self, self.canvas, parent)
        self.ensureVisible(0, 0, 1, 1)

        self.color1 = None
        self.color2 = None
        self.rgbColors = []
        self.passThroughColors = None

        #self.setFrameStyle(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setFixedHeight(ColorButtonSize)
        self.setMinimumWidth(ColorButtonSize)

        if parent and parent.layout() is not None:
            parent.layout().addWidget(self)

    def resizeEvent(self, ev):
        self.updateImage()

    def setDiscPalette(self, rgbColors):
        self.rgbColors = rgbColors
        self.updateImage()

    def setContPalette(self, color1, color2, passThroughBlack):
        self.color1 = color1
        self.color2 = color2
        self.passThroughBlack = passThroughBlack
        self.updateImage()

    def setExContPalette(self, color1, color2, passThroughColors):
        self.color1 = color1
        self.color2 = color2
        self.passThroughColors = passThroughColors
        self.updateImage()

    def updateImage(self):
        for item in self.scene().items():
            item.hide()
        if self.color1 is None:
            img = createDiscPalettePixmap(self.width(), self.height(), self.rgbColors)
        elif self.passThroughColors is None:
            img = createContPalettePixmap(self.width(), self.height(), self.color1, self.color2, self.passThroughBlack)
        else:
            img = createExContPalettePixmap(self.width(), self.height(), self.color1, self.color2,
                                            self.passThroughColors)
        self.scene().addPixmap(img)
        self.scene().update()


# create a pixmap with color going from color1 to color2
def createContPalettePixmap(width, height, color1, color2, passThroughBlack):
    p = QPainter()
    img = QPixmap(width, height)
    p.begin(img)

    #p.eraseRect(0, 0, w, h)
    p.setPen(QPen(Qt.NoPen))
    g = QLinearGradient(0, 0, width, height)
    g.setColorAt(0, color1)
    g.setColorAt(1, color2)
    if passThroughBlack:
        g.setColorAt(0.5, Qt.black)
    p.fillRect(img.rect(), QBrush(g))
    return img


# create a pixmap with a discrete palette
def createDiscPalettePixmap(width, height, palette):
    p = QPainter()
    img = QPixmap(width, height)
    p.begin(img)
    p.setPen(QPen(Qt.NoPen))
    if type(palette) == dict:       # if palette is the dict with different
        palette = palette[max(palette.keys())]
    if len(palette) == 0: return img
    rectWidth = width / float(len(palette))
    for i, col in enumerate(palette):
        p.setBrush(QBrush(QColor(*col)))
        p.drawRect(QtCore.QRectF(i * rectWidth, 0, (i + 1) * rectWidth, height))
    return img

# create a pixmap withcolor going from color1 to color2 passing through all intermidiate colors in passThroughColors
def createExContPalettePixmap(width, height, color1, color2, passThroughColors):
    p = QPainter()
    img = QPixmap(width, height)
    p.begin(img)

    #p.eraseRect(0, 0, w, h)
    p.setPen(QPen(Qt.NoPen))
    g = QLinearGradient(0, 0, width, height)
    g.setColorAt(0, color1)
    g.setColorAt(1, color2)
    for i, color in enumerate(passThroughColors):
        g.setColorAt(float(i + 1) / (len(passThroughColors) + 1), color)
    p.fillRect(img.rect(), QBrush(g))
    return img


class ColorButton(QWidget):
    def __init__(self, master=None, parent=None, label=None, color=None):
        QWidget.__init__(self, master)

        self.parent = parent
        self.master = master

        if self.parent and self.parent.layout() is not None:
            self.parent.layout().addWidget(self)

        self.setLayout(QHBoxLayout())
        self.layout().setMargin(0)
        self.icon = QFrame(self)
        self.icon.setFixedSize(ColorButtonSize, ColorButtonSize)
        self.icon.setAutoFillBackground(1)
        self.icon.setFrameStyle(QFrame.StyledPanel + QFrame.Sunken)
        self.layout().addWidget(self.icon)

        if label != None:
            self.label = gui.widgetLabel(self, label)
            self.layout().addWidget(self.label)

        if color != None:
            self.setColor(color)

    def setColor(self, color):
        self.color = color
        palette = QPalette()
        palette.setBrush(QPalette.Background, color)
        self.icon.setPalette(palette)

    def getColor(self):
        return self.color

    def mousePressEvent(self, ev):
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.setColor(color)
            if self.master and hasattr(self.master, "colorSchemaChange"):
                self.master.colorSchemaChange()


def rgbToQColor(rgb):
    return QColor(rgb & 0xFFFFFFFF)


class PaletteItemDelegate(QItemDelegate):
    def __init__(self, selector, *args):
        QItemDelegate.__init__(self, *args)
        self.selector = selector

    def paint(self, painter, option, index):
        img = self.selector.paletteImg[index.row()]
        painter.drawPixmap(option.rect.x(), option.rect.y(), img)

    def sizeHint(self, option, index):
        img = self.selector.paletteImg[index.row()]
        return img.size()


class PaletteSelectorComboBox(QComboBox):
    def __init__(self, *args):
        QComboBox.__init__(self, *args)
        self.paletteImg = []
        self.cachedPalettes = []
        ##        self.setItemDelegate(PaletteItemDelegate(self, self))
        size = self.sizeHint()
        size = QSize(size.width() * 2 / 3, size.height() * 2 / 3)
        self.setIconSize(size)

    def setPalettes(self, name, paletteDlg):
        self.clear()
        self.cachedPalettes = []
        shemas = paletteDlg.getColorSchemas()
        if name in paletteDlg.discPaletteNames:
            pass
        if name in paletteDlg.contPaletteNames:
            pass
        if name in paletteDlg.exContPaletteNames:
            palettes = []
            paletteIndex = paletteDlg.exContPaletteNames.index(name)
            for schemaName, state in shemas:
                butt, disc, cont, exCont = state
                name, (c1, c2, chk, colors) = exCont[paletteIndex]
                palettes.append((schemaName, (
                (rgbToQColor(c1), rgbToQColor(c2), [rgbToQColor(color) for color, check in colors if check and chk]))))
            self.setContinuousPalettes(palettes)

    def setDiscretePalettes(self, palettes):
        self.clear()
        paletteImg = []
        self.cachedPalettes = []
        for name, colors in palettes:
            self.addItem(name)
            self.paletteImg.append(createDiscPalettePixmap(200, 20, colors))
            self.cachedPalettes.append(ColorPaletteGenerator(rgb_colors=colors))

    def setContinuousPalettes(self, palettes):
        self.clear()
        paletteImg = []
        self.cachedPalettes = []
        for name, (c1, c2, colors) in palettes:
            icon = QIcon(createExContPalettePixmap(self.iconSize().width(), self.iconSize().height(), c1, c2, colors))
            self.addItem(icon, name)


if __name__ == "__main__":
    a = QApplication(sys.argv)

    c = ColorPaletteDlg(None)
    c.createContinuousPalette("continuousPalette", "Continuous Palette")
    c.createDiscretePalette("discPalette", "Discrete Palette")
    box = c.createBox("otherColors", "Colors")
    c.createColorButton(box, "Canvas", "Canvas")
    c.createColorButton(box, "Grid", "Grid")
    c.setColorSchemas()
    c.show()
    a.exec()
