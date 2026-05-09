// Tone Player plugin

// ── Init ────────────────────────────────────────────────────────────────

(function() {
    // Idempotency: if screen.js is re-evaluated (loader cache miss, hot reload,
    // older core builds without the load-side guard), don't re-wrap showScreen —
    // each re-wrap captures the previous wrapper, growing the chain and
    // leaking closures.
    const HOOK_KEY = '__slopsmithTonesShowScreenInstalled';
    if (window[HOOK_KEY]) return;
    window[HOOK_KEY] = true;

    const origShowScreen = window.showScreen;
    window.showScreen = function(id) {
        origShowScreen(id);
        if (id === 'plugin-tones') tpInit();
    };
})();

async function tpInit() {
    const resp = await fetch('/api/plugins/tones/assets-status');
    const data = await resp.json();
    const status = document.getElementById('tp-status');
    if (!data.ready) {
        status.innerHTML = `
            <div class="bg-yellow-900/20 border border-yellow-800/30 rounded-xl p-4 text-sm">
                <p class="text-yellow-400 font-semibold mb-1">Gear assets not found</p>
                <p class="text-gray-400">Run <code class="bg-dark-800 px-1 rounded">python extract_assets.py</code> to extract gear images from your Rocksmith installation. See the plugin README for details.</p>
            </div>`;
    } else {
        status.innerHTML = `
            <div class="bg-dark-700/50 border border-gray-800/50 rounded-xl p-3 text-xs text-gray-500">
                ${data.amps} amps · ${data.pedals} pedals · ${data.cabs} cabinets loaded
            </div>`;
    }
}

// ── Search ──────────────────────────────────────────────────────────────

async function tpSearch() {
    const q = document.getElementById('tp-search').value.trim();
    if (!q) return;
    const resp = await fetch(`/api/plugins/tones/search?q=${encodeURIComponent(q)}`);
    const data = await resp.json();
    const container = document.getElementById('tp-search-results');

    if (!data.songs || data.songs.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-xs py-2">No results</p>';
        return;
    }

    container.innerHTML = data.songs.map(s => `
        <div class="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-dark-700/50 transition cursor-pointer"
             onclick="tpLoadSong('${encodeURIComponent(s.filename)}', '${esc(s.title).replace(/'/g,"\\'")} - ${esc(s.artist).replace(/'/g,"\\'")}')">
            <div class="flex-1 min-w-0">
                <span class="text-sm text-white">${esc(s.title)}</span>
                <span class="text-xs text-gray-500 ml-2">${esc(s.artist)}</span>
            </div>
            <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </div>
    `).join('');
}

// ── Load tones for a song ───────────────────────────────────────────────

async function tpLoadSong(encodedFilename, displayName) {
    const container = document.getElementById('tp-tones');
    container.innerHTML = `<p class="text-gray-400 text-sm">Loading tones for ${displayName}...</p>`;
    document.getElementById('tp-search-results').innerHTML = '';

    const resp = await fetch(`/api/plugins/tones/song/${encodeURIComponent(decodeURIComponent(encodedFilename))}`);
    const data = await resp.json();

    if (data.error) {
        container.innerHTML = `<p class="text-red-400 text-sm">${data.error}</p>`;
        return;
    }

    if (!data.arrangements || data.arrangements.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-sm">No tone data found in this song.</p>';
        return;
    }

    let html = `<h3 class="text-lg font-bold text-white mb-4">${displayName}</h3>`;

    for (const arr of data.arrangements) {
        html += `<div class="mb-8">`;
        html += `<h4 class="text-sm font-semibold text-accent-light mb-4">${esc(arr.name)}</h4>`;

        for (const tone of arr.tones) {
            html += `<div class="mb-6">`;
            html += `<p class="text-xs text-gray-400 mb-3 uppercase tracking-wider">${esc(tone.name)}</p>`;

            // Signal chain
            html += `<div class="flex items-start gap-3 overflow-x-auto pb-3">`;

            for (let i = 0; i < tone.chain.length; i++) {
                const gear = tone.chain[i];
                html += tpRenderGear(gear);

                // Arrow between gear pieces
                if (i < tone.chain.length - 1) {
                    html += `<div class="flex items-center self-center text-gray-700 flex-shrink-0">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                        </svg>
                    </div>`;
                }
            }

            html += `</div>`; // chain
            html += `</div>`; // tone
        }
        html += `</div>`; // arrangement
    }

    container.innerHTML = html;
}

function tpRenderGear(gear) {
    const imgUrl = `/api/plugins/tones/gear-image/${encodeURIComponent(gear.type)}`;
    const knobs = gear.knobs || {};
    const knobEntries = Object.entries(knobs);

    // Slot type colors
    const slotColors = {
        pre_pedal: 'border-orange-800/40',
        amp: 'border-red-800/40',
        post_pedal: 'border-blue-800/40',
        rack: 'border-purple-800/40',
        cabinet: 'border-green-800/40',
    };
    const slotLabels = {
        pre_pedal: 'Pre',
        amp: 'Amp',
        post_pedal: 'Post',
        rack: 'Rack',
        cabinet: 'Cab',
    };
    const borderColor = slotColors[gear.slot] || 'border-gray-800';
    const slotLabel = slotLabels[gear.slot] || '';

    let html = `<div class="flex-shrink-0 w-40 bg-dark-700 border ${borderColor} rounded-xl overflow-hidden">`;

    // Slot label
    html += `<div class="px-3 py-1 text-[10px] uppercase tracking-wider text-gray-600 bg-dark-800/50">${slotLabel}</div>`;

    // Image
    html += `<div class="p-2 flex justify-center bg-dark-800/30">
        <img src="${imgUrl}" alt="${esc(gear.name)}" class="h-24 object-contain"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
        <div class="h-24 w-full items-center justify-center text-gray-600 text-xs" style="display:none">${esc(gear.name)}</div>
    </div>`;

    // Name
    html += `<div class="px-3 py-2 text-center">
        <p class="text-xs font-semibold text-gray-200 truncate">${esc(gear.name)}</p>
    </div>`;

    // Knobs
    if (knobEntries.length > 0) {
        html += `<div class="px-3 pb-3 space-y-1">`;
        for (const [name, value] of knobEntries) {
            // Determine bar width (assume 0-100 range for most, clamp)
            const numVal = typeof value === 'number' ? value : 0;
            const pct = Math.min(100, Math.max(0, Math.abs(numVal)));
            html += `<div class="flex items-center gap-2">
                <span class="text-[10px] text-gray-500 w-14 truncate" title="${esc(name)}">${esc(name)}</span>
                <div class="flex-1 h-1.5 bg-dark-600 rounded-full">
                    <div class="h-1.5 bg-accent/60 rounded-full" style="width:${pct}%"></div>
                </div>
                <span class="text-[10px] text-gray-500 w-8 text-right">${numVal}</span>
            </div>`;
        }
        html += `</div>`;
    }

    html += `</div>`;
    return html;
}

// ── Player integration: show tone button ────────────────────────────────

(function() {
    // Idempotency: see __slopsmithTonesShowScreenInstalled comment above. Same
    // reasoning for the playSong wrapper.
    const HOOK_KEY = '__slopsmithTonesPlaySongInstalled';
    if (window[HOOK_KEY]) return;
    window[HOOK_KEY] = true;

    const origPlaySong = window.playSong;
    window.playSong = async function(filename, arrangement) {
        await origPlaySong(filename, arrangement);
        _tpInjectPlayerButton(filename);
    };
})();

function _tpInjectPlayerButton(filename) {
    const controls = document.getElementById('player-controls');
    if (!controls || document.getElementById('btn-tones')) return;

    const closeBtn = controls.querySelector('button:last-child');
    const btn = document.createElement('button');
    btn.id = 'btn-tones';
    btn.className = 'px-3 py-1.5 bg-dark-600 hover:bg-dark-500 rounded-lg text-xs text-gray-400 transition';
    btn.textContent = 'Tones';
    btn.title = 'View signal chain';
    btn.onclick = () => {
        showScreen('plugin-tones');
        tpLoadSong(filename, document.getElementById('hud-title')?.textContent + ' - ' + document.getElementById('hud-artist')?.textContent);
    };
    if (closeBtn && closeBtn.parentNode === controls) {
        controls.insertBefore(btn, closeBtn);
    } else {
        controls.appendChild(btn);
    }
}
