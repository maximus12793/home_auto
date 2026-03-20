document.getElementById('intake-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerText = 'Submitting...';

    const payload = {
        portfolio_id: "PORTFOLIO-01",
        property_id: document.getElementById('property_id').value,
        unit_id: document.getElementById('unit_id').value,
        channel: "form",
        description: document.getElementById('description').value,
        issue_type: document.getElementById('issue_type').value,
        tenant: {
            display_name: document.getElementById('display_name').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value
        }
    };

    try {
        const response = await fetch('/requests', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            document.getElementById('intake-form').classList.add('hidden');
            document.getElementById('success-message').classList.remove('hidden');
        } else {
            const data = await response.json();
            alert('Failed to submit: ' + JSON.stringify(data));
        }
    } catch (err) {
        alert('API error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerText = 'Submit Request';
    }
});
