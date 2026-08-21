import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

// Email counter for the bar, and the host for the popup panel.
BarWidget {
  id: root
  moduleName: "nmr.omail"

  property string unreadCount: "?"
  property string omailError: ""
  property string activeEmail: ""
  property var emailsList: []
  property bool isFetching: false
  property bool isConnected: false
  property bool isLoadingMore: false
  property bool allLoaded: false
  property bool isSavingCreds: false

  // Force minimum visibility and display string
  readonly property string displayText: "󰇰"
  readonly property var verticalLines: [displayText]

  function refresh() {
    if (!isFetching) {
      isConnected = false
      isFetching = true
      fetchProcess.running = true
    }
  }

  function saveCredentials(email, pass) {
    omailError = "NOT_LOGGED_IN"
    isSavingCreds = true
    saveCredsProc.command = ["python3", "-c", "import sys, json, os; os.makedirs(os.path.expanduser('~/.config/omail'), exist_ok=True); json.dump({'email': sys.argv[1], 'app_password': sys.argv[2]}, open(os.path.expanduser('~/.config/omail/credentials.json'), 'w'))", email, pass]
    saveCredsProc.running = true
  }

  function unlinkAccount() {
    unlinkProc.running = true
  }

  function loadMoreEmails() {
    if (isLoadingMore || allLoaded || !emailsList) return
    isLoadingMore = true
    var currentOffset = emailsList.length
    fetchMoreProcess.command = ["python3", "/home/nmr/Projects/omail/daemon/fetch_gmail.py", "--offset", String(currentOffset), "--limit", "20"]
    fetchMoreProcess.running = true
  }

  // ---- Panel popup routing
  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false

  function open() {
    if (panelLoader.item) panelLoader.item.open()
  }

  function close() {
    if (panelLoader.item) panelLoader.item.close()
  }

  function togglePanel() {
    if (panelLoader.item) panelLoader.item.toggle()
  }

  readonly property real openPanelIndicatorWidth: button.width
  readonly property real openPanelIndicatorHeight: Math.max(Style.space(10), Math.round(Style.bar.iconSlot * 0.55))

  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false

  function closeForPopoutSwitch() {
    if (panelLoader.item) panelLoader.item.closeForPopoutSwitch()
  }

  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()

  Process {
    id: saveCredsProc
    onExited: {
      root.isSavingCreds = false
      root.refresh()
    }
  }

  Process {
    id: unlinkProc
    command: ["rm", "-f", Quickshell.env("HOME") + "/.config/omail/credentials.json"]
    onExited: {
      root.emailsList = []
      root.unreadCount = "?"
      root.omailError = "NOT_LOGGED_IN"
    }
  }

  Process {
    id: fetchMoreProcess
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var text = String(fetchMoreProcess.stdout.text || "").trim()
          if (text) {
            var result = JSON.parse(text)
            if (result.emails && result.emails.length > 0) {
              var currentList = root.emailsList
              for (var i = 0; i < result.emails.length; i++) {
                currentList.push(result.emails[i])
              }
              root.emailsList = currentList
            } else {
              root.allLoaded = true
            }
          }
        } catch(e) {
          console.log("Error parsing lazy load JSON:", e)
        }
        root.isLoadingMore = false
      }
    }
    onExited: {
      root.isLoadingMore = false
    }
  }

  Process {
    id: fetchProcess
    command: ["python3", Quickshell.env("HOME") + "/Projects/omail/daemon/fetch_gmail.py"]
    onExited: root.isFetching = false
    stdout: SplitParser {
      onRead: function(data) {
        try {
          var parsed = JSON.parse(data)
          if (parsed.status === "CONNECTED") {
             root.isConnected = true
             return
          }
          if (parsed.error) {
             root.omailError = parsed.error
             root.unreadCount = "?"
             root.emailsList = []
             root.activeEmail = ""
          } else {
             root.omailError = ""
             root.unreadCount = String(parsed.unread_count)
             root.emailsList = parsed.emails
             if (parsed.user_email) root.activeEmail = parsed.user_email
          }
        } catch(e) {
          root.omailError = "Error de parseo JSON"
          root.unreadCount = "?"
        }
      }
    }
  }

  Timer {
    interval: 60000 // Cada minuto
    running: true
    repeat: true
    onTriggered: root.refresh()
  }

  Component.onCompleted: root.refresh()

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  IpcHandler {
    target: "nmr.omail"

    function refresh(): void { root.refresh() }
    function open(): void { root.open() }
    function close(): void { root.close() }
    function show(): void { root.open() }
    function hide(): void { root.close() }
    function toggle(): void { root.togglePanel() }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    slotSize: Style.bar.statusSlot
    text: root.displayText

    onPressed: function(b) {
      if (b === Qt.RightButton) root.refresh() // Click derecho refresca
      else root.togglePanel()
    }
  }
}
