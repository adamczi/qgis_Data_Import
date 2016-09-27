# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DataImport
                                 A QGIS plugin
 This plugin lets you download Polish administrative data
                              -------------------
        begin                : 2016-09-20
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Adam Borczyk
        email                : ad.borczyk@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QSettings
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QToolBar
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsFeature, QgsGeometry
from qgis.gui import QgsMessageBar
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from data_import_dialog import DataImportDialog
import os.path
import urllib, json, subprocess

class DataImport:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DataImport_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = DataImportDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Location Intelligence')

        ## Add to LI tooblar or create if doesn't exist
        toolbarName = 'Location Intelligence'
        self.toolbar = self.iface.mainWindow().findChild(QToolBar,toolbarName)

        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar(toolbarName)
            self.toolbar.setObjectName(toolbarName)       

        ##
        self.url = 'http://127.0.0.1:5000'

        ## Read API keys from QSettings
        self.readKeys()
        

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DataImport', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/DataImport/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Import data'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Data Import'),
                action)
            self.iface.removeToolBarIcon(action)

        ## remove the toolbar
        if len(self.toolbar.actions())==0:
            del self.toolbar

    def fileWindow(self):
        """ Prepare window for file saving """
        self.fileDialog = QFileDialog()
        self.fileDialog.setWindowTitle('Save file')
        self.fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        self.fileDialog.setFileMode(QFileDialog.AnyFile)
        self.fileDialog.setViewMode(QFileDialog.Detail)        

    def readKeys(self):
        """ Load API key from global QGIS settings """
        s = QSettings()
        self.dlg.lineEdit.setText(s.value("data_import/gs_key"))

    def saveKeys(self):
        """ Save API key to global QGIS settings, so user doesn't need to input it every time """
        gs_key = 'none' if self.dlg.lineEdit.text() == '' else self.dlg.lineEdit.text()

        s = QSettings()
        s.setValue("data_import/gs_key", gs_key)

    def prepareList(self):
        """ Fill list of available layers """
        self.dlg.comboBox.clear()

        queryString = '%s/layers' % self.url
        response = urllib.urlopen(queryString)
        data = json.loads(response.read())

        self.dlg.comboBox.addItems(data)

    def getGeometry(self, path, key):
        """ Run server query and load returned file by its path """

        ## Get layer name
        region = self.dlg.comboBox.currentText()
        
        ## Append 'path' to path, so Flask won't cut '/home' in case of unix path
        ## Strips 'path' on the Flask side.
        path = 'path'+path

        queryString = '%s/%s/%s/%s' % (self.url, key, region, path)

        ## If any path specified
        if len(path)>5:            
            try:
                ## Run query
                urllib.urlopen(queryString)

                ## Load file to QGIS
                self.openFile(path[4:])
            except:
                print 'couldnt get the data'

    def openFile(self, path):
        """ Load file to QGIS """
        layer = self.iface.addVectorLayer(path, self.dlg.comboBox.currentText(), "ogr")
        if not layer:
          print "Layer failed to load!"

    def run(self):
        """Run method that performs all the real work"""
        try:
            ## Prepare "Save file" window
            self.fileWindow()

            ## Fill list of available layers
            self.prepareList()

            # show the dialog
            self.dlg.show()
            # Run the dialog event loop
            result = self.dlg.exec_()
            # See if OK was pressed
            if result:
                ## Get selected download path and API key
                dl_path = self.fileDialog.getSaveFileName(self.fileDialog, 'Save file', filter = '*.shp')
                key = self.dlg.lineEdit.text()

                ## Main function here
                self.getGeometry(dl_path, key)
                
                ## Save API keys
                self.saveKeys()
        except IOError:
            self.iface.messageBar().pushMessage("Error", "Service not available", level=QgsMessageBar.CRITICAL, duration=5)