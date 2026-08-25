import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "nmr.omail"
  ipcTarget: "nmr.omail"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  readonly property var barIdentity: hostWidget || root

  readonly property color contentForeground: bar ? bar.foreground : Color.foreground
  readonly property string contentFontFamily: bar ? bar.fontFamily : Style.font.family

  property string activeFilter: "Inbox"
  property bool isLoadingMore: root.hostWidget ? root.hostWidget.isLoadingMore : false
  property bool allLoaded: root.hostWidget ? root.hostWidget.allLoaded : false

  function loadMoreEmails() {
    if (root.hostWidget) root.hostWidget.loadMoreEmails()
  }


  function open() {
    root.controller.show()
    Qt.callLater(function() {
      if (root.opened) setCenterHoverRevealSuppressed(true)
    })
  }

  function close() {
    setCenterHoverRevealSuppressed(false)
    root.controller.hide()
    
    // Clear lazy-loaded emails from memory to free cache
    if (root.hostWidget && root.hostWidget.emailsList && root.hostWidget.emailsList.length > 60) {
      root.hostWidget.emailsList = root.hostWidget.emailsList.slice(0, 60)
      root.hostWidget.allLoaded = false
    }
  }

  function toggle() {
    if (root.opened) root.close()
    else root.open()
  }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.barIdentity, direction)
    return false
  }

  function setCenterHoverRevealSuppressed(value) {
    if (root.bar && "centerHoverRevealSuppressed" in root.bar)
      root.bar.centerHoverRevealSuppressed = value
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.barIdentity
    bar: root.bar
    open: root.opened
    centerOnBar: true
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(400))
    contentHeight: panel.fittedContentHeight(mainColumn.implicitHeight)

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      Flickable {
        id: scroll
        anchors.fill: parent
        contentWidth: mainColumn.width
        contentHeight: mainColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: contentHeight > height

        onAtYEndChanged: {
          if (atYEnd && interactive) {
            root.loadMoreEmails()
          }
        }

        Column {
          id: mainColumn
          width: scroll.width
          spacing: Style.space(12)

          Item {
            width: parent.width
            height: Style.space(40)
            visible: root.hostWidget && root.hostWidget.omailError !== "NOT_LOGGED_IN" && root.hostWidget.omailError !== "AUTH_FAILED"

            Flickable {
              anchors.left: parent.left
              anchors.right: userEmailText.left
              anchors.rightMargin: Style.space(16)
              anchors.verticalCenter: parent.verticalCenter
              height: Style.space(24)
              contentWidth: filterRow.width
              contentHeight: height
              clip: true
              interactive: contentWidth > width

              Row {
                id: filterRow
                spacing: Style.space(8)
                
                Repeater {
                  model: ["Inbox", "All"]
                  delegate: Rectangle {
                    property bool isSelected: root.activeFilter === modelData
                    width: filterText.implicitWidth + Style.space(16)
                    height: Style.space(24)
                    radius: Style.cornerRadius
                    color: isSelected ? Style.selectedStateColor(root.contentForeground, Color.accent) : "transparent"
                    border.width: isSelected ? 0 : Style.spacing.hairline
                    border.color: isSelected ? "transparent" : Qt.rgba(root.contentForeground.r, root.contentForeground.g, root.contentForeground.b, 0.3)
                    
                    Text {
                      id: filterText
                      anchors.centerIn: parent
                      text: modelData
                      color: isSelected ? (root.bar ? root.bar.background : "#000000") : root.contentForeground
                      font.family: root.contentFontFamily
                      font.pixelSize: Style.font.caption
                      font.bold: isSelected
                    }
                    
                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: root.activeFilter = modelData
                    }
                  }
                }
              }
            }

            Text {
              id: userEmailText
              anchors.right: unlinkBtn.left
              anchors.rightMargin: Style.space(12)
              anchors.verticalCenter: parent.verticalCenter
              width: Math.min(implicitWidth, parent.width * 0.45)
              elide: Text.ElideMiddle
              text: root.hostWidget ? root.hostWidget.activeEmail : ""
              color: Qt.darker(root.contentForeground, 1.5)
              font.family: root.contentFontFamily
              font.pixelSize: Style.font.caption
            }

            PanelActionButton {
              id: unlinkBtn
              anchors.right: refreshBtn.left
              anchors.rightMargin: Style.space(8)
              anchors.verticalCenter: parent.verticalCenter
              iconText: ""
              tooltipText: "Unlink Account"
              foreground: root.contentForeground
              fontFamily: root.contentFontFamily
              onClicked: {
                if (root.hostWidget) root.hostWidget.unlinkAccount()
              }
            }

            PanelActionButton {
              id: refreshBtn
              anchors.right: parent.right
              anchors.verticalCenter: parent.verticalCenter
              iconText: "󰑐"
              tooltipText: "Refresh"
              foreground: root.contentForeground
              fontFamily: root.contentFontFamily
              onClicked: {
                if (root.hostWidget) root.hostWidget.refresh()
              }
            }
          }

          Column {
             visible: root.hostWidget && (root.hostWidget.omailError === "NOT_LOGGED_IN" || root.hostWidget.omailError === "AUTH_FAILED")
             width: parent.width
             spacing: Style.space(16)
             
             Text {
                text: "Sign in to Google"
                color: root.contentForeground
                font.family: root.contentFontFamily
                font.pixelSize: Style.font.heading
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
             }

             Text {
                visible: root.hostWidget && root.hostWidget.omailError === "AUTH_FAILED"
                text: "Invalid email or App Password. Please try again."
                color: "#ff5555"
                font.family: root.contentFontFamily
                font.pixelSize: Style.font.bodySmall
                anchors.horizontalCenter: parent.horizontalCenter
             }
             
             TextField {
                id: emailInput
                width: parent.width
                placeholderText: "Email address"
             }

             TextField {
                id: passInput
                width: parent.width
                password: true
                placeholderText: "App Password"
             }

             Button {
                text: (root.hostWidget && root.hostWidget.isSavingCreds) || (root.hostWidget && root.hostWidget.isFetching && !root.hostWidget.isConnected) ? "Verifying credentials..." :
                      (root.hostWidget && root.hostWidget.isFetching && root.hostWidget.isConnected) ? "Downloading emails..." : "Link Account"
                width: parent.width
                enabled: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.text) && passInput.text.length > 0 && !(root.hostWidget && (root.hostWidget.isFetching || root.hostWidget.isSavingCreds))
                onClicked: {
                   if (root.hostWidget) root.hostWidget.saveCredentials(emailInput.text, passInput.text)
                }
             }
          }

          Rectangle {
            visible: root.hostWidget && root.hostWidget.omailError !== "NOT_LOGGED_IN" && root.hostWidget.omailError !== "AUTH_FAILED"
            width: parent.width
            height: Style.spacing.hairline
            color: root.contentForeground
            opacity: 0.1
          }

          Text {
            visible: root.hostWidget && root.hostWidget.omailError !== "" && root.hostWidget.omailError !== "NOT_LOGGED_IN" && root.hostWidget.omailError !== "AUTH_FAILED"
            width: parent.width
            text: root.hostWidget ? root.hostWidget.omailError : ""
            color: "#ff5555"
            font.family: root.contentFontFamily
            font.pixelSize: Style.font.body
            wrapMode: Text.Wrap
          }

          Text {
            visible: emailsRepeater.count === 0 && root.hostWidget && !root.hostWidget.isFetching && root.hostWidget.omailError === "" && root.hostWidget.omailError !== "NOT_LOGGED_IN" && root.hostWidget.omailError !== "AUTH_FAILED"
            width: parent.width
            text: "No emails in " + root.activeFilter
            color: Qt.darker(root.contentForeground, 1.5)
            font.family: root.contentFontFamily
            font.pixelSize: Style.font.body
            horizontalAlignment: Text.AlignHCenter
          }

          Repeater {
            id: emailsRepeater
            model: {
              if (!root.hostWidget) return []
              var list = root.hostWidget.emailsList || []
              var filtered = []
              for (var i = 0; i < list.length; ++i) {
                if (root.activeFilter === "All" || list[i].category === root.activeFilter) {
                  filtered.push(list[i])
                }
              }
              return filtered
            }
            delegate: Rectangle {
              id: emailRect
              property bool isExpanded: false
              property bool markedRead: false
              property bool isUnread: modelData.is_unread === true && !markedRead
              property bool matchesFilter: root.hostWidget && root.hostWidget.omailError !== "NOT_LOGGED_IN" && root.hostWidget.omailError !== "AUTH_FAILED" && (root.activeFilter === "All" || (modelData.category && modelData.category === root.activeFilter))

              visible: matchesFilter
              width: mainColumn.width
              height: matchesFilter ? (emailColumn.implicitHeight + Style.space(16)) : 0
              color: mouseArea.containsMouse ? Style.hoverFillFor(root.contentForeground, Color.accent) : "transparent"
              radius: Style.cornerRadius
              border.width: Style.spacing.hairline
              border.color: Qt.rgba(root.contentForeground.r, root.contentForeground.g, root.contentForeground.b, 0.15)
              clip: true

              Behavior on height { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

              MouseArea {
                id: mouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                
                onClicked: function(mouse) {
                  if (mouse.button === Qt.LeftButton) {
                    emailRect.isExpanded = !emailRect.isExpanded
                    if (emailRect.isExpanded && emailRect.isUnread) {
                      emailRect.markedRead = true
                      if (root.hostWidget) root.hostWidget.markEmailRead(modelData.uid)
                    }
                  } else if (mouse.button === Qt.MiddleButton) {
                    if (modelData.url) {
                      Qt.openUrlExternally(modelData.url)
                      root.close()
                    }
                  }
                }
                
                onDoubleClicked: function(mouse) {
                  if (mouse.button === Qt.LeftButton) {
                    if (modelData.url) {
                      Qt.openUrlExternally(modelData.url)
                      root.close()
                    }
                  }
                }
              }

              Column {
                id: emailColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.margins: Style.space(10)
                spacing: Style.space(4)

                Text {
                  width: parent.width
                  text: (emailRect.isUnread ? "● " : "") + modelData.from
                  color: emailRect.isUnread ? root.contentForeground : Qt.darker(root.contentForeground, 1.2)
                  font.family: root.contentFontFamily
                  font.pixelSize: Style.font.body
                  font.bold: emailRect.isUnread
                  elide: Text.ElideRight
                }

                Text {
                  width: parent.width
                  text: modelData.subject
                  color: emailRect.isUnread ? Qt.darker(root.contentForeground, 1.2) : Qt.darker(root.contentForeground, 1.5)
                  font.family: root.contentFontFamily
                  font.pixelSize: Style.font.bodySmall
                  font.bold: emailRect.isUnread
                  elide: Text.ElideRight
                }

                Text {
                  width: parent.width
                  text: {
                    var d = new Date(modelData.date);
                    if (isNaN(d.getTime())) return modelData.date;
                    var now = new Date();
                    var isToday = d.getDate() === now.getDate() && d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
                    if (isToday) {
                        var hrs = d.getHours();
                        var mins = d.getMinutes();
                        hrs = hrs < 10 ? '0' + hrs : hrs;
                        mins = mins < 10 ? '0' + mins : mins;
                        return hrs + ':' + mins;
                    } else {
                        var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                        return months[d.getMonth()] + " " + d.getDate();
                    }
                  }
                  color: Qt.darker(root.contentForeground, 1.8)
                  font.family: root.contentFontFamily
                  font.pixelSize: Style.font.caption
                  elide: Text.ElideRight
                }

                Rectangle {
                  visible: emailRect.isExpanded
                  width: parent.width
                  height: Style.spacing.hairline
                  color: root.contentForeground
                  opacity: 0.1
                  anchors.topMargin: Style.space(4)
                  anchors.bottomMargin: Style.space(4)
                }

                Text {
                  visible: emailRect.isExpanded
                  width: parent.width
                  textFormat: Text.MarkdownText
                  text: modelData.body ? modelData.body : "(No text content available)"
                  color: Qt.darker(root.contentForeground, 1.2)
                  font.family: root.contentFontFamily
                  font.pixelSize: Style.font.bodySmall
                  wrapMode: Text.Wrap
                  maximumLineCount: 15
                  elide: Text.ElideRight
                  onLinkActivated: function(link) { Qt.openUrlExternally(link); root.close() }
                }
              }
            }
          }

          Item {
            width: parent.width
            height: root.isLoadingMore ? Style.space(32) : 0
            visible: root.isLoadingMore
            
            Text {
              anchors.centerIn: parent
              text: "Loading more..."
              color: Qt.darker(root.contentForeground, 1.5)
              font.family: root.contentFontFamily
              font.pixelSize: Style.font.caption
            }
          }
        }
      }
    }
  }
}
