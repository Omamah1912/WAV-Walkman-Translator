(() => {
  const BACKEND_URL = 'http://127.0.0.1:5000';

  const form = document.getElementById('request-form');
  const input = document.getElementById('melody-request');
  const generateBtn = document.getElementById('generate-btn');
  const statusEl = document.getElementById('status');

  const audio = document.getElementById('audio-player');
  const playBtn = document.getElementById('play-btn');
  const pauseBtn = document.getElementById('pause-btn');
  const stopBtn = document.getElementById('stop-btn');

  const reelLeft = document.getElementById('reel-left');
  const reelRight = document.getElementById('reel-right');
  const tapeLabel = document.getElementById('tape-label');

  function setStatus(message, isError) {
    statusEl.textContent = message || '';
    statusEl.classList.toggle('error', Boolean(isError));
  }

  function setReelsSpinning(spinning) {
    reelLeft.classList.toggle('spinning', spinning);
    reelRight.classList.toggle('spinning', spinning);
  }

  function setControlsEnabled(enabled) {
    playBtn.disabled = !enabled;
    pauseBtn.disabled = !enabled;
    stopBtn.disabled = !enabled;
  }

  function setTapeLabel(text) {
    tapeLabel.textContent = text;
    tapeLabel.style.fontSize = '';
    const minFontSizePx = 9;
    let fontSizePx = parseFloat(getComputedStyle(tapeLabel).fontSize);
    while (tapeLabel.scrollWidth > tapeLabel.clientWidth && fontSizePx > minFontSizePx) {
      fontSizePx -= 1;
      tapeLabel.style.fontSize = `${fontSizePx}px`;
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const requestText = input.value.trim();
    if (!requestText) {
      return;
    }

    generateBtn.disabled = true;
    setControlsEnabled(false);
    setReelsSpinning(false);
    setStatus('composing...', false);

    try {
      const response = await fetch(`${BACKEND_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: requestText }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Request failed (${response.status})`);
      }

      audio.src = `data:audio/wav;base64,${data.audio_base64}`;
      audio.load();
      setTapeLabel(data.title || 'untitled tape');

      setControlsEnabled(true);
      setStatus(`ready — "${data.title || 'untitled'}"`, false);
    } catch (err) {
      setStatus(err.message || 'something went wrong', true);
    } finally {
      generateBtn.disabled = false;
    }
  }

  form.addEventListener('submit', handleSubmit);

  playBtn.addEventListener('click', () => {
    audio.play();
  });

  pauseBtn.addEventListener('click', () => {
    audio.pause();
  });

  stopBtn.addEventListener('click', () => {
    audio.pause();
    audio.currentTime = 0;
  });

  // Reels spin only while audio is actually playing — driven by the
  // audio element's real state, not by button clicks.
  audio.addEventListener('play', () => setReelsSpinning(true));
  audio.addEventListener('pause', () => setReelsSpinning(false));
  audio.addEventListener('ended', () => setReelsSpinning(false));
})();
