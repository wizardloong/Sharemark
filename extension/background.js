let wsConnection = null;
let wsTimeout = null;
const WS_IDLE_TIMEOUT = 5 * 60 * 1000; // 5 минут

// Подключаемся при запуске браузера
// chrome.runtime.onStartup.addListener(async () => {
//   await getWsConnection();
// });

// WebSocket: отправка обновлений по изменениям в мастер-папке
chrome.bookmarks.onCreated.addListener((id, bookmark) => sendBookmarkUpdate(id, null, 'created'));
chrome.bookmarks.onRemoved.addListener((id, removeInfo) => sendBookmarkUpdate(id, removeInfo, 'removed'));
chrome.bookmarks.onChanged.addListener((id, changeInfo) => sendBookmarkUpdate(id, null, 'updated'));

// // Запускаем при старте
updateRedirectRule();

// Если UUID в хранилище меняется — обновляем правило
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.sharemark_uuid) {
    updateRedirectRule();
  }
});

// Перехватываем запросы к /get_sharemark_share
chrome.webRequest.onBeforeRequest.addListener(
  async (details) => {
    console.log("Запрос на get_sharemark_share:", details.url);
    await getWsConnection(); // Откроем WS при первом запросе
  },
  { urls: ["http://localhost:8000/get_sharemark_share*"] },
  []
);

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
      title: data.name
    });

    data.bookmarks.forEach(async b => {
      await chrome.bookmarks.create({
        parentId: id,
        title: b.title,
        url: b.url
      });
    });

    storedData.folderStates ||= {};
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
let wsConnectingPromise = null;
let sharemark_uuid = null;

async function initWebSocketConnection() {
  // Если уже есть соединение — возвращаем его
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    console.log("WS уже открыт");
    return wsConnection;
  }

  // Если соединение в процессе установки — ждём его
  if (wsConnectingPromise) {
    console.log("Ждём существующее подключение WS...");
    return wsConnectingPromise;
  }

  // Создаём промис подключения
  wsConnectingPromise = new Promise(async (resolve, reject) => {
    // Закрываем старое соединение, если оно не закрыто
    if (wsConnection && (wsConnection.readyState === WebSocket.OPEN || wsConnection.readyState === WebSocket.CONNECTING)) {
      try {
        wsConnection.close();
      } catch (e) {
        console.warn("Ошибка при закрытии старого WS:", e);
      }
    }

    // Получаем или создаём sharemark_uuid
    sharemark_uuid = await getUuid();
    if (!sharemark_uuid) {
      sharemark_uuid = crypto.randomUUID();
      await chrome.storage.local.set({ sharemark_uuid });
    }

    console.log("Подключаем WS с UUID:", sharemark_uuid);

    wsConnection = new WebSocket(`ws://localhost:8000/ws/sync?sharemark_uuid=${sharemark_uuid}`);

    wsConnection.onopen = () => {
      console.log("WS соединение установлено");
      resetWsTimeout();
      wsConnectingPromise = null;
      resolve(wsConnection);
    };

    wsConnection.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "initial_data") {
        await processInitialData(message, message.folder_id);
      } else if (message.type === "bookmark_update") {
        await processBookmarkUpdate(message, message.folderId, message.isOwner);
      }

      resetWsTimeout();
    };

    wsConnection.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    wsConnection.onclose = async () => {
      console.log("WS соединение закрыто. Переподключаем...");
      wsConnectingPromise = null;
      setTimeout(() => initWebSocketConnection(), 2000); // авто-реконнект через 2 сек
    };
  });

  return wsConnectingPromise;
}


async function getWsConnection() {
  initWebSocketConnection();
}

async function getUuid() {
  return new Promise((resolve) => {
    chrome.storage.local.get("sharemark_uuid", (result) => {
      resolve(result.sharemark_uuid);
    });
  });
}

async function updateRedirectRule() {
  const uuid = await getUuid();
  if (!uuid) {
    console.warn("sharemark_uuid не найден — правило не будет добавлено");
    return;
  }

  // Удаляем старое правило, если оно есть
  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: [1], // ID нашего правила
  });

  // Добавляем новое правило
  await chrome.declarativeNetRequest.updateDynamicRules({
    addRules: [
      {
        id: 1,
        priority: 1,
        action: {
          type: "redirect",
          redirect: {
            transform: {
              queryTransform: {
                addOrReplaceParams: [
                  { key: "sharemark_uuid", value: uuid }
                ]
              },
              path: "/api/share"
            }
          }
        },
        condition: {
          urlFilter: "localhost:8000/get_sharemark_share",
          resourceTypes: ["main_frame"]
        }
      }
    ]
  });

  console.log("Правило редиректа обновлено:", uuid);
}

// async function tryShareRequest(url, uuid, maxAttempts = 3) {
//   let attempt = 0;
//   let finalUrl;

//   // Преобразуем URL, подставляем sharemark_uuid
//   const urlObj = new URL(url);
//   urlObj.pathname = "/api/share";
//   urlObj.searchParams.set("sharemark_uuid", uuid);
//   finalUrl = urlObj.toString();

//   while (attempt < maxAttempts) {
//     attempt++;
//     console.log(`Попытка #${attempt}: ${finalUrl}`);

//     try {
//       const res = await fetch(finalUrl);
//       const data = await res.json();

//       if (res.ok && data.status === "ok") {
//         console.log("✅ Успешно получили OK-ответ");
//         return finalUrl; // возвращаем URL для редиректа
//       }

//       console.warn("Ответ сервера:", data);
//     } catch (err) {
//       console.error("Ошибка запроса:", err);
//     }

//     // Подождём перед следующей попыткой
//     await new Promise(resolve => setTimeout(resolve, 1000));
//   }

//   console.error("❌ Не удалось получить успешный ответ за 3 попытки");
//   return null;
// }

// // Ловим запросы на /get_sharemark_share
// chrome.webRequest.onBeforeRequest.addListener(
//   async (details) => {
//     console.log("Перехвачен запрос:", details.url);

//     const uuid = await getUuid();
//     if (!uuid) {
//       console.warn("Нет sharemark_uuid — редирект отменён");
//       return;
//     }

//     const redirectUrl = await tryShareRequest(details.url, uuid);
//     if (redirectUrl) {
//       return { redirectUrl }; // редиректим, если успешный ответ
//     } else {
//       console.warn("Редирект отменён из-за неудачных попыток");
//     }
//   },
//   { urls: ["http://localhost:8000/get_sharemark_share*"], types: ["main_frame"] },
//   ["blocking"]
// );


function resetWsTimeout() {
  if (wsTimeout) {
    clearTimeout(wsTimeout);
  }
  wsTimeout = setTimeout(() => {
    if (wsConnection) {
      console.log("Закрываю WebSocket из-за бездействия");
      wsConnection.close();
      wsConnection = null;
    }
  }, WS_IDLE_TIMEOUT);
}

