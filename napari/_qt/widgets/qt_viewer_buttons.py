from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QMenu, QPushButton

from ...utils.interactions import KEY_SYMBOLS


class QtLayerButtons(QFrame):
    """Button controls for napari layers.

    Parameters
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.

    Attributes
    ----------
    deleteButton : QtDeleteButton
        Button to delete selected layers.
    newLabelsButton : QtViewerPushButton
        Button to add new Label layer.
    newPointsButton : QtViewerPushButton
        Button to add new Points layer.
    newShapesButton : QtViewerPushButton
        Button to add new Shapes layer.
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.
    """

    def __init__(self, viewer):
        super().__init__()

        self.viewer = viewer
        self.deleteButton = QtDeleteButton(self.viewer)

        context_menu = QMenu()
        for n in range(2, 6):
            context_menu.addAction(f'add {n}D points layer')

        self.newPointsButton = QtViewerPushButton(
            self.viewer,
            'new_points',
            'New points layer',
            slot=lambda: self.viewer.add_points(
                ndim=max(self.viewer.dims.ndim, 2),
                scale=self.viewer.layers.extent.step,
            ),
            secondary_slot=lambda: context_menu.popup(QCursor.pos()),
        )

        self.newShapesButton = QtViewerPushButton(
            self.viewer,
            'new_shapes',
            'New shapes layer',
            lambda: self.viewer.add_shapes(
                ndim=max(self.viewer.dims.ndim, 2),
                scale=self.viewer.layers.extent.step,
            ),
        )
        self.newLabelsButton = QtViewerPushButton(
            self.viewer,
            'new_labels',
            'New labels layer',
            lambda: self.viewer._new_labels(),
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.newPointsButton)
        layout.addWidget(self.newShapesButton)
        layout.addWidget(self.newLabelsButton)
        layout.addStretch(0)
        layout.addWidget(self.deleteButton)
        self.setLayout(layout)

    @property
    def _points_button_context_menu(self):
        print('in QMenu creation')
        context_menu = QMenu()
        for n in range(2, 6):
            context_menu.addAction(f'add {n}D points layer')
        return context_menu

    def _popup_context_menu(self):
        print('in popup method')
        print(QCursor.pos())
        print(self._points_button_context_menu.actions())
        self._points_button_context_menu.popup(QCursor.pos())


class QtViewerButtons(QFrame):
    """Button controls for the napari viewer.

    Parameters
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.

    Attributes
    ----------
    consoleButton : QtViewerPushButton
        Button to open iPython console within napari.
    rollDimsButton : QtViewerPushButton
        Button to roll orientation of spatial dimensions in the napari viewer.
    transposeDimsButton : QtViewerPushButton
        Button to transpose dimensions in the napari viewer.
    resetViewButton : QtViewerPushButton
        Button resetting the view of the rendered scene.
    gridViewButton : QtGridViewButton
        Button to toggle grid view mode of layers on and off.
    ndisplayButton : QtNDisplayButton
        Button to toggle number of displayed dimensions.
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.
    """

    def __init__(self, viewer):
        super().__init__()

        self.viewer = viewer
        self.consoleButton = QtViewerPushButton(
            self.viewer,
            'console',
            f"Open IPython terminal ({KEY_SYMBOLS['Control']}-{KEY_SYMBOLS['Shift']}-C)",
        )
        self.consoleButton.setProperty('expanded', False)
        self.rollDimsButton = QtViewerPushButton(
            self.viewer,
            'roll',
            f"Roll dimensions order for display ({KEY_SYMBOLS['Control']}-E)",
            lambda: self.viewer.dims._roll(),
        )
        self.transposeDimsButton = QtViewerPushButton(
            self.viewer,
            'transpose',
            f"Transpose displayed dimensions ({KEY_SYMBOLS['Control']}-T)",
            lambda: self.viewer.dims._transpose(),
        )
        self.resetViewButton = QtViewerPushButton(
            self.viewer,
            'home',
            f"Reset view ({KEY_SYMBOLS['Control']}-R)",
            lambda: self.viewer.reset_view(),
        )
        self.gridViewButton = QtGridViewButton(self.viewer)
        self.ndisplayButton = QtNDisplayButton(self.viewer)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.consoleButton)
        layout.addWidget(self.ndisplayButton)
        layout.addWidget(self.rollDimsButton)
        layout.addWidget(self.transposeDimsButton)
        layout.addWidget(self.gridViewButton)
        layout.addWidget(self.resetViewButton)
        layout.addStretch(0)
        self.setLayout(layout)


class QtDeleteButton(QPushButton):
    """Delete button to remove selected layers.

    Parameters
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.

    Attributes
    ----------
    hover : bool
        Hover is true while mouse cursor is on the button widget.
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.
    """

    def __init__(self, viewer):
        super().__init__()

        self.viewer = viewer
        self.setToolTip(
            f"Delete selected layers ({KEY_SYMBOLS['Control']}-{KEY_SYMBOLS['Backspace']})"
        )
        self.setAcceptDrops(True)
        self.clicked.connect(lambda: self.viewer.layers.remove_selected())

    def dragEnterEvent(self, event):
        """The cursor enters the widget during a drag and drop operation.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        event.accept()
        self.hover = True
        self.update()

    def dragLeaveEvent(self, event):
        """The cursor leaves the widget during a drag and drop operation.

        Using event.ignore() here allows the event to pass through the
        parent widget to its child widget, otherwise the parent widget
        would catch the event and not pass it on to the child widget.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        event.ignore()
        self.hover = False
        self.update()

    def dropEvent(self, event):
        """The drag and drop mouse event is completed.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        event.accept()
        layer_name = event.mimeData().text()
        layer = self.viewer.layers[layer_name]
        if not layer.selected:
            self.viewer.layers.remove(layer)
        else:
            self.viewer.layers.remove_selected()


class QtViewerPushButton(QPushButton):
    """Push button.

    Parameters
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.

    Attributes
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.
    """

    def __init__(
        self, viewer, button_name, tooltip=None, slot=None, secondary_slot=None
    ):
        super().__init__()

        self.viewer = viewer
        self.setToolTip(tooltip or button_name)
        self.setProperty('mode', button_name)
        if slot is not None:
            self.clicked.connect(slot)

        if secondary_slot is not None:
            # Enable context menu on secondary click
            # https://doc.qt.io/qt-5/qt.html#ContextMenuPolicy-enum
            self.setContextMenuPolicy(Qt.ContextMenuPolicy(3))
            self.customContextMenuRequested.connect(secondary_slot)


class QtGridViewButton(QCheckBox):
    """Button to toggle grid view mode of layers on and off.

    Parameters
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.

    Attributes
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.
    """

    def __init__(self, viewer):
        super().__init__()

        self.viewer = viewer
        self.setToolTip(f"Toggle grid view ({KEY_SYMBOLS['Control']}-G)")
        self.viewer.grid.events.connect(self._on_grid_change)
        self.stateChanged.connect(self.change_grid)
        self._on_grid_change()

    def change_grid(self, state):
        """Toggle between grid view mode and (the ordinary) stack view mode.

        Parameters
        ----------
        state : qtpy.QtCore.Qt.CheckState
            State of the checkbox.
        """
        self.viewer.grid.enabled = not state == Qt.Checked

    def _on_grid_change(self, event=None):
        """Update grid layout size.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        with self.viewer.grid.events.blocker():
            self.setChecked(not self.viewer.grid.enabled)


class QtNDisplayButton(QCheckBox):
    """Button to toggle number of displayed dimensions.

    Parameters
    ----------
    viewer : napari.components.ViewerModel
        Napari viewer containing the rendered scene, layers, and controls.
    """

    def __init__(self, viewer):
        super().__init__()

        self.viewer = viewer
        self.setToolTip(
            f"Toggle number of displayed dimensions ({KEY_SYMBOLS['Control']}-Y)"
        )
        self.viewer.dims.events.ndisplay.connect(self._on_ndisplay_change)

        self.setChecked(self.viewer.dims.ndisplay == 3)
        self.stateChanged.connect(self.change_ndisplay)

    def change_ndisplay(self, state):
        """Toggle between 2D and 3D display.

        Parameters
        ----------
        state : bool
            If state is True the display view is 3D, if False display is 2D.
        """
        if state == Qt.Checked:
            self.viewer.dims.ndisplay = 3
        else:
            self.viewer.dims.ndisplay = 2

    def _on_ndisplay_change(self, event=None):
        """Update number of displayed dimensions, while blocking events.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent, optional
            Event from the Qt context.
        """
        with self.viewer.dims.events.ndisplay.blocker():
            self.setChecked(self.viewer.dims.ndisplay == 3)
