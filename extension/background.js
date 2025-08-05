require('dotenv').config();

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "sharemark-folder",
    title: "Поделиться папкой",
    contexts: ["bookmark"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "sharemark-folder") {
    chrome.storage.local.set({ folderIdToShare: info.bookmarkId }, () => {
      chrome.action.openPopup(); // откроем popup, где будет форма
    });
  }
});

function connectWebSocket(folderId) {
    ws = new WebSocket(`wss://${process.env.DOMAIN_NAME}/ws/${folderId}`);
    ws.onopen = () => {
        console.log("WebSocket connected");
    };
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "update") {
            // обновляем папку
            chrome.bookmarks.getTree((tree) => {
                // найти нужную папку, сравнить и обновить
                // можно перезаписать содержимое
            });
        }
    };
    ws.onclose = () => {
        console.log("WebSocket closed, reconnecting...");
        setTimeout(() => connectWebSocket(folderId), 2000);
    };
}

function createSharedFolder(data) {
    chrome.bookmarks.create({
        parentId: "1", // или конкретный id
        title: `📁 [Shared] ${data.title}`
    }, (folder) => {
        // сохранить folderId ↔ sharedId
        chrome.storage.local.set({ [`shared-${data.id}`]: folder.id });
    });
}
