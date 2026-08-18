import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui

Item {
    id: root

    property bool opened: true
    property int unreadCount: 0
    // Mocking history for now, but this will read the Python JSON.
    property var history: [{"subject": "Test Email", "from": "John Doe", "date": "Now"}]

    function open() { root.opened = true }
    function close() { root.opened = false }
    function toggle() { root.opened ? root.close() : root.open() }

    IpcHandler {
        target: "custom.omail"
        function toggle(): void { root.toggle() }
        function open(): void { root.open() }
        function close(): void { root.close() }
    }

    Timer {
        interval: 60000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            console.log("Fetching emails...");
        }
    }

    PanelWindow {
        id: panel
        visible: root.opened
        anchors { top: true; bottom: true; left: true; right: true }
        color: "transparent"
        WlrLayershell.namespace: "omail-overlay"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        exclusionMode: ExclusionMode.Ignore

        // Scrim background (oscurece la pantalla)
        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(0, 0, 0, 0.7)
        }

        // Clicar fuera cierra el overlay
        MouseArea {
            anchors.fill: parent
            onClicked: root.close()
        }

        // El panel de correos real
        Rectangle {
            width: Math.min(800, parent.width * 0.8)
            height: Math.min(600, parent.height * 0.8)
            anchors.centerIn: parent
            color: "#1e1e2e" // Tema oscuro elegante
            radius: 12
            border.color: "#313244"
            border.width: 1

            // Previene que los clics dentro del panel lo cierren
            MouseArea { anchors.fill: parent; onClicked: {} }

            Column {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 16

                Text {
                    text: "Bandeja de Omail"
                    color: "white"
                    font.pixelSize: 24
                    font.bold: true
                }

                ListView {
                    width: parent.width
                    height: parent.height - 60
                    model: root.history
                    spacing: 8
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 70
                        color: "#313244"
                        radius: 8

                        Column {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            Text {
                                text: modelData.from + " - " + modelData.date
                                color: "#bac2de"
                                font.pixelSize: 12
                            }
                            Text {
                                text: modelData.subject
                                color: "white"
                                font.pixelSize: 16
                                font.bold: true
                            }
                        }
                    }
                }
            }
        }
    }
}
