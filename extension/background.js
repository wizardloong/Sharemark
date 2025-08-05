//const API_BASE = "http://localhost:8000/api";
//let socket = null;
//const sharedFolders = {};
//const pendingUpdates = {};
//
//function logError(action, error) {
//  console.error(`[ERROR] ${action}:`, error.message || error);
//}
//
//
//// Проверка доступных закладок
//chrome.bookmarks.getTree((tree) => {
//  console.log("[DEBUG] Bookmarks tree:", tree);
//});
//
//// WebSocket connection
//function connectWebSocket(token) {
//  if (socket) socket.close();
//
//  socket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
//
//  socket.onmessage = (event) => {
//    const message = JSON.parse(event.data);
//    if (message.type === "bookmark_update") {
//      applyRemoteUpdate(message.data);
//    }
//  };
//
//  socket.onclose = () => {
//    setTimeout(() => connectWebSocket(token), 5000);
//  };
//
//  socket.onerror = (error) => {
//    console.error('[ERROR] WebSocket error:', error);
//  };
//}
//
//function applyRemoteUpdate(data) {
//  const folderId = findLocalFolderId(data.folder_id);
//  if (!folderId) return;
//
//  chrome.bookmarks.getChildren(folderId, (children) => {
//    children.forEach(child => {
//      chrome.bookmarks.remove(child.id);
//    });
//
//    data.bookmarks.forEach(bookmark => {
//      chrome.bookmarks.create({
//        parentId: folderId,
//        title: bookmark.title,
//        url: bookmark.url
//      });
//    });
//  }, (error) => logError("getChildren", error));
//}
//
//function findLocalFolderId(remoteId) {
//  for (const [localId, folder] of Object.entries(sharedFolders)) {
//    if (folder.remoteId === remoteId) return localId;
//  }
//  return null;
//}
//
//// Context menu handler
//// Исправленный код создания контекстного меню
//chrome.runtime.onInstalled.addListener(() => {
//  console.log("[DEBUG] Extension installed");
//
//  // Единый пункт меню для всех контекстов закладок
//  chrome.contextMenus.create({
//    id: "share-folder",
//    title: "Поделиться папкой",
//    contexts: ["bookmark"],  // Правильный контекст для закладок
//    documentUrlPatterns: ["chrome://bookmarks/*"]  // Для менеджера закладок
//  });
//});
//
//
//chrome.contextMenus.onClicked.addListener((info, tab) => {
//  if (info.menuItemId === 'share-folder' && info.bookmarkId) {
//    // Проверяем, является ли элемент папкой
//    chrome.bookmarks.get(info.bookmarkId, (results) => {
//      if (results[0]?.url) {
//        console.log("Это не папка, а закладка");
//        return;
//      }
//
//      // Открываем модальное окно для папки
//      chrome.windows.create({
//        url: chrome.runtime.getURL(`share_modal.html?folderId=${info.bookmarkId}`),
//        type: 'popup',
//        width: 500,
//        height: 400,
//        focused: true
//      });
//    });
//  }
//});
//
//
//
//// Message handling
//chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
//  if (message.type === "join_shared_folder") {
//    joinSharedFolder(message.shareId);
//  } else if (message.type === "generate_share_link") {
//    generateShareLink(message.folderId, message.canWrite)
//      .then(sendResponse);
//    return true;
//  }
//});
//
//async function generateShareLink(folderId, canWrite) {
//  const folderTree = await new Promise(resolve => {
//    chrome.bookmarks.getSubTree(folderId, resolve);
//  });
//
//  const folder = folderTree[0];
//  const bookmarks = folder.children
//    .filter(child => child.url)
//    .map(child => ({
//      title: child.title,
//      url: child.url
//    }));
//
//  const response = await fetch(`${API_BASE}/share`, {
//    method: "POST",
//    headers: {"Content-Type": "application/json"},
//    body: JSON.stringify({
//      folder_id: folderId,
//      name: folder.title,
//      bookmarks: bookmarks,
//      can_write: canWrite
//    })
//  });
//
//  const data = await response.json();
//
//  sharedFolders[folderId] = {
//    token: data.token,
//    readOnly: false,
//    remoteId: folderId
//  };
//
//  connectWebSocket(data.token);
//  return `${API_BASE}/folder/${data.share_id}`;
//}
//
//async function joinSharedFolder(shareId) {
//  const response = await fetch(`${API_BASE}/folder/${shareId}`);
//  const data = await response.json();
//
//  chrome.bookmarks.create({
//    title: data.name
//  }, (folder) => {
//    sharedFolders[folder.id] = {
//      token: data.token,
//      readOnly: data.readOnly,
//      remoteId: data.folder_id
//    };
//
//    data.bookmarks.forEach(bookmark => {
//      chrome.bookmarks.create({
//        parentId: folder.id,
//        title: bookmark.title,
//        url: bookmark.url
//      });
//    });
//
//    connectWebSocket(data.token);
//  });
//}
//
//// Bookmark change listeners
//chrome.bookmarks.onChanged.addListener(handleBookmarkChange);
//chrome.bookmarks.onCreated.addListener(handleBookmarkChange);
//chrome.bookmarks.onRemoved.addListener(handleBookmarkChange);
//chrome.bookmarks.onMoved.addListener(handleBookmarkChange);
//
//function handleBookmarkChange(id, info) {
//  let parentId;
//
//  // Обработка разных типов событий
//  if (info.parentId) {
//    parentId = info.parentId; // Для onCreated, onMoved
//  } else if (info.node) {
//    parentId = info.node.parentId; // Для onChanged, onRemoved
//  }
//
//  if (parentId && sharedFolders[parentId] && !sharedFolders[parentId].readOnly) {
//    if (!pendingUpdates[parentId]) {
//      pendingUpdates[parentId] = setTimeout(() => {
//        sendFolderUpdate(parentId);
//        delete pendingUpdates[parentId];
//      }, 2000);
//    }
//  }
//}
//
//async function sendFolderUpdate(folderId) {
//  const folder = await new Promise(resolve => {
//    chrome.bookmarks.getSubTree(folderId, resolve);
//  });
//
//  const bookmarks = folder[0].children
//    .filter(child => child.url)
//    .map(child => ({
//      title: child.title,
//      url: child.url
//    }));
//
//  const token = sharedFolders[folderId].token;
//
//  fetch(`${API_BASE}/update/${token}`, {
//    method: "POST",
//    headers: {"Content-Type": "application/json"},
//    body: JSON.stringify({
//      name: folder[0].title,
//      bookmarks: bookmarks
//    })
//  });
//}
//
//chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
//  if (changeInfo.url && changeInfo.url.startsWith("http://localhost:8000/api/folder/")) {
//    const shareId = changeInfo.url.split("/").pop();
//    chrome.windows.create({
//      url: chrome.runtime.getURL(`share_modal.html?join=${shareId}`),
//      type: 'popup',
//      width: 400,
//      height: 300
//    });
//  }
//});
//
//
//chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
//  if (request.type === "SHOW_SHARE_MODAL") {
//    chrome.windows.create({
//      url: chrome.runtime.getURL(`share_modal.html?folderId=${request.folderId}`),
//      type: 'popup',
//      width: 400,
//      height: 300,
//      left: Math.round(screen.width/2 - 200),
//      top: Math.round(screen.height/2 - 150)
//    });
//  }
//});
