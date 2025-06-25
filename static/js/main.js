document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const converterForm = document.getElementById('converter-form');
    const urlInput = document.getElementById('youtube-url');
    const convertBtn = document.getElementById('convert-btn');
    const loader = document.getElementById('loader');
    const resultDiv = document.getElementById('result');
    const thumbnailImg = document.getElementById('thumbnail');
    const videoTitle = document.getElementById('video-title');
    const downloadBtn = document.getElementById('download-btn');
    const successSound = document.getElementById('success-sound');
    const themeToggle = document.getElementById('theme-toggle');
    const errorMessageDiv = document.getElementById('error-message');

    // --- Theme Switcher ---
    const applyTheme = (theme) => {
        document.body.classList.toggle('dark-mode', theme === 'dark');
        localStorage.setItem('theme', theme);
    };

    themeToggle.addEventListener('click', () => {
        const newTheme = document.body.classList.contains('dark-mode') ? 'light' : 'dark';
        applyTheme(newTheme);
    });

    // Apply saved theme or system preference on load
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(savedTheme || (prefersDark ? 'dark' : 'light'));

    // --- UI Update Functions ---
    const showLoader = () => {
        loader.classList.remove('hidden');
        convertBtn.disabled = true;
        convertBtn.textContent = 'Converting...';
        resultDiv.classList.add('hidden');
        errorMessageDiv.classList.add('hidden');
    };

    const hideLoader = () => {
        loader.classList.add('hidden');
        convertBtn.disabled = false;
        convertBtn.textContent = 'Convert to MP3';
    };

    const showResult = (data) => {
        thumbnailImg.src = data.thumbnail;
        videoTitle.textContent = data.title;
        downloadBtn.href = data.file;
        resultDiv.classList.remove('hidden');
        // Play a small success sound
        if (successSound) {
            successSound.currentTime = 0; // Rewind to start
            successSound.play().catch(e => console.error("Audio play failed:", e));
        }
    };
    
    const showError = (message) => {
        errorMessageDiv.textContent = `Error: ${message}`;
        errorMessageDiv.classList.remove('hidden');
    }

    // --- Form Submission Handler ---
    converterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const youtubeURL = urlInput.value.trim();

const youtubePattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/i;
if (!youtubeURL || !youtubePattern.test(youtubeURL)) {
    showError('Please paste a valid YouTube URL.');
    return;
}

        showLoader();

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: youtubeURL }),
            });
            
            const data = await response.json();

            if (!response.ok) {
                // Throws an error to be caught by the catch block
                throw new Error(data.error || 'Something went wrong.');
            }
            
            showResult(data);

        } catch (error) {
            console.error('Conversion Error:', error);
            showError(error.message);
            resultDiv.classList.add('hidden'); // Ensure result is hidden on error
        } finally {
            hideLoader();
        }
    });
});
