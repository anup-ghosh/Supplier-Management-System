let factor = 1;
let resendCount = 0;

function sendOtp() {
    const resendButton = document.getElementById('resend');
    const resendUI = document.getElementById('resend-ui');
    resendButton.disabled = true;
    const email = document.getElementById('email').value;

    // Validate the email format before proceeding
    if (validateEmail(email)) {
        // Check if we've hit the resend limit
        if (resendCount >= 5) {
            alert("You've reached the maximum number of OTP resend attempts. Please try again later.");
            resendButton.textContent = "Resend Limit Reached";
            return;
        }

        // Call the server to validate the email (whether it's allowed or blacklisted)
        fetch('/api/verify_email', {
            method: 'POST',
            body: JSON.stringify({
                email: email // Send email inside the JSON body
            }),
            headers: { 'Content-Type': 'application/json' }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json(); // Parse the response as JSON
            })
            .then(data => {
                const result = data.result;
                if (result.status === "success") {
                    // Email is allowed, show OTP field
                    document.getElementById('otp-container').style.display = 'block';

                    alert(result.message); // OTP sent message
                    const otpButton = document.getElementById('send-otp-btn');
                    otpButton.textContent = 'Verify OTP';
                    otpButton.removeEventListener('click', sendOtp);
                    otpButton.addEventListener('click', verifyOtp);
                    resendUI.style.display = 'block';
                    // Factorial increase in wait time
                    let current = 5 * factor;
                    const interval = setInterval(() => {
                        resendButton.textContent = `You can request OTP after ${current.toString().padStart(2, '0')} s`;
                        current -= 1;
                        if (current < 0) {
                            resendButton.style.display = 'block';
                            resendButton.removeAttribute('disabled');
                            resendButton.textContent = 'Resend OTP';
                            clearInterval(interval);
                        }
                    }, 1000);
                    factor++; // Increase factor for next time
                    resendCount++; // Increment resend count
                } else {
                    alert(result.message); // Show error message from server (e.g., "Email already registered")
                }
            })
            .catch(error => {
                alert("Error validating email: " + error.message); // Generic error handling
            });
    } else {
        alert("Please enter a valid email.");
    }
}

function verifyOtp() {
    const email = document.getElementById('email').value;
    const otp = document.getElementById('otp').value;

    // Call the server to verify the OTP
    fetch('/api/verify_otp', {
        method: 'POST',
        body: JSON.stringify({
            email: email, // Send email and OTP inside the JSON body
            otp: otp
        }),
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json(); // Parse the response as JSON
        })
        .then(data => {
            const result = data.result;
            if (result.status === "success") {
                console.log(result);
                alert(result.message); // OTP verification success
                window.location.href = result.redirect_url;
            } else {
                alert(result.message); // OTP verification failed
            }
        })
        .catch(error => {
            alert("Error verifying OTP: " + error.message); // Specific OTP error
        });
}

function validateEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(String(email).toLowerCase());
}

document.addEventListener('DOMContentLoaded', function() {
    const sendButton = document.getElementById('send-otp-btn');
    sendButton.addEventListener('click', sendOtp);

    const resendButton = document.getElementById('resend');
    resendButton.addEventListener('click', function() {
        // Send OTP again and increase wait time
        factor = Math.max(1, factor); // Ensure factor doesn't go below 1
        sendOtp();
    });
});