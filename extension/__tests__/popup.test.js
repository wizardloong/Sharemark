/**
 * @jest-environment jsdom
 */
global.TextEncoder = require('util').TextEncoder;
global.TextDecoder = require('util').TextDecoder;

let getUuid,
  handleShare,
  updateToggleState,
  saveToggleState,
  getBookmarksRecursive,
  getBookmarkFolders,
  renderFolders;

describe('Sharemark Extension', () => {
  let store;

  beforeEach(() => {
    // Обнуляем мок-хранилище
    store = {};

    global.chrome = {
      storage: {
        local: {
          get: jest.fn(async (key) => {
            if (!key) return store;
            if (typeof key === 'string') {
              return { [key]: store[key] };
            }
            const result = {};
            key.forEach((k) => (result[k] = store[k]));
            return result;
          }),
          set: jest.fn(async (obj) => {
            store = { ...store, ...obj };
          }),
        },
      },
      bookmarks: {
        getTree: jest.fn(),
      },
      runtime: {
        sendMessage: jest.fn(),
        id: 'test-extension-id',
      },
    };

    // Удаляем глобальный crypto перед установкой мока
    delete global.crypto;
    global.crypto = { randomUUID: jest.fn(() => 'test-uuid') };

    Object.defineProperty(global.navigator, 'clipboard', {
      value: { writeText: jest.fn() },
      configurable: true,
    });

    global.fetch = jest.fn();

    window.close = jest.fn();
    window.alert = jest.fn();

    // Импорт после моков
    const popup = require('../popup.js');
    getUuid = popup.getUuid;
    handleShare = popup.handleShare;
    updateToggleState = popup.updateToggleState;
    saveToggleState = popup.saveToggleState;
    getBookmarksRecursive = popup.getBookmarksRecursive;
    getBookmarkFolders = popup.getBookmarkFolders;
    renderFolders = popup.renderFolders;
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.resetModules(); // сбросить кэш require
  });

  test('Генерация и сохранение UUID (персистентность)', async () => {
    // ничего не переопределяем — используем общий мок со store
    const uuid1 = await getUuid();
    expect(uuid1).toBe('test-uuid');
    expect(chrome.storage.local.set).toHaveBeenCalledTimes(1);
    expect(chrome.storage.local.set).toHaveBeenCalledWith({ sharemark_uuid: 'test-uuid' });

    const uuid2 = await getUuid();
    expect(uuid2).toBe(uuid1);
    // второй раз set вызываться не должен
    expect(chrome.storage.local.set).toHaveBeenCalledTimes(1);
  });

  test('Работа с chrome.storage.local', async () => {
    await chrome.storage.local.set({ sharemark_uuid: 'existing-uuid' });
    const uuid = await getUuid();
    expect(uuid).toBe('existing-uuid');
  });

  test('updateToggleState меняет иконку и состояние', () => {
    const el = document.createElement('span');
    updateToggleState(el, 2);
    expect(el.textContent).toBe('👑');
    expect(el.dataset.state).toBe('2');
  });

  test('saveToggleState сохраняет состояние', async () => {
    await saveToggleState('folder1', 1);
    const result = await chrome.storage.local.get('folderStates');
    expect(result.folderStates.folder1.state).toBe(1);
  });

  test('getBookmarksRecursive собирает закладки рекурсивно', async () => {
    const tree = {
      title: 'Root',
      children: [
        { title: 'Google', url: 'https://google.com' },
        { title: 'Folder', children: [{ title: 'GitHub', url: 'https://github.com' }] },
      ],
    };
    const bookmarks = await getBookmarksRecursive(tree);
    expect(bookmarks).toEqual([
      { title: 'Google', url: 'https://google.com' },
      { title: 'GitHub', url: 'https://github.com' },
    ]);
  });

  test('getBookmarkFolders исключает root', async () => {
    chrome.bookmarks.getTree.mockResolvedValue([
      {
        id: '0',
        title: 'root',
        children: [
          { id: '1', title: 'Folder1', children: [] },
          { id: '2', title: 'Folder2', children: [] },
        ],
      },
    ]);
    const folders = await getBookmarkFolders();
    expect(folders.map((f) => f.id)).toEqual(['1', '2']);
  });

  test('renderFolders отрисовывает список', async () => {
    document.body.innerHTML = '<div id="foldersList"></div>';
    const folders = [{ id: '1', title: 'Folder1' }];
    await renderFolders(folders);
    expect(document.getElementById('foldersList').textContent).toContain('Folder1');
  });

  test('handleShare отправляет запрос и вызывает window.close', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ share_url: 'https://test', share_id: 'id123' }),
    });
    const folder = { id: 'f1', title: 'Folder' };
    await handleShare(folder, true);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/share'),
      expect.objectContaining({ method: 'POST' })
    );
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://test');
    // expect(window.close).toHaveBeenCalled();
    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({ type: 'initWebSocket', shareId: 'id123' });
  });

  test('handleShare показывает ошибку при bad response', async () => {
    fetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: 'Ошибка' }),
    });
    const folder = { id: 'f1', title: 'Folder' };
    await handleShare(folder, true);
    expect(window.alert).toHaveBeenCalledWith(expect.stringContaining('Ошибка'));
  });
});
