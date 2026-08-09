async function createFlutterwavePayment() {
  const amount = document.getElementById('momo-amount').value;
  const currency = document.getElementById('momo-currency').value || 'UGX';
  const donorEmail = document.getElementById('momo-email').value || '';
  const phone = document.getElementById('momo-phone').value || '';
  const name = document.getElementById('donor-name') ? document.getElementById('donor-name').value : '';

  if (!amount) { alert('Enter an amount'); return; }

  const payload = { amount, currency, donor_email: donorEmail, phone, name };
  try {
    const res = await fetch('/payments/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!data.success) { alert('Error creating payment: ' + data.message); return; }
    // Redirect donor to the hosted payment link
    window.location.href = data.link;
  } catch (err) {
    console.error(err);
    alert('Network error creating payment');
  }
}
