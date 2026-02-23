(function(){
  if(window.zkDeviceDiscovery) return;

  const CSS = `
  /* Dark/compact chrome to match the device config modal */
  .zkdd-overlay{position:fixed;inset:0;display:none;align-items:center;justify-content:center;z-index:4000;padding:8px;background:rgba(0,0,0,0.62);}
  .zkdd-overlay.is-open{display:flex;}
  .zkdd-modal{width:min(480px, calc(100vw - 16px));max-height:92vh;display:flex;flex-direction:column;overflow:hidden;background:#1e4a6b;border:2px solid #3da5d9;border-radius:6px;box-shadow:0 22px 50px rgba(0,0,0,0.55);}

  .zkdd-header{padding:6px 8px;display:flex;align-items:flex-start;justify-content:space-between;gap:8px;
    background: linear-gradient(90deg, rgba(15,42,71,0.92) 0%, rgba(61,165,217,0.92) 100%);
    border-bottom:1px solid #3d6a8b;
  }
  .zkdd-title{flex:1;text-align:left;}
  .zkdd-title .t1{font-size:11px;font-weight:900;letter-spacing:0.2px;color:#ffffff;}
  .zkdd-title .t2{margin-top:1px;font-size:8px;font-weight:800;color:#9fd2f1;opacity:0.9;}

  .zkdd-close{width:18px;height:18px;border-radius:2px;background:#163247;border:1px solid #3d6a8b;color:#9fd2f1;font-size:12px;font-weight:900;cursor:pointer;display:flex;align-items:center;justify-content:center;line-height:1;padding:0;}
  .zkdd-close:hover{background:#3da5d9;border-color:#3da5d9;color:#fff;}

  .zkdd-body{padding:6px 8px;overflow:auto;color:#e8f0f8;background:#163247;}
  .zkdd-section{border:1px solid #3d6a8b;border-radius:2px;padding:6px;background:#0f2433;margin-bottom:6px;}
  .zkdd-section h4{margin:0 0 4px 0;color:#7db3d9;font-weight:900;font-size:8px;letter-spacing:0.35px;text-transform:uppercase;}

  .zkdd-grid{display:grid;grid-template-columns:minmax(160px, 1fr) auto;gap:6px;align-items:end;}
  .zkdd-grid3{display:grid;grid-template-columns:minmax(160px, 1fr) 92px auto;gap:6px;align-items:end;}

  .zkdd-field{display:flex;flex-direction:column;gap:2px;min-width:0;}
  .zkdd-field label{font-size:7px;color:#9fd2f1;letter-spacing:0.25px;font-weight:900;text-transform:uppercase;}
  .zkdd-field input{width:100%;max-width:260px;min-width:0;height:22px;padding:1px 4px;border:1px solid #3d6a8b;background:#163247;color:#e8f0f8;border-radius:2px;outline:none;font-size:9px;font-family:Tahoma,Arial,sans-serif;}
  .zkdd-field input:focus{border-color:#3da5d9;box-shadow:0 0 2px #3da5d9;}

  .zkdd-help{color:#7db3d9;font-size:8px;line-height:1.15;margin-top:2px;font-style:italic;}
  .zkdd-actions{display:flex;gap:6px;align-items:center;justify-content:flex-end;flex-wrap:wrap;}

  .zkdd-btn{height:22px;padding:0 8px;border-radius:2px;font-weight:900;font-size:9px;border:1px solid #3d6a8b;cursor:pointer;display:inline-flex;align-items:center;gap:6px;background:#2d5a7b;color:#fff;transition: background 120ms ease,border-color 120ms ease;}
  .zkdd-btn:hover{background:#3d7a9b;border-color:#4d8aab;}
  .zkdd-btn.primary{background:#3da5d9;border-color:#2c8ec0;color:#fff;}
  .zkdd-btn.primary:hover{background:#2c8ec0;border-color:#1a5a8f;}
  .zkdd-btn.ping{background:#2da44e;border-color:#2da44e;color:#fff;}
  .zkdd-btn.ping:hover{background:#22863a;border-color:#22863a;}
  .zkdd-btn.test{background:#3da5d9;border-color:#2c8ec0;color:#fff;}
  .zkdd-btn.test:hover{background:#2c8ec0;border-color:#1a5a8f;}

  .zkdd-results{margin-top:6px;border:1px solid #3d6a8b;background:#0f2433;border-radius:2px;padding:6px;min-height:18px;white-space:normal;color:#e8f0f8;font-size:9px;}
  .zkdd-results.is-open{animation: zkddPop 160ms ease-out both;}
  @keyframes zkddPop{from{transform: translateY(3px);opacity:0.0;}to{transform:none;opacity:1.0;}}
  .zkdd-results .zkdd-loading{display:inline-flex;align-items:center;gap:8px;font-weight:900;color:#9fd2f1;}
  .zkdd-results .zkdd-spinner{width:12px;height:12px;border-radius:999px;border:2px solid rgba(61,165,217,0.22);border-top-color:#3da5d9;animation: zkddSpin 0.9s linear infinite;}
  @keyframes zkddSpin{to{transform:rotate(360deg);}}

  .zkdd-ip{display:inline-flex;align-items:center;gap:8px;padding:3px 8px;margin:4px 6px 0 0;border-radius:999px;border:1px solid #3d6a8b;background:rgba(61,165,217,0.10);cursor:pointer;color:#e8f0f8;font-size:9px;font-weight:900;}
  .zkdd-ip:hover{background:rgba(61,165,217,0.18);}
  `;

  function ensureStyle(){
    if(document.getElementById('zkdd-style')) return;
    const st = document.createElement('style');
    st.id = 'zkdd-style';
    st.textContent = CSS;
    document.head.appendChild(st);
  }

  function ensureModal(){
    ensureStyle();
    let overlay = document.getElementById('zkdd-overlay');
    if(overlay) return overlay;

    overlay = document.createElement('div');
    overlay.id = 'zkdd-overlay';
    overlay.className = 'zkdd-overlay';
    overlay.innerHTML = `
      <div class="zkdd-modal" role="dialog" aria-modal="true">
        <div class="zkdd-header">
          <div class="zkdd-title">
            <div class="t1">Descoperire / Testare dispozitive</div>
            <div class="t2">Scanare • Ping • Test port (rapid, compact)</div>
          </div>
          <button type="button" class="zkdd-close" data-zkdd-close="1" title="Închide">✕</button>
        </div>
        <div class="zkdd-body">
          <div class="zkdd-section">
            <h4>Scanare rețea</h4>
            <div class="zkdd-grid">
              <div class="zkdd-field">
                <label>Prefix rețea</label>
                <input type="text" data-zkdd-netbase value="192.168.1" placeholder="192.168.1" />
                <div class="zkdd-help">Primele 3 octeți: scanează XXX.XXX.XXX.1-254</div>
              </div>
              <div class="zkdd-actions">
                <button type="button" class="zkdd-btn primary" data-zkdd-scan="1">🔎 Scanează</button>
              </div>
            </div>
          </div>

          <div class="zkdd-section">
            <h4>Ping</h4>
            <div class="zkdd-grid">
              <div class="zkdd-field">
                <label>IP</label>
                <input type="text" data-zkdd-pingip placeholder="192.168.1.235" />
              </div>
              <div class="zkdd-actions">
                <button type="button" class="zkdd-btn ping" data-zkdd-ping="1">📡 Ping</button>
              </div>
            </div>
          </div>

          <div class="zkdd-section">
            <h4>Test port TCP</h4>
            <div class="zkdd-grid3">
              <div class="zkdd-field">
                <label>IP</label>
                <input type="text" data-zkdd-portip placeholder="192.168.1.235" />
              </div>
              <div class="zkdd-field">
                <label>Port</label>
                <input type="number" data-zkdd-port value="14370" min="1" max="65535" />
              </div>
              <div class="zkdd-actions">
                <button type="button" class="zkdd-btn test" data-zkdd-porttest="1">🔌 Test</button>
              </div>
            </div>
          </div>

          <div class="zkdd-results" data-zkdd-results style="display:none"></div>
        </div>
      </div>
    `;

    overlay.addEventListener('click', (e)=>{
      if(e.target === overlay) close();
    });

    overlay.addEventListener('click', (e)=>{
      const t = e.target;
      if(!t) return;
      if(t && t.getAttribute && t.getAttribute('data-zkdd-close') === '1') close();
    });

    document.addEventListener('keydown', (e)=>{
      if(e.key === 'Escape' && overlay.classList.contains('is-open')) close();
    });

    document.body.appendChild(overlay);
    return overlay;
  }

  let currentTargetForm = null;

  function showResults(html, color){
    const overlay = ensureModal();
    const box = overlay.querySelector('[data-zkdd-results]');
    if(!box) return;
    box.style.display = 'block';
    box.style.color = color || '#e8f0f8';
    box.innerHTML = html;
    try{ box.classList.remove('is-open'); void box.offsetWidth; box.classList.add('is-open'); }catch(_e){}
  }

  function setFormIpPort(ip, port){
    if(!currentTargetForm) return;
    try{
      const ipInput = currentTargetForm.querySelector('input[name="ip_address"], input#id_ip_address');
      if(ipInput){
        ipInput.value = ip;
        ipInput.dispatchEvent(new Event('input', {bubbles:true}));
      }
      if(port){
        const portInput = currentTargetForm.querySelector('input[name="port"], input#id_port');
        if(portInput){
          portInput.value = String(port);
          portInput.dispatchEvent(new Event('input', {bubbles:true}));
        }
      }
    }catch(_e){
      // ignore
    }
  }

  async function scan(){
    const overlay = ensureModal();
    const base = (overlay.querySelector('[data-zkdd-netbase]')?.value || '').trim();
    if(!base) { showResults('❌ Introdu prefixul rețelei (ex: 192.168.1)', '#ff9999'); return; }
    showResults('<span class="zkdd-loading"><span class="zkdd-spinner"></span>Scanare în curs... (poate dura 30-60 secunde)</span>');
    try{
      const resp = await fetch(`/agent/devices/discover/?base=${encodeURIComponent(base)}`);
      const data = await resp.json();
      if(data && data.ok && Array.isArray(data.responsive) && data.responsive.length){
        const ips = data.responsive;
        const pills = ips.map(ip => `<span class="zkdd-ip" data-zkdd-use="1" data-ip="${ip}">${ip}</span>`).join('');
        showResults(`<strong style="color:#2da44e;">✓ Găsite ${data.count || ips.length} dispozitive</strong><div class="zkdd-help">Click pe IP ca să îl pui în formular</div><div style="margin-top:6px;">${pills}</div>`);
      } else {
        showResults('❌ Nicio adresă receptivă găsită (ICMP poate fi blocat)', '#ff9999');
      }
    }catch(e){
      showResults('❌ Eroare: ' + (e && e.message ? e.message : String(e)), '#ff9999');
    }
  }

  async function ping(){
    const overlay = ensureModal();
    const ip = (overlay.querySelector('[data-zkdd-pingip]')?.value || '').trim();
    if(!ip) { showResults('❌ Introdu un IP pentru ping', '#ff9999'); return; }
    showResults('<span class="zkdd-loading"><span class="zkdd-spinner"></span>Testare conectivitate...</span>');
    try{
      const resp = await fetch(`/agent/devices/ping/?ip=${encodeURIComponent(ip)}`);
      const data = await resp.json();
      if(data && data.ok && data.alive){
        showResults(`<strong style="color:#2da44e;">🟢 ${ip} ONLINE ✓</strong><div style="margin-top:6px;"><span class="zkdd-ip" data-zkdd-use="1" data-ip="${ip}">➕ Folosește ${ip}</span></div>`);
      } else if(data && data.ok) {
        showResults(`🔴 ${ip} NU răspunde la ping`, '#ff9999');
      } else {
        showResults('❌ Eroare ping: ' + (data && data.error ? data.error : 'unknown'), '#ff9999');
      }
    }catch(e){
      showResults('❌ Eroare: ' + (e && e.message ? e.message : String(e)), '#ff9999');
    }
  }

  async function portTest(){
    const overlay = ensureModal();
    const ip = (overlay.querySelector('[data-zkdd-portip]')?.value || '').trim();
    const port = (overlay.querySelector('[data-zkdd-port]')?.value || '').trim();
    if(!ip) { showResults('❌ Introdu un IP pentru test port', '#ff9999'); return; }
    const p = port || '4370';
    showResults(`<span class="zkdd-loading"><span class="zkdd-spinner"></span>Testare port ${p} pe ${ip}...</span>`);
    try{
      const resp = await fetch(`/agent/devices/port-test/?ip=${encodeURIComponent(ip)}&port=${encodeURIComponent(p)}`);
      const data = await resp.json();
      if(data && data.ok && data.open){
        showResults(`<strong style="color:#2da44e;">✓ Port ${data.port} DESCHIS pe ${data.ip}</strong><div style="margin-top:6px;"><span class="zkdd-ip" data-zkdd-use="1" data-ip="${ip}" data-port="${data.port}">➕ Folosește ${ip}:${data.port}</span></div>`);
      } else if(data && data.ok) {
        showResults(`<strong style="color:#ff9999;">✗ Port ${data.port || p} ÎNCHIS/FILTRAT pe ${data.ip || ip}</strong>`, '#ff9999');
      } else {
        showResults('❌ Eroare: ' + (data && data.error ? data.error : 'unknown'), '#ff9999');
      }
    }catch(e){
      showResults('❌ Eroare: ' + (e && e.message ? e.message : String(e)), '#ff9999');
    }
  }

  function open(opts){
    const overlay = ensureModal();
    currentTargetForm = (opts && opts.targetForm) ? opts.targetForm : null;

    // Best-effort prefill from current form
    try{
      if(currentTargetForm){
        const ip = (currentTargetForm.querySelector('input[name="ip_address"], input#id_ip_address')?.value || '').trim();
        const port = (currentTargetForm.querySelector('input[name="port"], input#id_port')?.value || '').trim();
        if(ip){
          const ping = overlay.querySelector('[data-zkdd-pingip]');
          const pip = overlay.querySelector('[data-zkdd-portip]');
          if(ping) ping.value = ip;
          if(pip) pip.value = ip;
        }
        if(port){
          const p = overlay.querySelector('[data-zkdd-port]');
          if(p) p.value = port;
        }
      }
    }catch(_e){
      // ignore
    }

    overlay.classList.add('is-open');
  }

  function close(){
    const overlay = ensureModal();
    overlay.classList.remove('is-open');
    currentTargetForm = null;
  }

  document.addEventListener('click', (e)=>{
    const t = e.target;
    if(!t) return;

    // Open button inside any injected modal/device form
    if(t.matches && t.matches('[data-zk-device-discovery="1"]')){
      e.preventDefault();
      const form = t.closest('form');
      open({targetForm: form});
      return;
    }

    // Modal internal actions
    if(t.matches && t.matches('[data-zkdd-scan="1"]')){ e.preventDefault(); scan(); return; }
    if(t.matches && t.matches('[data-zkdd-ping="1"]')){ e.preventDefault(); ping(); return; }
    if(t.matches && t.matches('[data-zkdd-porttest="1"]')){ e.preventDefault(); portTest(); return; }

    if(t.matches && t.matches('[data-zkdd-use="1"]')){
      e.preventDefault();
      const ip = t.getAttribute('data-ip') || '';
      const port = t.getAttribute('data-port') || '';
      if(ip){
        setFormIpPort(ip, port);
      }
      return;
    }
  });

  window.zkDeviceDiscovery = { open, close };
})();
