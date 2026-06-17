# -*- coding: utf-8 -*-
"""Проверка веб-интерфейса MICHI в headless-браузере (Chrome/Edge) через CDP.

Снимает ключевые экраны в shot_*.png (today, lessons, упражнение до/после
ответа, настройки) и печатает диагностику: JS-ошибки, горизонтальный overflow,
сдвиг макета при ответе (layout shift), декодирование звуков. Сам поднимает
сервер, если он ещё не запущен, и сам находит браузер.

Запуск:  .venv\\Scripts\\python scripts\\ui_check.py
Зависимости: websockets (есть в requirements-dev.txt).

Грабли (зашиты, чтобы не наступать снова):
  * скриншот через CDP Page.captureScreenshot (а не флаг --screenshot, который
    на Windows пишет в чужой каталог и из --headless=new выдаёт 0 байт);
  * функции-сессии (startReview/runChoice) возвращают вечно висящий Promise —
    в CDP их зовём fire-and-forget (`expr;0`, awaitPromise=false);
  * упражнение-выбор рендерим синтетически (runChoice без afterAnswer) —
    стабильно ловим .options и не пишем ответы в michi.db.
"""
import asyncio, json, base64, subprocess, time, urllib.request
import tempfile, shutil, os, glob, sys

try:                       # кириллица в выводе на Windows-консоли (cp1251)
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PORT = 9222          # порт CDP
SRV_PORT = 8000      # порт приложения
ORIGIN = f"http://127.0.0.1:{SRV_PORT}"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for p in BROWSERS:
        if os.path.isfile(p):
            return p
    return None


def server_up():
    try:
        with urllib.request.urlopen(ORIGIN + "/", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_server():
    """Возвращает Popen, если сервер пришлось поднять (его потом гасим), иначе None."""
    if server_up():
        return None
    py = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    proc = subprocess.Popen(
        [py, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(SRV_PORT), "--log-level", "warning"],
        cwd=ROOT)
    for _ in range(40):
        if server_up():
            return proc
        time.sleep(0.5)
    return proc  # не поднялся — вернём всё равно, чтобы погасить


def http_json(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}") as r:
        return json.loads(r.read())


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.id = 0

    async def send(self, method, **params):
        self.id += 1
        mid = self.id
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    async def js(self, expr):
        r = await self.send("Runtime.evaluate", expression=expr,
                            awaitPromise=True, returnByValue=True)
        return r.get("result", {}).get("value")

    async def fire(self, expr):
        # запуск без ожидания промиса (для функций-сессий, см. шапку модуля)
        await self.send("Runtime.evaluate", expression=f"{expr};0",
                        awaitPromise=False, returnByValue=True)

    async def shot(self, name):
        r = await self.send("Page.captureScreenshot", format="png")
        with open(os.path.join(ROOT, f"shot_{name}.png"), "wb") as f:
            f.write(base64.b64decode(r["data"]))
        print(f"  saved shot_{name}.png")

    async def metrics(self, w, h, dpr=2, mobile=True):
        await self.send("Emulation.setDeviceMetricsOverride",
                        width=w, height=h, deviceScaleFactor=dpr, mobile=mobile)


async def settle(ms=1400):
    await asyncio.sleep(ms / 1000)


OVERFLOW_JS = r"""
(() => {
  const vw = document.documentElement.clientWidth;
  const bad = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.right > vw + 0.5 || r.left < -0.5)
      bad.push({tag: el.tagName.toLowerCase(),
                cls: (el.className && el.className.toString().slice(0,40)) || '',
                left: Math.round(r.left), right: Math.round(r.right)});
  }
  return JSON.stringify({vw, scroll: document.documentElement.scrollWidth,
                         bad: bad.slice(0, 12)});
})()
"""


async def main():
    browser = find_browser()
    if not browser:
        print("Браузер не найден (Chrome/Edge). Пути — в BROWSERS.")
        sys.exit(1)
    srv = ensure_server()
    if not server_up():
        print(f"Сервер на {ORIGIN} не отвечает — запустите run.bat.")
        if srv:
            srv.terminate()
        sys.exit(1)

    for d in glob.glob(os.path.join(ROOT, ".chrome-tmp*")):
        shutil.rmtree(d, ignore_errors=True)
    prof = tempfile.mkdtemp(prefix=".chrome-tmp-", dir=ROOT)  # совпадает с .gitignore
    chrome = subprocess.Popen([
        browser, "--headless", "--disable-gpu", "--no-first-run", "--no-sandbox",
        f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}",
        "--hide-scrollbars", "--autoplay-policy=no-user-gesture-required",
        "about:blank",
    ])
    problems = []
    try:
        target = None
        for _ in range(40):
            try:
                pages = [t for t in http_json("/json") if t["type"] == "page"]
                if pages:
                    target = pages[0]; break
            except Exception:
                pass
            time.sleep(0.25)
        if not target:
            print("CDP endpoint не готов"); return

        import websockets
        async with websockets.connect(target["webSocketDebuggerUrl"],
                                      max_size=12_000_000) as ws:
            cdp = CDP(ws)
            await cdp.send("Page.enable")
            await cdp.send("Runtime.enable")
            await cdp.send("Page.addScriptToEvaluateOnNewDocument", source=(
                "window.__errs=[];"
                "addEventListener('error',e=>window.__errs.push(''+((e.error&&e.error.stack)||e.message)));"
                "addEventListener('unhandledrejection',e=>window.__errs.push('promise:'+e.reason));"
            ))

            # --- Мобильный: today + диагностика ---
            await cdp.metrics(390, 844, dpr=2, mobile=True)
            await cdp.send("Page.navigate", url=ORIGIN + "/")
            await settle(1800)
            await cdp.shot("m_today")
            diag = json.loads(await cdp.js(
                "JSON.stringify({haptics: typeof Haptics, hero: "
                "!!document.querySelector('.hero'), viewKids: "
                "document.querySelector('#view').children.length})"))
            errs = json.loads(await cdp.js("JSON.stringify(window.__errs||[])"))
            print(f"JS: Haptics={diag['haptics']} hero={diag['hero']} viewKids={diag['viewKids']}")
            if errs:
                problems.append(f"JS errors: {errs}")
            print(f"JS errors: {errs if errs else '(none)'}")
            snd = await cdp.js(
                "(async()=>{try{const b=await Haptics.buffer('drop_003');"
                "return b?('ok '+Math.round(b.duration*1000)+'ms'):'null';}"
                "catch(e){return 'err '+e}})()")
            print(f"sound decode drop_003: {snd}")

            info = json.loads(await cdp.js(OVERFLOW_JS))
            print(f"overflow (mobile today): vw={info['vw']} scrollWidth={info['scroll']}")
            for b in info["bad"]:
                msg = f"<{b['tag']}.{b['cls']}> left={b['left']} right={b['right']}"
                problems.append("overflow " + msg)
                print("  ! " + msg)
            if not info["bad"]:
                print("  (none)")

            # --- Путь ---
            await cdp.js("document.querySelector('nav.tabs button[data-view=lessons]').click()")
            await settle(1100)
            await cdp.shot("m_lessons")

            # --- Упражнение-выбор (синтетический рендер, без записи в БД) ---
            await cdp.js("document.querySelector('nav.tabs button[data-view=today]').click()")
            await settle(800)
            await cdp.fire(
                "document.querySelector('#player').classList.add('open');"
                "playerBody.classList.remove('center-step');setProgress(0.4);"
                "document.querySelector('#player-counter').textContent='3 · осталось ~7';"
                "runChoice({type:'kana_recognition',question:'Какой знак так читается?',"
                "prompt:{style:'jp',text:'あ',tts:'あ'},options:['か','さ','あ','な'],"
                "answer:2,options_are_kana:true})")
            await settle(1300)
            await cdp.shot("m_exercise")
            if await cdp.js("!!document.querySelector('#player-body .options button')"):
                topq = ("Math.round(document.querySelector("
                        "'#player-body .options button').getBoundingClientRect().top)")
                before = await cdp.js(topq)
                await cdp.js("document.querySelectorAll('#player-body .options button')[0].click()")
                await settle(1000)
                await cdp.shot("m_exercise_answered")
                after = await cdp.js(topq)
                shift = after - before
                if abs(shift) > 2:
                    problems.append(f"layout shift {shift}px при ответе")
                print(f"layout shift options.top: {before}->{after} = {shift}px (цель ~0)")
            else:
                problems.append("упражнение-выбор не отрендерилось")

            # --- Настройки (тумблер + селектор звука) ---
            await cdp.send("Page.navigate", url=ORIGIN + "/")
            await settle(1400)
            await cdp.js("openSettings()")
            await settle(700)
            opts = await cdp.js("Array.from(document.querySelectorAll("
                                "'#set-tap-sound option')).length")
            print(f"tap-sound options: {opts}")
            await cdp.shot("m_settings")

            # --- Статистика: лимиты SRS должны быть редактируемыми ---
            await cdp.send("Page.navigate", url=ORIGIN + "/")
            await settle(900)
            await cdp.js("document.querySelector('nav.tabs button[data-view=stats]').click()")
            await settle(1500)
            await cdp.js("const e=document.querySelector('#data-export'); "
                         "e&&e.scrollIntoView({block:'center'});")
            await settle(500)
            await cdp.shot("m_stats")
            srs_ok = await cdp.js(
                "!!(document.querySelector('#srs-new')&&document.querySelector('#srs-rev')"
                "&&document.querySelector('#srs-ret'))")
            print(f"stats SRS-limits selects: {'present' if srs_ok else 'MISSING'}")
            if not srs_ok:
                problems.append("на вкладке статистики нет селекторов лимитов SRS")
            backup_ok = await cdp.js(
                "!!(document.querySelector('#data-export')&&document.querySelector('#data-import'))")
            print(f"stats backup buttons: {'present' if backup_ok else 'MISSING'}")
            if not backup_ok:
                problems.append("на вкладке статистики нет кнопок резервной копии")
            errs_stats = json.loads(await cdp.js("JSON.stringify(window.__errs||[])"))
            if errs_stats:
                problems.append(f"JS errors (stats): {errs_stats}")
            print(f"JS errors (stats): {errs_stats if errs_stats else '(none)'}")

            # --- Словарь (справочник изученного) ---
            await cdp.js("document.querySelector('nav.tabs button[data-view=dict]').click()")
            await settle(1200)
            await cdp.shot("m_dict")
            dict_ok = await cdp.js(
                "!!(document.querySelector('.dict-grid')||document.querySelector('.dict-wrap .note'))")
            print(f"dict tab rendered: {'yes' if dict_ok else 'MISSING'}")
            if not dict_ok:
                problems.append("вкладка «Словарь» не отрисовалась")
            ow_dict = await cdp.js(
                "JSON.stringify([innerWidth, document.documentElement.scrollWidth])")
            vw_d, sw_d = json.loads(ow_dict)
            print(f"overflow (dict): vw={vw_d} scrollWidth={sw_d}")
            if sw_d > vw_d + 1:
                problems.append(f"горизонтальный overflow на «Словаре»: {sw_d}>{vw_d}")
            errs_dict = json.loads(await cdp.js("JSON.stringify(window.__errs||[])"))
            if errs_dict:
                problems.append(f"JS errors (dict): {errs_dict}")
            print(f"JS errors (dict): {errs_dict if errs_dict else '(none)'}")

            # --- Английский интерфейс (фаза 2: локализация контента) ---
            await cdp.js("localStorage.setItem('michi_lang','en')")
            await cdp.send("Page.navigate", url=ORIGIN + "/")
            await settle(1300)
            await cdp.js("document.querySelector('nav.tabs button[data-view=lessons]').click()")
            await settle(1000)
            await cdp.shot("m_lessons_en")
            # синтетическое vocab-упражнение: вопрос и варианты-переводы должны стать EN
            await cdp.fire(
                "document.querySelector('#player').classList.add('open');"
                "playerBody.classList.remove('center-step');setProgress(0.4);"
                "runChoice({type:'vocab_choice',question:'Что означает это слово?',"
                "prompt:{style:'jp',text:'みず',tts:'みず'},"
                "options:['чай (зелёный)','хлеб','вода','рыба'],answer:2})")
            await settle(1200)
            await cdp.shot("m_exercise_en")
            q_en = await cdp.js(
                "(document.querySelector('#player-body .question')||{}).textContent||''")
            print(f"EN exercise question: {q_en!r}")
            if "What does this word" not in q_en:
                problems.append(f"вопрос упражнения не переведён на EN: {q_en!r}")
            await cdp.js("document.querySelector('#player-close').click();"
                         "document.querySelector('#confirm-yes').click();")
            await settle(500)
            await cdp.js("document.querySelector('nav.tabs button[data-view=dict]').click()")
            await settle(1000)
            await cdp.shot("m_dict_en")
            # синтетическое интро кандзи в EN: значение переведено, мнемоника скрыта
            await cdp.fire(
                "document.querySelector('#player').classList.add('open');"
                "playerBody.classList.add('center-step');"
                "showIntroKanji({char:'水',meaning:'вода',on:['スイ'],kun:['みず'],"
                "examples:[{w:'水',r:'みず',ru:'вода'},{w:'水よう日',r:'すいようび',ru:'среда'}],"
                "mnemonic:'тест-мнемоника',components:[],tts:'みず'})")
            await settle(900)
            await cdp.shot("m_kanji_en")
            kmean = await cdp.js("(document.querySelector('.kanji-meaning')||{}).textContent||''")
            has_mnem = await cdp.js("!!document.querySelector('#player-body .mnemonic')")
            print(f"EN kanji intro: meaning={kmean!r} mnemonic_shown={has_mnem}")
            if kmean != "water":
                problems.append(f"значение кандзи в интро не переведено: {kmean!r}")
            if has_mnem:
                problems.append("мнемоника показана в EN (должна быть скрыта)")
            await cdp.js("document.querySelector('#player-close').click();"
                         "var c=document.querySelector('#confirm-yes');c&&c.click();")
            await settle(400)
            # overlay фаз 2+3 загрузился без синтаксических ошибок? (tr напрямую)
            checks = json.loads(await cdp.js(
                "JSON.stringify({"
                "w:tr('вода'),"                                        # фаза 2: слово
                "one:tr('один'),"                                      # фаза 3: значение кандзи
                "st:tr('Я студент.'),"                                 # фаза 3: пример грамматики
                "iv:tr('через {n} мин',{n:5}),"                        # клиентский интервал SRS
                "wk:tr('«{x}» — запишите кандзи',{x:tr('Япония')}),"   # составной вопрос word_kanji
                "vb:tr('«{v}» → {f}',{v:tr('идти, ехать'),f:tr('ます-форма')})})"))
            print(f"EN content overlay: {checks}")
            for key, want in (("w", "water"), ("one", "one"), ("st", "I'm a student."),
                              ("iv", "in 5 min"), ("wk", "«Japan» — write it in kanji"),
                              ("vb", "«to go» → ます form")):
                if checks.get(key) != want:
                    problems.append(
                        f"EN overlay: {key}={checks.get(key)!r}, ждали {want!r}")
            errs_en = json.loads(await cdp.js("JSON.stringify(window.__errs||[])"))
            if errs_en:
                problems.append(f"JS errors (en): {errs_en}")
            print(f"JS errors (en): {errs_en if errs_en else '(none)'}")
            await cdp.js("localStorage.setItem('michi_lang','ru')")   # вернуть язык

            # --- Десктоп today ---
            await cdp.metrics(1100, 860, dpr=1, mobile=False)
            await cdp.send("Page.navigate", url=ORIGIN + "/")
            await settle(1500)
            await cdp.shot("d_today")
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except Exception:
            chrome.kill()
        shutil.rmtree(prof, ignore_errors=True)
        if srv:
            srv.terminate()

    print("\n=== ИТОГ ===")
    if problems:
        print(f"ПРОБЛЕМЫ ({len(problems)}):")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("OK — проблем не найдено. Скриншоты: shot_*.png в корне проекта.")


if __name__ == "__main__":
    asyncio.run(main())
