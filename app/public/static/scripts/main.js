// Theme toggle functionality
const toggle = document.getElementById('toggle');
const html = document.documentElement;

// Check for saved user preference, if any, on load of the website
if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    html.classList.add('dark');
    toggle.checked = true;
} else {
    html.classList.remove('dark');
    toggle.checked = false;
}

// Listen for toggle changes
toggle.addEventListener('change', function() {
    if (this.checked) {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    } else {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    }
});

// Общий ползунок цены
const commonPriceSlider = document.getElementById('common-price-slider');
const commonPriceValue = document.getElementById('common-price-value');
const commonPriceContainer = document.getElementById('common-price-slider-container');

// Отслеживаем изменения общего ползунка
commonPriceSlider.addEventListener('input', function() {
    commonPriceValue.textContent = this.value;
});

commonPriceSlider.addEventListener('change', async function() {
    const price = this.value;
    
    // Prepare AJAX request for price selection
    const priceData = {
        price: price,
    };
    console.log('Prepared price AJAX:', priceData);
    // Here you would normally do: fetch('/api/feature-price', { method: 'POST', body: JSON.stringify(priceData) })

    try {
        const response = await fetch('/set_price', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(priceData)
        });

        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            alert("Что-то пошло не так. Попробуйте ещё раз.");
        }
    } catch (error) {
        console.error("Ошибка отправки:", error);
        alert("Не удалось отправить форму. Попробуйте позже.");
    }
});

// Like button functionality
document.querySelectorAll('.like-btn').forEach(button => {
    button.addEventListener('click', async function() {
        const icon = this.querySelector('i');
        const countSpan = this.querySelector('span');
        const futureId = this.dataset.feature;
        let currentCount = parseInt(countSpan.textContent);
        
        if (currentCount < 3) {
            currentCount++;
            countSpan.textContent = currentCount;
            this.classList.add('liked');
            icon.classList.remove('far');
            icon.classList.add('fas');
            
            // Показываем общий ползунок цены
            commonPriceContainer.classList.remove('hidden');         
        } else {
            currentCount = 0;
            countSpan.textContent = currentCount;
            this.classList.remove('liked');
            icon.classList.remove('fas');
            icon.classList.add('far');
        }

        // Prepare AJAX request for like
        const likeData = {
            feature_id: futureId,
            vote_count: currentCount
        };
        console.log('Prepared like AJAX:', likeData);

        try {
            const response = await fetch('/set_vote', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(likeData)
            });

            if (!response.ok) {
                throw new Error(`Ошибка: ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                alert("Что-то пошло не так. Попробуйте ещё раз.");
            }
        } catch (error) {
            console.error("Ошибка отправки:", error);
            alert("Не удалось отправить форму. Попробуйте позже.");
        }
    });
});

// Feedback form submission
document.getElementById('feedbackForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // Собираем данные из формы
    const formData = new FormData(this);

    try {
        const response = await fetch('/feedback', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }

        const data = await response.json();

        // Обработка ответа от сервера
        if (data.success === true) {
            alert(data.message);
            this.reset();
        } else {
            alert("Что-то пошло не так. Попробуйте ещё раз.");
        }
    } catch (error) {
        console.error("Ошибка отправки:", error);
        alert("Не удалось отправить форму. Попробуйте позже.");
    }
});


// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Map для хранения времени начала просмотра секции
const sectionViewStartTimes = new Map();

// Функция для проверки, виден ли элемент
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Функция для обработки видимости секций
function trackSectionView() {
    document.querySelectorAll('section[id]').forEach(section => {
        const sectionId = section.id;
        const isInViewport = isElementInViewport(section);

        if (isInViewport && !sectionViewStartTimes.has(sectionId)) {
            // Секция стала видимой -> записываем время начала
            sectionViewStartTimes.set(sectionId, Date.now());
            
            // Отправляем событие "section_view_start"
            umami.track('section_view_start', { 
                section_name: sectionId 
            });

        } else if (!isInViewport && sectionViewStartTimes.has(sectionId)) {
            // Секция перестала быть видимой -> вычисляем длительность и отправляем
            const startTime = sectionViewStartTimes.get(sectionId);
            const duration = Date.now() - startTime;
            sectionViewStartTimes.delete(sectionId);

            // Отправляем событие "section_view_end" с длительностью
            umami.track('section_view_end', { 
                section_name: sectionId,
                duration_ms: duration 
            });
        }
    });
}

// Запускаем проверку при скролле и загрузке страницы
let scrollCheckTimer;
window.addEventListener('scroll', () => {
    clearTimeout(scrollCheckTimer);
    scrollCheckTimer = setTimeout(trackSectionView, 100); // Дебаунсинг
});
window.addEventListener('load', trackSectionView);
// Также можно использовать Intersection Observer для большей эффективности

// Отслеживание кликов по кнопкам
document.body.addEventListener('click', function(event) {
    // Находим ближайший элемент с data-track атрибутом
    const trackedElement = event.target.closest('[data-track]');
    
    if (trackedElement) {
        const eventName = trackedElement.getAttribute('data-track');
        let eventData = {};

        // Собираем все data-атрибуты элемента в объект eventData
        for (let attr of trackedElement.attributes) {
            if (attr.name.startsWith('data-') && attr.name !== 'data-track') {
                const key = attr.name.replace('data-', '');
                eventData[key] = attr.value;
            }
        }

        // Отправляем событие в Umami
        umami.track(eventName, eventData);
        console.log('Tracked event:', eventName, eventData); // Для отладки
    }
});

// Отслеживание JavaScript ошибок
window.addEventListener('error', function(e) {
    umami.track('js_error', {
        error_message: e.error?.message || e.message,
        error_file: e.filename,
        error_line: e.lineno,
        error_col: e.colno
    });
});