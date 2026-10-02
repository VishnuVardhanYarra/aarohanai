// Array of Aarohan-AI modules with respective high-quality mascots and their HTML links
const modules = [
    { title: "Aarohan Farmer", image: "assets/farmer_mascot_1772364655200.png", link: "../farmer_support/village.html" },
    { title: "Aarohan Market", image: "assets/market_mascot_1772364781308.png", link: "../marketing/index.html" },
    { title: "Aarohan Youth", image: "assets/youth_mascot_1772364809240.png", link: "../Youth/seventh.html" },
    { title: "Aarohan Transport", image: "assets/transport_mascot_1772364874722.png", link: "../transport/first.html" },
    { title: "Aarohan Governance", image: "assets/govt_mascot_1772364927678.png", link: "../government/smartvillage.html" },
    { title: "Aarohan Health", image: "assets/health_mascot_1772364984699.png", link: "../Heathcare/index.html" }
];

const carousel = document.getElementById('carousel');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');

let currentIndex = 0; // The active, centered card

// Generate Cards inside the Carousel
function generateCarousel() {
    carousel.innerHTML = '';
    modules.forEach((mod, index) => {
        const card = document.createElement('div');
        card.classList.add('card');

        // Structure for the linear cards
        card.innerHTML = `
            <img src="${mod.image}" alt="${mod.title}">
            <div class="info">
                <h2>${mod.title}</h2>
            </div>
        `;

        // Clicking a card brings it to the center or opens it if already center
        card.addEventListener('click', () => {
            if (index === currentIndex) {
                // Redirect exactly to the file we stated
                window.location.href = mod.link;
            } else {
                currentIndex = index;
                updateCarousel();
            }
        });

        carousel.appendChild(card);
    });

    // Position it initially
    updateCarousel();
}

function updateCarousel() {
    const cards = document.querySelectorAll('.card');

    // We want the active card to be physically centered on the screen.
    // In style.css: .card width = 260px, .carousel gap = 40px
    const cardWidth = 260;
    const gap = 40;
    const step = cardWidth + gap; // 300px

    // Calculate the center of the viewport
    const screenCenter = window.innerWidth / 2;

    // The offset to shift the carousel container so the currentIndex item hits the exact center
    const offset = screenCenter - (cardWidth / 2) - (currentIndex * step);

    // Apply transform to the container
    carousel.style.transform = `translateX(${offset}px)`;

    // Update active visual classes
    cards.forEach((card, index) => {
        if (index === currentIndex) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });

    // Update button states
    prevBtn.style.opacity = currentIndex === 0 ? '0.3' : '1';
    prevBtn.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';

    nextBtn.style.opacity = currentIndex === modules.length - 1 ? '0.3' : '1';
    nextBtn.style.pointerEvents = currentIndex === modules.length - 1 ? 'none' : 'auto';
}

// Function to trigger quick rotation animation on the AI Agent Logo
function triggerAILogoRotation(direction) {
    const aiImg = document.getElementById('ai-agent-img');
    if (!aiImg) return;

    // Clear previously applied animation classes and use reflow to force animation restart if clicked quickly
    aiImg.classList.remove('animate-rotate-left', 'animate-rotate-right');
    void aiImg.offsetWidth;

    if (direction === 'left') {
        aiImg.classList.add('animate-rotate-left');
    } else {
        aiImg.classList.add('animate-rotate-right');
    }
}

// Next/Prev Events
nextBtn.addEventListener('click', () => {
    if (currentIndex < modules.length - 1) {
        currentIndex++;
        triggerAILogoRotation('right');
        updateCarousel();
        resetAutoPlay();
    }
});

prevBtn.addEventListener('click', () => {
    if (currentIndex > 0) {
        currentIndex--;
        triggerAILogoRotation('left');
        updateCarousel();
        resetAutoPlay();
    }
});

// Auto-play feature
let autoPlayTimer;

function startAutoPlay() {
    autoPlayTimer = setInterval(() => {
        if (currentIndex < modules.length - 1) {
            currentIndex++;
            triggerAILogoRotation('right');
        } else {
            // Loop back to the first module automatically
            currentIndex = 0;
            triggerAILogoRotation('right');
        }
        updateCarousel();
    }, 4500); // Wait 4.5 seconds on each module
}

function resetAutoPlay() {
    clearInterval(autoPlayTimer);
    startAutoPlay();
}

// Pause automatic switching when user interacts or hovers over carousel
const carouselContainerEl = document.querySelector('.carousel-container');
const aiContainerEl = document.querySelector('.bottom-ai-container');

if (carouselContainerEl) {
    carouselContainerEl.addEventListener('mouseenter', () => clearInterval(autoPlayTimer));
    carouselContainerEl.addEventListener('mouseleave', () => startAutoPlay());
}
if (aiContainerEl) {
    aiContainerEl.addEventListener('mouseenter', () => clearInterval(autoPlayTimer));
    aiContainerEl.addEventListener('mouseleave', () => startAutoPlay());
}

startAutoPlay();

// Update centering automatically on window resize
window.addEventListener('resize', updateCarousel);

// ====== SIDEBAR TOGGLE ======
const sidebarToggle = document.getElementById('sidebar-toggle');
const closeSidebar = document.getElementById('close-sidebar');
const sidebar = document.getElementById('ai-sidebar');

sidebarToggle.addEventListener('click', () => {
    sidebar.classList.remove('hidden');
});

closeSidebar.addEventListener('click', () => {
    sidebar.classList.add('hidden');
});

// Bottom AI Logo click opens sidebar too
const aiLogo = document.getElementById('ai-logo');
aiLogo.addEventListener('click', () => {
    sidebar.classList.remove('hidden');
    // Change pulsing textual state to indicate it's listening intently
    document.querySelector('.ai-status').innerText = "Vocalizing...";
    setTimeout(() => {
        document.querySelector('.ai-status').innerText = "Listening...";
    }, 3000);
});

// Initialize
generateCarousel();

// Authentication Handling: Check query params for logged-in user
const urlParams = new URLSearchParams(window.location.search);
const authName = urlParams.get('name');
if (authName) {
    const authUserSpan = document.getElementById('authUserName');
    if (authUserSpan) {
        // Truncate name if it's too long
        authUserSpan.innerText = authName.length > 15 ? authName.substring(0, 15) + '...' : authName;
    }
}

// ====== CENTRAL AI AGENT LOGIC ======
const chatInput = document.querySelector('.sidebar-input input');
const chatBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const chatContent = document.querySelector('.sidebar-content');
let chatHistory = [];
let isContinuousListening = false;
let isSpeaking = false;

// Initialize Speech Recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false; // We manage continuity manually to allow AI to speak
    recognition.lang = 'te-IN';
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript;
        chatInput.value = transcript;

        const lowerTrans = transcript.toLowerCase();
        if (lowerTrans.includes('quit') || lowerTrans.includes('stop') || lowerTrans.includes('ఆపు') || lowerTrans.includes('విడువు') || lowerTrans.includes('ముగించు')) {
            isContinuousListening = false;
            updateMicIcon(false);
            addMessage("Listening stopped. Goodbye!", 'bot');
            speakText("Listening stopped. Goodbye!", 'en-US');
            return;
        }

        // Auto-send on voice command completion
        handleChat();
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        if (event.error !== 'no-speech') {
            isContinuousListening = false;
            updateMicIcon(false);
        }
    };

    recognition.onend = () => {
        // Automatically restart if continuous loop is active and bot is not talking
        if (isContinuousListening && !isSpeaking) {
            try { recognition.start(); } catch (e) { }
        } else if (!isContinuousListening) {
            updateMicIcon(false);
        }
    };
}

function updateMicIcon(active) {
    if (active) {
        micBtn.innerHTML = '<ion-icon name="mic-circle" style="font-size: 1.5rem;"></ion-icon>';
        micBtn.style.color = "#ff4757"; // Red when recording
    } else {
        micBtn.innerHTML = '<ion-icon name="mic-outline" style="font-size: 1.5rem;"></ion-icon>';
        micBtn.style.color = "white";
    }
}

// Speak the response aloud using the SpeechSynthesis API
function speakText(text, language = 'te-IN', onEndCallback = null) {
    if ('speechSynthesis' in window) {
        // Explicitly stop the recognition so it doesn't accidentally pick up the computer's voice
        if (recognition && isContinuousListening) {
            try { recognition.stop(); } catch (e) { }
        }

        window.speechSynthesis.cancel(); // cancel any ongoing speech

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language;
        utterance.rate = 1.0;

        // Critical fix for Chrome: attach the utterance to the window object to prevent Garbage Collection 
        // from destroying the utterance mid-sentence which causes it to stop after 1-2 seconds.
        window.speechUtterance = utterance;

        isSpeaking = true;
        utterance.onend = () => {
            isSpeaking = false;
            // Clear the reference
            window.speechUtterance = null;
            if (onEndCallback) onEndCallback();
        };
        utterance.onerror = () => {
            isSpeaking = false;
            window.speechUtterance = null;
            if (onEndCallback) onEndCallback();
        };

        window.speechSynthesis.speak(utterance);
    } else {
        if (onEndCallback) onEndCallback();
    }
}

micBtn.addEventListener('click', () => {
    if (recognition) {
        if (isContinuousListening) {
            isContinuousListening = false;
            recognition.stop();
            updateMicIcon(false);
        } else {
            isContinuousListening = true;
            updateMicIcon(true);
            try { recognition.start(); } catch (e) { }
        }
    } else {
        alert("Voice recognition not supported in this browser.");
    }
});

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;
    msgDiv.innerHTML = `<p>${text}</p>`;
    chatContent.appendChild(msgDiv);
    chatContent.scrollTop = chatContent.scrollHeight;
}

async function handleChat() {
    const text = chatInput.value.trim();
    if (!text) return;

    // 1. Show user message
    addMessage(text, 'user');
    chatInput.value = '';

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot typing';
    typingDiv.innerHTML = '<p>...</p>';
    chatContent.appendChild(typingDiv);
    chatContent.scrollTop = chatContent.scrollHeight;

    // 2. Prepare payload
    const currentUserInfo = window.currentUser || JSON.parse(localStorage.getItem('currentUser') || '{}');
    const payload = {
        message: text,
        history: chatHistory,
        user: currentUserInfo
    };

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        // Remove typing indicator
        typingDiv.remove();

        if (data.success) {
            addMessage(data.reply, 'bot');

            // 3. SPEAK OUT LOUD THE REPLY
            // Use Romanized text provided by the backend to bypass TTS not having Telugu fonts!
            const spokenText = data.reply_spoken || data.reply;

            // By using 'en-IN' (Indian English), the browser will confidently read Romanized Telugu
            // perfectly, ignoring whether the user actually has the Telugu pack installed.
            speakText(spokenText, 'en-IN', () => {
                if (isContinuousListening) {
                    try { recognition.start(); } catch (e) { }
                }
            });

            // update local history
            chatHistory.push({ user: text });
            chatHistory.push({ bot: data.reply });
            if (chatHistory.length > 6) chatHistory = chatHistory.slice(-6);
        } else {
            const errReply = "I am sorry, my systems are currently unreachable.";
            addMessage(errReply + " " + (data.error || ''), 'bot');
            speakText(errReply, 'en-US', () => {
                if (isContinuousListening) {
                    try { recognition.start(); } catch (e) { }
                }
            });
        }
    } catch (err) {
        typingDiv.remove();
        addMessage("Connection error while talking to center agent.", 'bot');
        speakText("Connection error while talking to center agent.", 'en-US', () => {
            if (isContinuousListening) {
                try { recognition.start(); } catch (e) { }
            }
        });
    }
}

chatBtn.addEventListener('click', handleChat);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleChat();
});

// ====== POINT 3: WAKE WORD LISTENER ======
let wakeWordRecognition = null;
let wakeWordStarted = false;

function initWakeWordListener() {
    if (wakeWordStarted || !SpeechRecognition) return;
    wakeWordStarted = true;

    wakeWordRecognition = new SpeechRecognition();
    wakeWordRecognition.continuous = true;
    wakeWordRecognition.interimResults = true;
    wakeWordRecognition.lang = 'en-IN'; // Mix of EN and TE

    wakeWordRecognition.onresult = (event) => {
        // If the main agent is already listening actively, ignore wake word
        if (isContinuousListening) return;

        const latestResult = event.results[event.results.length - 1];
        const transcript = latestResult[0].transcript.toLowerCase();

        if (transcript.includes('hey kittu') || transcript.includes('hello kittu') || transcript.includes('namaste kittu')) {
            console.log("Wake word detected!");

            // Open sidebar if closed
            const sidebar = document.getElementById('ai-sidebar');
            if (sidebar && sidebar.classList.contains('hidden')) {
                sidebar.classList.remove('hidden');
                document.querySelector('.ai-status').innerText = "Wake word detected...";
            }

            // Play a small beep (optional) or just start main listening
            speakText("Namaste! I am Agentic-AI Kittu, your smart assistant. I am here.", 'en-IN', () => {
                // Stop wake word temporarily to prevent overlap
                wakeWordRecognition.stop();

                // Trigger main AI mic
                micBtn.click();
            });
        }
    };

    wakeWordRecognition.onerror = (e) => {
        // silently ignore error and restart
    };

    wakeWordRecognition.onend = () => {
        // Auto-restart wake word listener if main agent is not actively listening
        if (!isContinuousListening) {
            try { wakeWordRecognition.start(); } catch (e) { }
        }
    };

    try { wakeWordRecognition.start(); } catch (e) { }
}

// Start wake word listener on first user interaction to bypass browser mic autoplay politics
window.addEventListener('click', initWakeWordListener, { once: true });


// ====== HOMEPAGE EXCLUSIVE CINEMATIC BACKGROUND ======
function initHomeBgAnimation() {
    const playIntro = sessionStorage.getItem('playIntro') === 'true';
    if (playIntro) {
        sessionStorage.removeItem('playIntro');
    }

    const bgContainer = document.createElement('div');
    Object.assign(bgContainer.style, {
        position: 'fixed',
        top: '0',
        left: '0',
        width: '100vw',
        height: '100vh',
        zIndex: '-999',
        pointerEvents: 'none',
        overflow: 'hidden',
        backgroundColor: '#050B14'
    });

    const canvas = document.createElement('canvas');
    Object.assign(canvas.style, {
        width: '100%',
        height: '100%',
        objectFit: 'cover', // This CSS property perfectly mimics background-size: cover
        opacity: '0.9',
        filter: 'brightness(0.6)' // Zero blur for crystal clear clarity
    });

    bgContainer.appendChild(canvas);
    document.body.prepend(bgContainer);

    document.body.style.backgroundColor = 'transparent';
    document.body.style.backgroundImage = 'none';

    // UI Fade Logic Integration
    let uiElements = [];
    if (playIntro) {
        // Find elements to fade in (excluding our background and scripts)
        uiElements = Array.from(document.body.children).filter(el =>
            el !== bgContainer && el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE' && el.id !== 'ai-sidebar'
        );

        uiElements.forEach(el => {
            el.style.opacity = '0';
            el.style.pointerEvents = 'none'; // prevent interacting while invisible
        });

        // The sequence: 8 seconds of slow-motion intro. 
        // Cards should slowly appear to get fully visible after 5 seconds.
        // So we delay 3000ms, then run a 5000ms fade transition.
        setTimeout(() => {
            uiElements.forEach(el => {
                el.style.transition = 'opacity 5s ease-out';
                el.style.opacity = '1';
                el.style.pointerEvents = 'auto'; // Re-enable interaction smoothly
            });
        }, 3000);
    }

    const ctx = canvas.getContext('2d', { alpha: false });

    const totalFrames = 240;
    const frames = new Array(totalFrames);
    for (let i = 1; i <= totalFrames; i++) {
        const img = new Image();
        img.src = `/back/ezgif-frame-${i.toString().padStart(3, '0')}.jpg`;
        frames[i - 1] = img;
    }

    let currentFrame = playIntro ? 0 : totalFrames - 1;
    let startTime = null;
    const animationDuration = 8000; // Force exactly 8.0 seconds in slow motion

    // Neural Mesh State
    const nodes = [];
    const numNodes = 120;
    const maxConnectionDist = 180;

    // Load the final destination hub background
    const hubBg = new Image();
    hubBg.src = 'aarohan_ai_hub_bg_1772775264547.png';

    function initNodes() {
        if (nodes.length > 0) return;
        for (let i = 0; i < numNodes; i++) {
            nodes.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                radius: Math.random() * 2 + 1
            });
        }
    }

    function updateNodes() {
        nodes.forEach(node => {
            node.x += node.vx;
            node.y += node.vy;

            if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
            if (node.y < 0 || node.y > canvas.height) node.vy *= -1;
        });
    }

    function drawNodes() {
        // Subtle brightness boost on top of Hub BG
        ctx.fillStyle = 'rgba(0, 240, 255, 0.4)';
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.1)';
        ctx.lineWidth = 0.5;

        for (let i = 0; i < nodes.length; i++) {
            const p1 = nodes[i];
            ctx.beginPath();
            ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
            ctx.fill();

            for (let j = i + 1; j < nodes.length; j++) {
                const p2 = nodes[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < maxConnectionDist) {
                    const alpha = 1 - (dist / maxConnectionDist);
                    ctx.strokeStyle = `rgba(0, 240, 255, ${alpha * 0.2})`;
                    ctx.lineWidth = alpha * 0.8;
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }
    }

    function drawFrame(img, opacity = 1.0) {
        if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            initNodes();
        }
        ctx.globalAlpha = opacity;
        ctx.drawImage(img, 0, 0);
        ctx.globalAlpha = 1.0;
    }

    function animate(currentTime) {
        if (!startTime) startTime = currentTime;
        const elapsedTime = currentTime - startTime;

        if (!playIntro) {
            // Immediately show Hub and Neural Loop
            if (hubBg.complete) {
                drawFrame(hubBg);
                updateNodes();
                drawNodes();
            }
            requestAnimationFrame(animate);
            return;
        }

        const progress = Math.min(elapsedTime / animationDuration, 1.0);
        let frameIndex = Math.floor(progress * (totalFrames - 1));

        const img = frames[frameIndex];
        if (img && img.complete && img.naturalHeight !== 0 && img.naturalWidth !== 0) {
            drawFrame(img);
        }

        if (progress < 1.0) {
            requestAnimationFrame(animate);
        } else {
            // Intro sequence finished. Seamlessly transition to the "AI Hub" loop.
            if (hubBg.complete) {
                drawFrame(hubBg);
                updateNodes();
                drawNodes();
            }
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
}

document.addEventListener('DOMContentLoaded', initHomeBgAnimation);


