import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui

Item {
  id: root

  property bool opened: false

  function open() {
    root.opened = true
  }

  function close() {
    root.opened = false
  }

  function toggle() {
    if (root.opened) {
      root.close()
    } else {
      root.open()
    }
  }



  PanelWindow {
    id: panel
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-omail"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    exclusionMode: ExclusionMode.Ignore

    Rectangle {
      anchors.fill: parent
      color: "#80000000" // Scrim
    }

    MouseArea {
      anchors.fill: parent
      onClicked: root.close()
    }

    Rectangle {
      width: 500
      height: 600
      anchors.centerIn: parent
      color: "#1e1e2e"
      border.color: "#313244"
      border.width: 2
      radius: 12

      MouseArea { anchors.fill: parent }

      Column {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        Text {
          text: "📧 Bandeja de Entrada (OMAIL)"
          color: "white"
          font.pixelSize: 22
          font.bold: true
        }

        Text {
          text: "Aquí se cargarán tus correos no leídos..."
          color: "#bac2de"
          font.pixelSize: 16
        }
      }
    }
  }
}
