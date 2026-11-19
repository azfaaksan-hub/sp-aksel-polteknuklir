/* Panel USB DECY-13. Memakai koneksi MQTT yang sudah dibuka HMI. */
window.attachDecyUsbPanel = function (client) {
  const key = 'decy-usb-panel';
  document.getElementById(key)?.remove();
  const panel = document.createElement('details');
  panel.id = key;
  panel.open = true;
  panel.style.cssText = 'margin:16px;padding:14px;border:1px solid #425671;border-radius:10px;background:#151c30;color:#e5effa';
  panel.innerHTML = `<summary>Panel tiga TFT · USB Raspberry Pi</summary>
    <p data-link role="status"></p><p data-values></p>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button data-action="START">Mulai RPM simulasi</button>
      <button data-action="STOP">Jeda keluaran</button>
      <button data-action="LED">Ganti LED Uno</button>
    </div>
    <p data-result role="status"></p>`;
  const header = document.querySelector('header');
  if (header) header.after(panel);
  else document.body.prepend(panel);
  const prefix = 'decy13/usb/';
  const link = panel.querySelector('[data-link]');
  const values = panel.querySelector('[data-values]');
  const result = panel.querySelector('[data-result]');
  const buttons = [...panel.querySelectorAll('button')];
  buttons.forEach(b => { b.style.cssText = 'padding:6px 10px;border:1px solid #7b94a9;border-radius:5px'; });
  let snapshot = null, last = -Infinity, pending = null;
  function render() {
    const fresh = client.connected && performance.now() - last <= 2000;
    const nodes = fresh ? snapshot.nodes : {};
    const actuator = nodes.actuator?.online ? nodes.actuator.data : null;
    const sensor = nodes.sensor?.online ? nodes.sensor.data : null;
    link.textContent = fresh
      ? ['hmi', 'sensor', 'actuator'].map((name, i) => 'TFT ' + (i + 1) + ' ' + (nodes[name]?.online ? 'online' : 'offline')).join(' · ')
      : 'Menunggu telemetri hub USB';
    values.textContent = [
      actuator && Number.isInteger(actuator.bits) && `${actuator.rpm} / ${actuator.target} RPM · LED ${['mati','hijau','kuning','merah'][actuator.bits & 3]} · kipas ${actuator.bits & 4 ? 'nyala' : 'mati'} · relai ${actuator.bits & 16 ? 'nyala' : 'mati'} · alarm ${actuator.bits & 8 ? 'nyala' : 'mati'} · katup ${actuator.bits & 32 ? 'nyala' : 'mati'} · interlock ${actuator.guard ? 'siap' : 'terbuka'}`,
      sensor && Number.isInteger(sensor.temp_dc) && `${sensor.vac_pa} Pa · ${sensor.hv_v} V simulasi · ${(sensor.temp_dc / 10).toFixed(1)} °C`
    ].filter(Boolean).join(' | ');
    if (pending && (!fresh || performance.now() >= pending.deadline)) {
      result.textContent = 'Konfirmasi perangkat belum diterima.';
      pending = null;
    }
    for (const button of buttons) {
      button.disabled = !(actuator && snapshot.commands === true && !pending &&
        (button.dataset.action === 'STOP' || (actuator.guard && actuator.link &&
          (button.dataset.action !== 'LED' || actuator.mode !== 1))));
      button.style.opacity = button.disabled ? '.5' : '1';
    }
    return actuator;
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    const actuator = render();
    if (button.disabled || !actuator) return;
    const action = button.dataset.action;
    const val = action === 'LED' ? ((actuator.bits & 3) + 1) % 4 : 1;
    const request = Array.from(crypto.getRandomValues(new Uint32Array(3)), n => n.toString(16).padStart(8, '0')).join('');
    pending = { request, deadline: performance.now() + 2200 };
    result.textContent = 'Menunggu konfirmasi Uno…';
    client.publish(prefix + 'cmd', JSON.stringify({ request, target: 'actuator', action, val }), { qos: 0, retain: false });
    render();
  }));
  client.on('connect', () => client.subscribe([prefix + 'state', prefix + 'ack'], { qos: 0 }));
  client.on('message', (topic, payload, packet) => {
    if (packet?.retain || ![prefix + 'state', prefix + 'ack'].includes(topic)) return;
    let value;
    try { value = JSON.parse(payload.toString()); } catch { return; }
    if (!value || typeof value !== 'object') return;
    if (topic === prefix + 'state' && value.version === 1 && value.nodes) {
      snapshot = value;
      last = performance.now();
    }
    if (topic === prefix + 'ack' && pending && value.request === pending.request) {
      result.textContent = value.ok === true ? 'Perintah diterapkan oleh Uno.' :
        'Perintah ditolak atau belum terkonfirmasi (' + Number(value.code) + ').';
      pending = null;
    }
    render();
  });
  client.on('close', () => { last = -Infinity; render(); });
  const timer = setInterval(() => {
    if (!panel.isConnected) clearInterval(timer);
    else render();
  }, 250);
  render();
};
