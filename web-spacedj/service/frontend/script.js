function ge(elementId){
    return document.getElementById(elementId);
}

Object.defineProperty(window, 'vmax', {
    get: () => {
        return Math.max(document.body.clientWidth, document.body.clientHeight);
    }
});

Object.defineProperty(window, 'aspectRatio', {
    get: () => {
        return window.innerWidth / window.innerHeight;
    }
});

Node.prototype.css = function(css) {
    for (let style in css) this.style[style] = css[style];
}

Node.prototype.hide = function() {
    this.style.display = 'none';
}

Node.prototype.show = function(display = 'block') {
    this.style.display = display;
}

Node.prototype.fadeIn = function() {
    this.style.animation = `fade-in-animation 0.5s ease`;
}


function scaleUI(){
    if (!window.ui.clientWidth) return

    let scale = (0.043 * window.vmax) / window.ui.clientWidth;
    window.ui.css({transform: `scale(${scale})`});
}


function block_actions() {
    window.make_remix_btn.disabled = true;
    ge('preset-selector').disabled = true;
    for (e of document.querySelectorAll('input')) {
        e.disabled = true;
    }
    document.body.style.cursor='wait';
}


function unblock_actions() {
    window.make_remix_btn.disabled = false;
    ge('preset-selector').disabled = false;
    for (e of document.querySelectorAll('input')) {
        e.disabled = false;
    }
    document.body.style.cursor='default';
}


async function do_remix() {
    block_actions();

    if (!window.author.value) {
        alert('Fill the author field!')
        return unblock_actions();
    }

    if (!window.file.value) {
        alert('Select a file!')
        return unblock_actions();
    }

    if (window.file.value.split('.').pop() !== 'mp3') {
        alert('File type should be mp3!')
        return unblock_actions();
    }

    const preset = ge('preset-selector').value;
    const formData = new FormData();
    formData.append("author", window.author.value);
    formData.append("preset", preset);
    formData.append("file", window.file.files[0]);
    if (preset === "CUSTOM") {
        formData.append("process_cf", JSON.stringify(
            [
                window.bass.value, window.volume.value, window.reverb.value,
                window.tempo.value, window.treble.value, window.normalize.checked ? "1" : "0"
            ]
        ));
    }

    try {
        let response = await fetch("/api/remix/create", {
            method: "POST",
            body: formData,
            signal: AbortSignal.timeout(17000)
        });

        if (response.status === 200) {
            let uuid = await response.text();
            window.location.assign('/remix/' + uuid);
        } else {
            let err = await response.text();
            alert(err)
        }
    } catch (err) {
        if (err.name === "TimeoutError") {
            alert('Timed out. Processing took more than 17 seconds.');
        } else {
            alert('Unknown error');
            console.error(err);
        }
    } finally {
        unblock_actions();
    }
}

let preset_keys = {
    "BASSBOOST_TAZ": "Bassboost Taz",
    "BASSBOOST_PACAN": "Bassboost Pacan",
    "NIGHTCORE": "Nightcore",
    "DAYCORE": "Daycore",
    "REVERB": "Reverb",
    "EARRAPE": "Earrape",
    "CUSTOM": "Custom"
}


document.addEventListener('DOMContentLoaded', async () => {
    window.addEventListener('resize', scaleUI);

    let route_check = window.location.pathname.match('^/remix/([a-f0-9\-]+)$');

    if (route_check) {
        document.querySelector('.ui-bg').css({
            background: 'url(/img/bg_main_collapsed.png)',
            backgroundSize: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'center center'
        });

        let audio = new Audio();
        audio.onerror = function() {
            window.location.assign('/');
        };
        audio.onended = function() {
            window.btn_pause.hide();
        };

        audio.src = `/api/file?name=${route_check[1]}.mp3`;

        window.btn_play.addEventListener('click', () => {
            audio.play();
            window.btn_pause.show();
        });
        window.btn_pause.addEventListener('click', () => {
            audio.pause();
            window.btn_pause.hide();
        });
        window.btn_stop.addEventListener('click', () => {
            audio.pause();
            audio.currentTime = 0;
            window.btn_pause.hide();
        });

        window.btn_pause.hide();
        
        try {
            let data = await (await fetch(`/api/remix/metadata?name=${route_check[1]}`)).json();
            window.meta_author.innerText = data['author'].substr(0, 10) + (data['author'].length > 10 ? '...' : '');
            window.meta_preset.innerText = preset_keys[data['preset']];
        } catch(e) {
            window.location.assign('/');
        }
    } else {
        const sliders = document.querySelectorAll('.slider');
        const inputs = document.querySelectorAll('.number-input');

        sliders.forEach((slider, index) => {
            const input = inputs[index];

            input.value = slider.value;

            input.disabled = true;
            slider.disabled = true;

            slider.addEventListener('input', () => {
                input.value = slider.value;
            });

            input.addEventListener('input', () => {
                let value = input.value;
                if (value === '') return;
                value = Math.min(Math.max(value, slider.min), slider.max);
                slider.value = value;
            });
        });

        window.normalize.disabled = true;

        window.make_remix_btn.addEventListener('click', do_remix);
        ge('preset-selector').addEventListener('change', (e) => {
            if (e.target.value === 'CUSTOM') {
                sliders.forEach((slider, index) => {
                    const input = inputs[index];
                    input.disabled = false;
                    slider.disabled = false;
                });
                window.normalize.disabled = false;
            } else {
                sliders.forEach((slider, index) => {
                    const input = inputs[index];
                    input.disabled = true;
                    slider.disabled = true;
                });
                window.normalize.disabled = true;
            }
        });
    }

    let gw = ge('global-wrapper');
    gw.show();
    scaleUI();
});