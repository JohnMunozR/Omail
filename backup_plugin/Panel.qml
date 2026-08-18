import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "custom.omail"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null

  function open() {
    root.controller.show()
  }

  function close() {
    root.controller.hide()
  }

  function toggle() {
    root.opened ? root.close() : root.open()
  }

  KeyboardPanel {
    id: panelSurface
    controller: root.controller
    anchorItem: root.anchorItem
    width: 400
    height: 500

    PanelKeyCatcher {
      anchors.fill: parent
      onEscape: root.close()

      Rectangle {
        anchors.fill: parent
        color: "#1e1e2e"
        border.color: "#313244"
        radius: 8

        Column {
          anchors.fill: parent
          anchors.margins: 16
          spacing: 12

          Text {
            text: "Bandeja de Entrada"
            color: "white"
            font.pixelSize: 18
            font.bold: true
          }

          Text {
            text: "Aquí irán los correos..."
            color: "#bac2de"
          }
        }
      }
    }
  }
}
