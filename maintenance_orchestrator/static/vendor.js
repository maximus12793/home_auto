document.getElementById('quote-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerText = 'Submitting...';

    const reqId = document.getElementById('correlation_id').value;
    const amountFloat = parseFloat(document.getElementById('amount').value);
    
    const payload = {
        vendor_id: document.getElementById('vendor_id').value,
        amount_cents: Math.round(amountFloat * 100),
        notes: document.getElementById('notes').value
    };

    try {
        const response = await fetch(`/requests/${reqId}/quotes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            document.getElementById('quote-form').classList.add('hidden');
            document.getElementById('success-message').classList.remove('hidden');
        } else {
            const data = await response.json();
            alert('Failed to submit quote: ' + JSON.stringify(data));
        }
    } catch (err) {
        alert('API error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerText = 'Submit Quote';
    }
});
