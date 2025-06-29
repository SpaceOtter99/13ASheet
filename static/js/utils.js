function generateUUID() {
  // 16 bytes = 128 bits
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);

  // Per RFC4122 4.4, set version to 4 (xxxx10xx) in byte 6
  bytes[6] = (bytes[6] & 0x0f) | 0x40;

  // Per RFC4122 4.4, set variant to RFC 4122 (10xxxxxx) in byte 8
  bytes[8] = (bytes[8] & 0x3f) | 0x80;

  // Convert to hex & insert hyphens
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  return (
    hex.substring(0, 8) + '-' +
    hex.substring(8, 12) + '-' +
    hex.substring(12, 16) + '-' +
    hex.substring(16, 20) + '-' +
    hex.substring(20)
  );
}

let textareas;

function autoResize() {
  this.rows = 1;
  this.style.height = 'auto';
  this.style.height = this.scrollHeight + 'px';
}

function autoResizeAll() {
    console.log("Resizing");
    textareas.forEach(textarea => autoResize.call(textarea));
}


document.addEventListener('DOMContentLoaded', () => {
  textareas = document.querySelectorAll(".autoresizing");

  textareas.forEach(textarea => {
    textarea.addEventListener('input', autoResize, false);
    autoResize.call(textarea);
  });

  window.addEventListener('resize', autoResizeAll);
});

function addNotification(text) {
  const container = document.getElementById('notification-container');
  if (!container) return;

  const note = document.createElement('div');
  note.className = 'notification';
  note.textContent = text;

  container.appendChild(note);

  setTimeout(() => {
    note.classList.add('fading');
  }, 2500);

  setTimeout(() => {
    if (note.parentNode === container) {
      container.removeChild(note);
    }
  }, 3000);
}