"""Optional preload prompt. Failure/absence always offers normal play."""
import json
from pathlib import Path
import queue
import threading
import urllib.parse
import urllib.request
from dh_preload import (Cancelled, apply_selection, atomic_json, identity,
                        last_center, max_radius, select_tiles, validate_catalog)


def offer(app_dir, state):
    url = state.get('server',{}).get('dhPreloadUrl')
    if not url:
        return
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname != 'github.com' or not parsed.path.startswith('/DrewPhi/DrewCraft/releases/download/'):
            raise ValueError('Unsupported preload catalog origin')
        with urllib.request.urlopen(url,timeout=10) as response:
            body = response.read(8*1024*1024+1)
        if len(body)>8*1024*1024:
            raise ValueError('LOD catalog too large')
        catalog = validate_catalog(json.loads(body),state)
        import tkinter as tk
        from tkinter import ttk
        root = tk.Tk()
    except Exception as error:
        print('Optional distant-terrain preload unavailable:',error,flush=True)
        return
    minecraft = Path(state['prismRoot']) / 'instances' / state['instanceId'] / 'minecraft'
    atomic_json(minecraft / 'drewcraft-preload-world.json',catalog['identity'])
    center, label = last_center(minecraft,catalog)
    maximum = max_radius(catalog,center)
    preferences = app_dir / 'user-data/dh-preload.json'
    try:
        saved = json.loads(preferences.read_text())
        if saved.get('identity') != identity(state):
            saved = {}
    except (OSError,ValueError):
        saved = {}
    root.title('DrewCraft — distant terrain')
    root.geometry('600x340')
    frame = ttk.Frame(root,padding=18)
    frame.pack(fill='both',expand=True)
    enabled = tk.BooleanVar(value=bool(saved.get('enabled',False)))
    value = saved.get('radiusBlocks',0)
    radius = tk.IntVar(value=min(maximum,max(0,value if type(value) is int else 0)))
    ttk.Checkbutton(frame,text='Preload distant terrain before playing',variable=enabled).pack(anchor='w')
    ttk.Label(frame,text=f'Center: {label} · X {center[0]}, Z {center[1]}',wraplength=550).pack(anchor='w',pady=8)
    detail = ttk.Label(frame,wraplength=550)
    detail.pack(anchor='w')
    def estimate(*args):
        value = radius.get()
        size = sum(tile['size'] for tile in select_tiles(catalog,center,value))
        detail.configure(text=f'{value:,} blocks ({value/16:,.0f} chunks) radius · up to {size/1024**2:,.1f} MiB\n0 = skip; maximum includes all available sections. Cached tiles may need no download.')
    slider = tk.Scale(frame,from_=0,to=maximum,orient='horizontal',variable=radius,command=estimate,showvalue=False)
    slider.pack(fill='x')
    estimate()
    ttk.Label(frame,text='Visuals only; stored coverage may have gaps. Preloading uses a stable IP-based DH cache in this instance. Old cache folders are retained.',wraplength=550).pack(anchor='w',pady=8)
    status = ttk.Label(frame,wraplength=550)
    status.pack(anchor='w')
    bar = ttk.Progressbar(frame,maximum=100)
    bar.pack(fill='x',pady=8)
    buttons = ttk.Frame(frame)
    buttons.pack(fill='x')
    cancelled = threading.Event()
    events = queue.Queue()
    running = False
    def remember():
        try:
            atomic_json(preferences,{'identity':identity(state),'enabled':enabled.get(),'radiusBlocks':radius.get()})
        except OSError as error:
            print('Could not save optional terrain preferences:',error,flush=True)
    def skip():
        if running:
            cancelled.set()
            status.configure(text='Stopping safely, then launching…')
        else:
            remember()
            root.destroy()
    def start():
        nonlocal running
        remember()
        if not enabled.get() or radius.get()==0:
            root.destroy()
            return
        running = True
        cancelled.clear()
        download_button.configure(state='disabled')
        slider.configure(state='disabled')
        selected_radius = radius.get()
        def worker():
            try:
                apply_selection(app_dir,state,catalog,center,selected_radius,
                                progress=events.put,cancelled=cancelled.is_set)
                events.put({'phase':'done'})
            except Cancelled:
                events.put({'phase':'done'})
            except Exception as error:
                events.put({'phase':'error','label':str(error)})
        threading.Thread(target=worker,daemon=True).start()
    download_button = ttk.Button(buttons,text='Download and play',command=start)
    download_button.pack(side='right')
    ttk.Button(buttons,text='Skip and play',command=skip).pack(side='right',padx=8)
    root.protocol('WM_DELETE_WINDOW',skip)
    def update():
        nonlocal running
        while not events.empty():
            event = events.get_nowait()
            if event['phase']=='done':
                root.destroy()
                return
            if event['phase']=='error':
                running = False
                status.configure(text='Preload stopped: '+event['label']+' — you can still skip and play.')
                download_button.configure(state='normal')
                slider.configure(state='normal')
            elif event['phase']=='download':
                bar.configure(value=100*event['downloaded']/max(1,event['total']))
                status.configure(text=f"Downloading tile: {event['downloaded']/1024**2:.1f}/{event['total']/1024**2:.1f} MiB · ETA {event['etaSeconds']:.0f}s")
            else:
                status.configure(text=event.get('label',''))
        root.after(100,update)
    root.after(100,update)
    root.mainloop()
