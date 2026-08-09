// JS helper to initiate MTN/Airtel Mobile Money collection via /momo/initiate
// Expects donate.html to include inputs with IDs: momo-provider, momo-phone, momo-amount, momo-currency

async function initiateMoMo() {
  const provider = document.querySelector('input[name="momo_provider"]:checked').value;
  const phone = document.getElementById('momo-phone').value;
  const amount = document.getElementById('momo-amount').value;
  const currency = document.getElementById('momo-currency').value || 'UGX';

  if (!phone || !amount) {
    alert('Please enter phone and amount');
    return;
  }

  const payload = { provider, phone, amount, currency };
  try {
    const res = await fetch('/momo/initiate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      alert('Initiated. Transaction reference: ' + data.tx_ref + '\n' + data.message);
      // Optionally show tx_ref on the page or allow user to check status
      document.getElementById('momo-txref').textContent = data.tx_ref;
    } else {
      alert('Error: ' + data.message);
    }
  } catch (err) {
    console.error(err);
    alert('Network error initiating payment');
  }
}

// Optional: function to query status
async function checkStatus() {
  const tx_ref = document.getElementById('momo-txref').textContent;
  const provider = document.querySelector('input[name="momo_provider"]:checked').value;
  if (!tx_ref) { alert('No transaction reference to check'); return; }
  try {
    const res = await fetch('/momo/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, tx_ref })
    });
    const data = await res.json();
    if (data.success) {
      alert('Status: ' + data.status);
    } else {
      alert('Error: ' + data.message);
    }
  } catch (err) {
    console.error(err);
    alert('Network error checking status');
  }
}
