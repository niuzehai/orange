"""
<name>Interaction Graph</name>
<description>Show interaction graph</description>
<category>Classification</category>
<icon>icons/InteractionGraph.png</icon>
<priority>4000</priority>
"""
# InteractionGraph.py
#
# 

from OWWidget import *
from OWInteractionGraphOptions import *
from OWScatterPlotGraph import OWScatterPlotGraph
from OData import *
from qt import *
from qtcanvas import *
import orngInteract
import statc
import os
from re import *
from math import floor, ceil


class IntGraphView(QCanvasView):
    def __init__(self, parent, name, *args):
        apply(QCanvasView.__init__,(self,) + args)
        self.parent = parent
        self.name = name

    # mouse button was pressed
    def contentsMousePressEvent(self, ev):
        self.parent.mousePressed(self.name, ev)


###########################################################################################
##### WIDGET : Interaction graph
###########################################################################################
class OWInteractionGraph(OWWidget):
    settingsList = ["onlyImportantAttrs", "onlyImportantInteractions"]
    
    def __init__(self,parent=None):
        OWWidget.__init__(self, parent, "Interaction graph", 'show interaction graph', FALSE, FALSE)

        #set default settings
        self.data = None
        self.interactionMatrix = None
        self.rectIndices = {}   # QRect rectangles
        self.rectNames   = {}   # info about rectangle names (attributes)
        self.lines = []         # dict of form (rectName1, rectName2):(labelQPoint, [p1QPoint, p2QPoint, ...])
        self.interactionRects = []
        self.rectItems = []

        self.onlyImportantAttrs = 1
        self.onlyImportantInteractions = 1

        self.addInput("cdata")
        self.addOutput("cdata")
        self.addOutput("view")      # when user clicks on a link label we can send information about this two attributes to a scatterplot
        self.addOutput("selection") # when user clicks on "show selection" button we can send information about selected attributes

        #load settings
        self.loadSettings()

        # add a settings dialog and initialize its values
        #self.options = OWInteractionGraphOptions()

        self.splitCanvas = QSplitter(self.mainArea)
        
        self.canvasL = QCanvas(2000, 2000)
        self.canvasViewL = IntGraphView(self, "interactions", self.canvasL, self.splitCanvas)
        self.canvasViewL.show()
        
        self.canvasR = QCanvas(2000,2000)
        self.canvasViewR = IntGraphView(self, "graph", self.canvasR, self.splitCanvas)
        self.canvasViewR.show()


        #GUI
        #add controls to self.controlArea widget
        self.shownAttribsGroup = QVGroupBox(self.space)
        self.addRemoveGroup = QHButtonGroup(self.space)
        self.hiddenAttribsGroup = QVGroupBox(self.space)
        self.shownAttribsGroup.setTitle("Shown attributes")
        self.hiddenAttribsGroup.setTitle("Hidden attributes")

        self.shownAttribsLB = QListBox(self.shownAttribsGroup)
        self.shownAttribsLB.setSelectionMode(QListBox.Extended)

        self.hiddenAttribsLB = QListBox(self.hiddenAttribsGroup)
        self.hiddenAttribsLB.setSelectionMode(QListBox.Extended)
        
        self.attrAddButton = QPushButton("Add attr.", self.addRemoveGroup)
        self.attrRemoveButton = QPushButton("Remove attr.", self.addRemoveGroup)

        self.importantAttrsCB = QCheckBox('Show only important attributes', self.space)
        self.importantInteractionsCB = QCheckBox('Show only important interactions', self.space)
        
        self.selectionButton = QPushButton("Show selection", self.space)

        self.saveLCanvas = QPushButton("Save left canvas", self.space)
        self.saveRCanvas = QPushButton("Save right canvas", self.space)
        self.connect(self.saveLCanvas, SIGNAL("clicked()"), self.saveToFileLCanvas)
        self.connect(self.saveRCanvas, SIGNAL("clicked()"), self.saveToFileRCanvas)

        #connect controls to appropriate functions
        self.connect(self.attrAddButton, SIGNAL("clicked()"), self.addAttributeClick)
        self.connect(self.attrRemoveButton, SIGNAL("clicked()"), self.removeAttributeClick)
        self.connect(self.selectionButton, SIGNAL("clicked()"), self.selectionClick)
        self.connect(self.importantAttrsCB, SIGNAL("toggled(bool)"), self.showImportantAttrs)
        self.connect(self.importantInteractionsCB, SIGNAL("toggled(bool)"), self.showImportantInteractions)

        #self.connect(self.graphButton, SIGNAL("clicked()"), self.graph.saveToFile)
        #self.connect(self.settingsButton, SIGNAL("clicked()"), self.options.show)
        self.activateLoadedSettings()

    def showImportantAttrs(self, b):
        self.onlyImportantAttrs = b
        self.showInteractionRects()
        
    def showImportantInteractions(self, b):
        self.onlyImportantInteractions = b
        self.showInteractionRects()

    def activateLoadedSettings(self):
        self.importantAttrsCB.setChecked(self.onlyImportantAttrs)
        self.importantInteractionsCB.setChecked(self.onlyImportantInteractions)

    # did we click inside the rect rectangle
    def clickInside(self, rect, point):
        x = point.x()
        y = point.y()
        
        if rect.left() > x: return 0
        if rect.right() < x: return 0
        if rect.top() > y: return 0
        if rect.bottom() < y: return 0

        return 1
        
    # if we clicked on edge label send "wiew" signal, if clicked inside rectangle select/unselect attribute
    def mousePressed(self, name, ev):
        if ev.button() == QMouseEvent.LeftButton and name == "graph":
            for name in self.rectNames:
                clicked = self.clickInside(self.rectNames[name].rect(), ev.pos())
                if clicked == 1:
                    self._setAttrVisible(name, not self.getAttrVisible(name))
                    self.showInteractionRects()
                    self.canvasR.update()
                    return
            for (attr1, attr2, rect) in self.lines:
                clicked = self.clickInside(rect.rect(), ev.pos())
                if clicked == 1:
                    self.send("view", (attr1, attr2))
                    return


    # we catch mouse release event so that we can send the "view" signal
    def onMouseReleased(self, e):
        for i in range(len(self.graphs)):
            if self.graphs[i].blankClick == 1:
                (attr1, attr2, className, string) = self.graphParameters[i]
                self.send("view", (attr1, attr2))
                self.graphs[i].blankClick = 0

    # click on selection button   
    def selectionClick(self):
        if self.data == None: return
        list = []
        for i in range(self.shownAttribsLB.count()):
            list.append(str(self.shownAttribsLB.text(i)))
        self.send("selection", list)

    def resizeEvent(self, e):
        self.splitCanvas.resize(self.mainArea.size())


    ####### CDATA ################################
    # receive new data and update all fields
    def cdata(self, data):
        self.data = orange.Preprocessor_dropMissing(data.data)
        self.interactionMatrix = orngInteract.InteractionMatrix(self.data)

        self.interactionList = []
        entropy = self.interactionMatrix.entropy

        ################################
        # create a sorted list of total information
        for ((val,(val2, attrIndex1, attrIndex2))) in self.interactionMatrix.list:
            gain1 = self.interactionMatrix.gains[attrIndex1] / entropy
            gain2 = self.interactionMatrix.gains[attrIndex2] / entropy
            total = (val/entropy) + gain1 + gain2
            self.interactionList.append((total, (gain1, gain2, attrIndex1, attrIndex2)))
        self.interactionList.sort()
        self.interactionList.reverse()
       
        f = open('interaction.dot','w')
        self.interactionMatrix.exportGraph(f, significant_digits=3,positive_int=8,negative_int=8,absolute_int=0,url=1)
        f.flush()
        f.close()

        # execute dot and save otuput to pipes
        (pipePngOut, pipePngIn) = os.popen2("dot interaction.dot -Tpng", "b")
        (pipePlainOut, pipePlainIn) = os.popen2("dot interaction.dot -Tismap", "t")
        textPng = pipePngIn.read()
        textPlainList = pipePlainIn.readlines()
        pipePngIn.close()
        pipePlainIn.close()
        pipePngOut.close()
        pipePlainOut.close()
        
        pixmap = QPixmap()
        pixmap.loadFromData(textPng)
        canvasPixmap = QCanvasPixmap(pixmap, QPoint(0,0))
        width = canvasPixmap.width()
        height = canvasPixmap.height()

        # hide all rects
        for rectInd in self.rectIndices.keys():
            self.rectIndices[rectInd].hide()

        self.send("cdata", data)
        
        self.canvasR.setTiles(pixmap, 1, 1, width, height)
        self.canvasR.resize(width, height)
        
        self.rectIndices = {}       # QRect rectangles
        self.rectNames   = {}       # info about rectangle names (attributes)
        self.lines = []             # dict of form (rectName1, rectName2):(labelQPoint, [p1QPoint, p2QPoint, ...])

        
        self.parseGraphData(textPlainList, width, height)
        self.initLists(self.data)   # add all attributes found in .dot file to shown list
        self.showInteractionRects() # use interaction matrix to fill the left canvas with rectangles
        
        self.canvasL.update()
        self.canvasR.update()

    def showInteractionPair(self, attrIndex1, attrIndex2):
        attrName1 = self.data.domain[attrIndex1].name
        attrName2 = self.data.domain[attrIndex2].name
        if self.onlyImportantAttrs == 1:
            if self.getAttrVisible(attrName1) == 0 or self.getAttrVisible(attrName2) == 0: return 0
        if self.onlyImportantInteractions == 1:
            for (attr1, attr2, rect) in self.lines:
                if (attr1 == attrName1 and attr2 == attrName2) or (attr1 == attrName2 and attr2 == attrName1): return 1
            return 0
        return 1

    def showInteractionRects(self):
        if self.interactionMatrix == None: return
        if self.data == None : return

        ################################
        # hide all interaction rectangles
        for (rect1, rect2, rect3, text1, text2) in self.interactionRects:
            rect1.hide() 
            rect2.hide() 
            rect3.hide() 
            text1.hide() 
            text2.hide() 
        self.interactionRects = []

        for item in self.rectItems:
            item.hide()
        self.rectItems = []
        
        ################################
        # get max width of the attribute text
        xOff = 0        
        for ((total, (gain1, gain2, attrIndex1, attrIndex2))) in self.interactionList:
            if not self.showInteractionPair(attrIndex1, attrIndex2): continue
            text = QCanvasText(self.data.domain[attrIndex1].name, self.canvasL)
            rect = text.boundingRect()
            if xOff < rect.width():
                xOff = rect.width()

        xOff += 10;  yOff = 40
        index = 0
        xscale = 300;  yscale = 200
        maxWidth = xOff + xscale + 10;  maxHeight = 0
        rectHeight = yscale * 0.1    # height of the rectangle will be 1/10 of max width

        ################################
        # print scale
        line = QCanvasRectangle(xOff, yOff - 4, xscale, 1, self.canvasL)
        line.show()
        tick1 = QCanvasRectangle(xOff, yOff-10, 1, 6, self.canvasL);              tick1.show()
        tick2 = QCanvasRectangle(xOff + (xscale/2), yOff-10, 1, 6, self.canvasL); tick2.show()
        tick3 = QCanvasRectangle(xOff + xscale-1, yOff-10, 1, 6,  self.canvasL);  tick3.show()
        self.rectItems = [line, tick1, tick2, tick3]
        for i in range(10):
            tick = QCanvasRectangle(xOff + xscale * (float(i)/10.0), yOff-8, 1, 5, self.canvasL);
            tick.show()
            self.rectItems.append(tick)
        
        text1 = QCanvasText("0%", self.canvasL);   text1.setTextFlags(Qt.AlignHCenter); text1.move(xOff, yOff - 23); text1.show()
        text2 = QCanvasText("50%", self.canvasL);  text2.setTextFlags(Qt.AlignHCenter); text2.move(xOff + xscale/2, yOff - 23); text2.show()
        text3 = QCanvasText("100%", self.canvasL); text3.setTextFlags(Qt.AlignHCenter); text3.move(xOff + xscale, yOff - 23); text3.show()
        text4 = QCanvasText("Class entropy removed", self.canvasL); text4.setTextFlags(Qt.AlignHCenter); text4.move(xOff + xscale/2, yOff - 36); text4.show()
        self.rectItems.append(text1); self.rectItems.append(text2); self.rectItems.append(text3); self.rectItems.append(text4)

        ################################
        #create rectangles
        for ((total, (gain1, gain2, attrIndex1, attrIndex2))) in self.interactionList:
            if not self.showInteractionPair(attrIndex1, attrIndex2): continue
            
            interaction = (total - gain1 - gain2)
            rectsYOff = yOff + index * yscale * 0.15

            x1 = round(xOff)
            if interaction < 0:
                x2 = floor(xOff + xscale*(gain1+interaction))
                x3 = ceil(xOff + xscale*gain1)
            else:
                x2 = floor(xOff + xscale*gain1)
                x3 = ceil(xOff + xscale*(total-gain2))
            x4 = ceil(xOff + xscale*total)

            rect1 = QCanvasRectangle(x1, rectsYOff, x2-x1, rectHeight, self.canvasL)
            rect2 = QCanvasRectangle(x2, rectsYOff,   x3-x2, rectHeight, self.canvasL)
            rect3 = QCanvasRectangle(x3, rectsYOff, x4-x3, rectHeight, self.canvasL)
            if interaction < 0.0:
                #color = QColor(255, 128, 128)
                color = QColor(200, 0, 0)
                style = Qt.DiagCrossPattern
            else:
                color = QColor(Qt.green)
                style = Qt.Dense5Pattern

            brush1 = QBrush(Qt.blue); brush1.setStyle(Qt.BDiagPattern)
            brush2 = QBrush(color);   brush2.setStyle(style)
            brush3 = QBrush(Qt.blue); brush3.setStyle(Qt.FDiagPattern)
            
            rect1.setBrush(brush1); rect1.setPen(QPen(QColor(Qt.blue)))
            rect2.setBrush(brush2); rect2.setPen(QPen(color))
            rect3.setBrush(brush3); rect3.setPen(QPen(QColor(Qt.blue)))
            rect1.show(); rect2.show();  rect3.show()

            # create text labels
            text1 = QCanvasText(self.data.domain[attrIndex1].name, self.canvasL)
            text2 = QCanvasText(self.data.domain[attrIndex2].name, self.canvasL)
            text1.setTextFlags(Qt.AlignRight)
            text2.setTextFlags(Qt.AlignLeft)
            text1.move(xOff - 5, rectsYOff + 3)
            text2.move(xOff + xscale*total + 5, rectsYOff + 3)
            
            text1.show()
            text2.show()

            # compute line width
            rect = text2.boundingRect()
            lineWidth = xOff + xscale*total + 5 + rect.width() + 10
            if  lineWidth > maxWidth:
                maxWidth = lineWidth 

            if rectsYOff + rectHeight + 10 > maxHeight:
                maxHeight = rectsYOff + rectHeight + 10

            self.interactionRects.append((rect1, rect2, rect3, text1, text2))
            index += 1

        self.canvasL.resize(maxWidth + 10, maxHeight)
        self.canvasViewL.setMaximumSize(QSize(maxWidth + 30, max(2000, maxHeight)))
        self.canvasViewL.setMinimumWidth(0)

        self.canvasL.update()

    # parse info from plain file. picWidth and picHeight are sizes in pixels
    def parseGraphData(self, textPlainList, picWidth, picHeight):
        scale = 0
        w = 1; h = 1
        for line in textPlainList:
            if line[:9] == "rectangle":
                list = line.split()
                topLeftRectStr = list[1]
                bottomRightRectStr = list[2]
                attrIndex = list[3]
                
                isAttribute = 0     # does rectangle represent attribute
                if attrIndex.find("-") < 0:
                    isAttribute = 1
                
                topLeftRectStr = topLeftRectStr.replace("(","")
                bottomRightRectStr = bottomRightRectStr.replace("(","")
                topLeftRectStr = topLeftRectStr.replace(")","")
                bottomRightRectStr = bottomRightRectStr.replace(")","")
                
                topLeftRectList = topLeftRectStr.split(",")
                bottomRightRectList = bottomRightRectStr.split(",")
                xLeft = int(topLeftRectList[0])
                yTop = int(topLeftRectList[1])
                width = int(bottomRightRectList[0]) - xLeft
                height = int(bottomRightRectList[1]) - yTop

                rect = QCanvasRectangle(xLeft+2, yTop+2, width, height, self.canvasR)
                pen = QPen(Qt.green)
                pen.setWidth(4)
                rect.setPen(pen)
                rect.hide()
                
                if isAttribute == 1:
                    name = self.data.domain[int(attrIndex)].name
                    self.rectIndices[int(attrIndex)] = rect
                    self.rectNames[name] = rect
                else:
                    attrs = attrIndex.split("-")
                    attr1 = self.data.domain[int(attrs[0])].name
                    attr2 = self.data.domain[int(attrs[1])].name
                    pen.setStyle(Qt.NoPen)
                    rect.setPen(pen)
                    self.lines.append((attr1, attr2, rect))
    
    def initLists(self, data):
        self.shownAttribsLB.clear()
        self.hiddenAttribsLB.clear()

        if data == None: return

        for key in self.rectNames.keys():
            self._setAttrVisible(key, 1)


    #################################################
    ### showing and hiding attributes
    #################################################
    def _showAttribute(self, name):
        self.shownAttribsLB.insertItem(name)    # add to shown

        count = self.hiddenAttribsLB.count()
        for i in range(count-1, -1, -1):        # remove from hidden
            if str(self.hiddenAttribsLB.text(i)) == name:
                self.hiddenAttribsLB.removeItem(i)

    def _hideAttribute(self, name):
        self.hiddenAttribsLB.insertItem(name)    # add to hidden

        count = self.shownAttribsLB.count()
        for i in range(count-1, -1, -1):        # remove from shown
            if str(self.shownAttribsLB.text(i)) == name:
                self.shownAttribsLB.removeItem(i)

    ##########
    # add attribute to showList or hideList and show or hide its rectangle
    def _setAttrVisible(self, name, visible = 1):
        if visible == 1:
            if name in self.rectNames.keys(): self.rectNames[name].show();
            self._showAttribute(name)
        else:
            if name in self.rectNames.keys(): self.rectNames[name].hide();
            self._hideAttribute(name)

    def getAttrVisible(self, name):
        for i in range(self.shownAttribsLB.count()):
            if str(self.shownAttribsLB.text(i)) == name: return 1
        return 0

    #################################################
    # event processing
    #################################################
    def addAttributeClick(self):
        count = self.hiddenAttribsLB.count()
        for i in range(count-1, -1, -1):
            if self.hiddenAttribsLB.isSelected(i):
                name = str(self.hiddenAttribsLB.text(i))
                self._setAttrVisible(name, 1)
        self.showInteractionRects()
        self.canvasL.update()
        self.canvasR.update()

    def removeAttributeClick(self):
        count = self.shownAttribsLB.count()
        for i in range(count-1, -1, -1):
            if self.shownAttribsLB.isSelected(i):
                name = str(self.shownAttribsLB.text(i))
                self._setAttrVisible(name, 0)
        self.showInteractionRects()
        self.canvasL.update()
        self.canvasR.update()

    ##################################################
    # SAVING GRAPHS
    ##################################################
    def saveToFileLCanvas(self):
        self.saveCanvasToFile(self.canvasViewL, self.canvasL.size())

    def saveToFileRCanvas(self):
        self.saveCanvasToFile(self.canvasViewR, self.canvasR.size())
        
    def saveCanvasToFile(self, canvas, size):
        qfileName = QFileDialog.getSaveFileName("graph.png","Portable Network Graphics (.PNG)\nWindows Bitmap (.BMP)\nGraphics Interchange Format (.GIF)", None, "Save to..")
        fileName = str(qfileName)
        if fileName == "": return
        (fil,ext) = os.path.splitext(fileName)
        ext = ext.replace(".","")
        ext = ext.upper()
        
        buffer = QPixmap(size) # any size can do, now using the window size
        painter = QPainter(buffer)
        painter.fillRect(buffer.rect(), QBrush(QColor(255, 255, 255))) # make background same color as the widget's background
        canvas.drawContents(painter, 0,0, size.width(), size.height())
        painter.end()
        buffer.save(fileName, ext)


#test widget appearance
if __name__=="__main__":
    a=QApplication(sys.argv)
    ow=OWInteractionGraph()
    a.setMainWidget(ow)
    ow.show()
    a.exec_loop()

    #save settings 
    ow.saveSettings()
