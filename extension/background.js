let wsConnection = null;
let wsTimeout = null;
let wsConnectingPromise = null;
let sharemark_uuid = null;
let heartbeatInterval = null;
let lastPong = Date.now();
let reconnectDelay = 1000;

const RECONNECT_MAX_DELAY = 30000;
const HEARTBEAT_INTERVAL = 25000;  // 25 секунд
const WS_HEARTBEAT_TIMEOUT = 60000; // 60 секунд

// ------------------ События закладок ------------------
chrome.bookmarks.onCreated.addListener((id) => sendBookmarkUpdate(id, null, 'created'));
chrome.bookmarks.onRemoved.addListener((id, removeInfo) => sendBookmarkUpdate(id, removeInfo, 'removed'));
chrome.bookmarks.onChanged.addListener((id) => sendBookmarkUpdate(id, null, 'updated'));

// ------------------ Стартовая настройка ------------------
updateRedirectRule();

// Если UUID в хранилище меняется — обновляем правило
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.sharemark_uuid) updateRedirectRule();
});

// Перехват запроса к share API
chrome.webRequest.onBeforeRequest.addListener(
  async () => { await getWsConnection(); },
  { urls: ["https://getsharemark.com/get_sharemark_share*"] },
  []
);

// ------------------ WebSocket ------------------
async function getWsConnection() {
  return await initWebSocketConnection();
}

async function initWebSocketConnection() {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) return wsConnection;
  if (wsConnectingPromise) return wsConnectingPromise;

  wsConnectingPromise = new Promise(async (resolve) => {
    if (wsConnection && (wsConnection.readyState === WebSocket.OPEN || wsConnection.readyState === WebSocket.CONNECTING)) {
      wsConnection.close();
    }

    try {
      sharemark_uuid = await getUuid() || crypto.randomUUID();
      await chrome.storage.local.set({ sharemark_uuid });

      wsConnection = new WebSocket(`wss://getsharemark.com/ws/sync?sharemark_uuid=${sharemark_uuid}`);

      wsConnection.onopen = () => {
        console.log("WS открыт");
        reconnectDelay = 1000; // сброс экспоненциального backoff
        startHeartbeat();
        wsConnectingPromise = null;
        resolve(wsConnection);
      };

      wsConnection.onmessage = async (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "ping") {
          wsConnection.send(JSON.stringify({ type: "pong" }));
          return;
        }
        if (message.type === "pong") {
          lastPong = Date.now();
          return;
        }

        if (message.type === "initial_data") await processInitialData(message, message.folder_id);
        else if (message.type === "bookmark_update") await processBookmarkUpdate(message, message.folderId, message.isOwner);

        resetWsTimeout();
      };

      wsConnection.onerror = console.error;

      wsConnection.onclose = () => {
        console.log("WS закрыт, переподключаем...");
        wsConnectingPromise = null;
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
        wsConnection = null;
        setTimeout(() => { if (!wsConnectingPromise) initWebSocketConnection(); }, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, RECONNECT_MAX_DELAY);
      };
    } catch (e) {
      console.error("Ошибка WS:", e);
      wsConnectingPromise = null;
      setTimeout(() => { if (!wsConnectingPromise) initWebSocketConnection(); }, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, RECONNECT_MAX_DELAY);
    }
  });

  return wsConnectingPromise;
}

// ------------------ Heartbeat ------------------
function startHeartbeat() {
  if (heartbeatInterval) clearInterval(heartbeatInterval);
  lastPong = Date.now();
  heartbeatInterval = setInterval(() => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      wsConnection.send(JSON.stringify({ type: "ping" }));
      if (Date.now() - lastPong > WS_HEARTBEAT_TIMEOUT) {
        console.warn("Heartbeat timeout, закрываю WS");
        wsConnection.close();
        wsConnection = null;
      }
    }
  }, HEARTBEAT_INTERVAL);
}

// ------------------ Работа с UUID ------------------
async function getUuid() {
  return new Promise((resolve) => {
    chrome.storage.local.get("sharemark_uuid", (result) => {
      resolve(result.sharemark_uuid);
    });
  });
}

// ------------------ Управление редиректом ------------------
async function updateRedirectRule() {
  const uuid = await getUuid();
  if (!uuid) { console.warn("sharemark_uuid не найден — правило не будет добавлено"); return; }

  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: [1],
  });

  await chrome.declarativeNetRequest.updateDynamicRules({
    addRules: [{
      id: 1,
      priority: 1,
      action: {
        type: "redirect",
        redirect: {
          transform: {
            queryTransform: { addOrReplaceParams: [{ key: "sharemark_uuid", value: uuid }] },
            path: "/api/share"
          }
        }
      },
      condition: { urlFilter: "getsharemark.com/get_sharemark_share", resourceTypes: ["main_frame"] }
    }]
  });

  console.log("Правило редиректа обновлено:", uuid);
}

// ------------------ Закладки ------------------
async function sendBookmarkUpdate(id, removeInfo, eventType) {
  const folderStates = await chrome.storage.local.get('folderStates');
  const folderId = await findParentFolderId(id);
  if (!folderId || !folderStates[folderId] || !folderStates[folderId].canWrite) return;

  const changeData = await getBookmarkChangeData(id, removeInfo, eventType);
  if (changeData && wsConnection?.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({ type: 'bookmark_update', folderId, data: changeData }));
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
  if (removeInfo) return { action: 'removed', id, parentId: removeInfo.parentId, timestamp: Date.now() };
  const [bookmark] = await chrome.bookmarks.get(id);
  return { action: eventType, id: bookmark.id, title: bookmark.title, url: bookmark.url || '', parentId: bookmark.parentId, index: bookmark.index || 0, timestamp: Date.now() };
}

async function processInitialData(data, folderId) {
  let storedData = await chrome.storage.local.get('folderStates');
  const existingFolder = storedData.folderStates?.[folderId];
  if (!existingFolder) {
    const { id } = await chrome.bookmarks.create({ parentId: '1', title: data.name });
    for (const b of data.bookmarks) {
      await chrome.bookmarks.create({ parentId: id, title: b.title, url: b.url });
    }
    storedData.folderStates ||= {};
    storedData.folderStates[folderId] = { canWrite: false };
    await chrome.storage.local.set(storedData);
  }
}

async function processBookmarkUpdate(update, folderId, isOwner) {
  if (isOwner) return;
  switch (update.action) {
    case 'created': await chrome.bookmarks.create({ parentId: update.parentId, title: update.title, url: update.url, index: update.index }); break;
    case 'removed': await chrome.bookmarks.remove(update.id); break;
    case 'updated': await chrome.bookmarks.update(update.id, { title: update.title, url: update.url }); break;
  }
}

// ------------------ Idle timeout ------------------
function resetWsTimeout() {
  if (wsTimeout) clearTimeout(wsTimeout);
  wsTimeout = setTimeout(() => {
    if (wsConnection) {
      console.log("Закрываю WebSocket из-за бездействия");
      wsConnection.close();
      wsConnection = null;
    }
  }, 5 * 60 * 1000);
}
