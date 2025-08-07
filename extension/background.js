let wsConnection = null;

// Подключаемся при запуске браузера
chrome.runtime.onStartup.addListener(() => {
  getWsConnection();
});

// WebSocket: отправка обновлений по изменениям в мастер-папке
chrome.bookmarks.onCreated.addListener((id, bookmark) => sendBookmarkUpdate(id, null, 'created'));
chrome.bookmarks.onRemoved.addListener((id, removeInfo) => sendBookmarkUpdate(id, removeInfo, 'removed'));
chrome.bookmarks.onChanged.addListener((id, changeInfo) => sendBookmarkUpdate(id, null, 'updated'));

async function sendBookmarkUpdate(id, removeInfo, eventType) {
  const folderStates = await chrome.storage.local.get('folderStates');
  const folderId = await findParentFolderId(id);

  if (!folderId || !folderStates[folderId] || !folderStates[folderId].canWrite) return;

  const changeData = await getBookmarkChangeData(id, removeInfo, eventType);

  if (changeData && wsConnection?.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'bookmark_update',
      folderId: folderId,
      data: changeData
    }));
  }
}

async function findParentFolderId(bookmarkId) {
  const [bookmark] = await chrome.bookmarks.get(bookmarkId);
  if (!bookmark) return null;

  let parent = bookmark;
  while (parent.parentId && parent.parentId !== '0') {
    parent = (await chrome.bookmarks.get(parent.parentId))[0];
  }
  return parent.id;
}

async function getBookmarkChangeData(id, removeInfo, eventType) {
  if (removeInfo) {
    return {
      action: 'removed',
      id: id,
      parentId: removeInfo.parentId,
      timestamp: Date.now()
    };
  }

  const [bookmark] = await chrome.bookmarks.get(id);

  return {
    action: eventType,
    id: bookmark.id,
    title: bookmark.title,
    url: bookmark.url || '',
    parentId: bookmark.parentId,
    index: bookmark.index || 0,
    timestamp: Date.now()
  };
}

async function processInitialData(data, folderId) {
  let storedData = await chrome.storage.local.get('folderStates');
  const existingFolder = storedData.folderStates?.[folderId];

  if (!existingFolder) {
    const { id } = await chrome.bookmarks.create({
      parentId: '1',
      title: data.folder_name
    });

    data.bookmarks.forEach(async b => {
      await chrome.bookmarks.create({
        parentId: id,
        title: b.title,
        url: b.url
      });
    });

    storedData.folderStates[folderId] = { canWrite: false };
    await chrome.storage.local.set(storedData);
  }
}

async function processBookmarkUpdate(update, folderId, isOwner) {
  if (isOwner) return;

  switch (update.action) {
    case 'created':
      await chrome.bookmarks.create({
        parentId: update.parentId,
        title: update.title,
        url: update.url,
        index: update.index
      });
      break;

    case 'removed':
      await chrome.bookmarks.remove(update.id);
      break;

    case 'updated':
      await chrome.bookmarks.update(update.id, {
        title: update.title,
        url: update.url
      });
      break;
  }
}

// WebSocket. Приём обновлений
function initWebSocketConnection(shareId) {
  if (wsConnection) {
    wsConnection.close();
  }

  wsConnection = new WebSocket(`wss://localhost:8000/ws/sync?share_id=${shareId}`);

  wsConnection.onmessage = async (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'initial_data') {
      await processInitialData(message.data, message.folderId);
    } else if (message.type === 'bookmark_update') {
      await processBookmarkUpdate(message.data, message.folderId, message.isOwner);
    }
  };

  wsConnection.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
}

function getWsConnection() {
  const shareId = localStorage.getItem('shareId') || uuidv4();
  localStorage.setItem('shareId', shareId);
  initWebSocketConnection(shareId);
}
