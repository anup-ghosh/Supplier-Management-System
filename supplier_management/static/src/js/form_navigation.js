document.addEventListener("DOMContentLoaded", function () {
    // File Size Validation
    document.querySelectorAll("input[type='file']").forEach(fileInput => {
        fileInput.addEventListener("change", function () {
            validateFileSize(this);
        });
    });

    function validateFileSize(fileInput) {
        let fileSize = fileInput.files[0]?.size / 1024 / 1024; // Convert to MB
        let existingError = fileInput.parentNode.querySelector(".invalid-feedback");

        // Remove previous error if exists
        if (existingError) {
            existingError.remove();
            fileInput.classList.remove("is-invalid");
        }

        if (fileSize > 1) {
            fileInput.classList.add("is-invalid");
            let error = document.createElement("div");
            error.className = "invalid-feedback";
            error.innerText = "File size cannot exceed 1MB.";
            fileInput.parentNode.appendChild(error);

            // Clear the file selection
            fileInput.value = "";
        }
    }

    // Tab Navigation
    document.querySelectorAll(".next-btn").forEach(button => {
        button.addEventListener("click", function () {
            let currentTab = this.closest(".tab-pane");
            let nextTabId = this.getAttribute("data-next");

            if (validateTab(currentTab)) {
                switchTab(currentTab, nextTabId);
            } else {
                alert("Please fill out all required fields correctly before proceeding.");
            }
        });
    });

    let clientCount = 1;
    const maxClients = 5;
    const clientContainer = document.getElementById("clientReferencesContainer");
    const addClientBtn = document.getElementById("addClientBtn");

    // Add Client
    addClientBtn.addEventListener("click", function () {
        if (clientCount < maxClients) {
            clientCount++;

            const clientDiv = document.createElement("div");
            clientDiv.classList.add("client-reference", "border", "rounded", "p-3", "mb-3", "shadow-sm");
            clientDiv.innerHTML = `
                <h5 class="text-secondary">🧑‍💼 Client ${clientCount}</h5>
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Client Name</label>
                        <input type="text" name="client_${clientCount}_name" class="form-control shadow-sm" required />
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">✉ Client Email</label>
                        <input type="text" name="client_${clientCount}_email" class="form-control shadow-sm" />
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-6">
                        <label class="form-label fw-bold">📞 Client Phone</label>
                        <input type="text" name="client_${clientCount}_phone" class="form-control shadow-sm" />
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">📍 Client Address</label>
                        <input type="text" name="client_${clientCount}_address" class="form-control shadow-sm" />
                    </div>
                </div>
                <button type="button" class="btn btn-outline-danger w-100 mt-3 remove-client-btn">
                    ❌ Remove Client
                </button>
            `;

            clientContainer.appendChild(clientDiv);

            // Ensure the new client div is displayed properly after adding it to the DOM
            clientDiv.offsetHeight;

            // Remove Client
            clientDiv.querySelector(".remove-client-btn").addEventListener("click", function () {
                clientDiv.remove();
                clientCount--;

                // Update client numbers
                updateClientNumbers();

                // Re-enable add button if below max
                if (clientCount < maxClients) {
                    addClientBtn.disabled = false;
                }
            });

            // Disable Add Button at Max Limit
            if (clientCount === maxClients) {
                addClientBtn.disabled = true;
            }
        } else {
            alert('You can only add up to 5 clients.');
        }
    });

    // Function to update client numbers when one is removed
    function updateClientNumbers() {
        let clients = document.querySelectorAll('.client-reference');
        clients.forEach((client, index) => {
            client.querySelector('h5').textContent = `🧑‍💼 Client ${index + 1}`;
            // Update the name attributes of inputs
            let inputs = client.querySelectorAll('input');
            inputs.forEach(input => {
                let newName = input.name.replace(/\d+/, index + 1);
                input.setAttribute('name', newName);
            });
        });
    }

    document.querySelectorAll(".prev-btn").forEach(button => {
        button.addEventListener("click", function () {
            let currentTab = this.closest(".tab-pane");
            let prevTabId = this.getAttribute("data-prev");

            switchTab(currentTab, prevTabId);
        });
    });

    function switchTab(currentTab, targetTabId) {
        // Hide the current tab
        currentTab.classList.remove("show", "active");
        currentTab.style.display = "none";

        // Show the target tab
        let targetTab = document.querySelector(targetTabId);
        if (targetTab) {
            targetTab.classList.add("show", "active");
            targetTab.style.display = "block";
        }
    }

    // Tab Validation
    function validateTab(tab) {
    let isValid = true;

    // Clear Previous Errors
    tab.querySelectorAll(".is-invalid").forEach(el => el.classList.remove("is-invalid"));
    tab.querySelectorAll(".invalid-feedback").forEach(el => el.remove());

    // Required Fields
    tab.querySelectorAll("input[required='1'], select[required='1']").forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showError(input, "This field is required.");
        }
    });

    // Trade License Validation
    let tradeLicense = tab.querySelector("input[name='trade_license_number']");
    if (tradeLicense && tradeLicense.value.trim()) {
        let licensePattern = /^[a-zA-Z0-9]{8,20}$/;
        if (!licensePattern.test(tradeLicense.value)) {
            isValid = false;
            showError(tradeLicense, "Trade License Number must be alphanumeric and 8–20 characters long.");
        }
    }

    // Commencement Date (Before Today)
    let commencementDate = tab.querySelector("input[name='commencement_date']");
    if (commencementDate && commencementDate.value) {
        let today = new Date().toISOString().split("T")[0];
        if (commencementDate.value >= today) {
            isValid = false;
            showError(commencementDate, "Commencement date must be before today.");
        }
    }

    // Expiry Date (Future Date)
    let expiryDate = tab.querySelector("input[name='expiry_date']");
    if (expiryDate && expiryDate.value) {
        let today = new Date().toISOString().split("T")[0];
        if (expiryDate.value <= today) {
            isValid = false;
            showError(expiryDate, "Expiry date must be in the future.");
        }
    }

    // TIN Validation (16 Digits)
    let tin = tab.querySelector("input[name='tax_identification_number']");
    if (tin && tin.value.trim()) {
        let tinPattern = /^\d{16}$/;
        if (!tinPattern.test(tin.value)) {
            isValid = false;
            showError(tin, "Tax Identification Number must be a 16-digit numeric string.");
        }
    }

    // Client Reference Validation (Fixing the Issue)
    tab.querySelectorAll(".client-reference").forEach(client => {
        let name = client.querySelector("input[name^='client_'][name$='_name']");
        let email = client.querySelector("input[name^='client_'][name$='_email']");
        let phone = client.querySelector("input[name^='client_'][name$='_phone']");
        let address = client.querySelector("input[name^='client_'][name$='_address']");

        let isEmailFilled = email && email.value.trim() !== "";
        let isPhoneFilled = phone && phone.value.trim() !== "";
        let isAddressFilled = address && address.value.trim() !== "";

        // If any of email, phone, or address is filled, name is required
        if ((isEmailFilled || isPhoneFilled || isAddressFilled) && (!name || name.value.trim() === "")) {
            isValid = false;
            showError(name, "Client Name is required if Email, Phone, or Address is provided.");
        }
    });

    return isValid;
}


    // Show Error Function
    function showError(input, message) {
        // Only show errors for visible and enabled inputs
        if (input.offsetParent !== null && !input.disabled) {
            input.classList.add("is-invalid");
            let error = document.createElement("div");
            error.className = "invalid-feedback";
            error.innerText = message;
            input.parentNode.appendChild(error);
        }
    }

    // Form Submission Validation
    document.getElementById("multi-step-form")?.addEventListener("submit", function (event) {
        let isValid = true;
        document.querySelectorAll(".tab-pane").forEach(tab => {
            if (!validateTab(tab)) {
                isValid = false;
            }
        });

        if (!isValid) {
            event.preventDefault(); // Prevent form submission if validation fails
            alert("Please fill out all required fields correctly before submitting.");
        }
    });

    // Dynamic Subtotal Calculation for RFP Product Lines
    const orderLinesContainer = document.getElementById("order_lines_container");
    if (orderLinesContainer) {
        const rows = orderLinesContainer.querySelectorAll("tr");

        rows.forEach(row => {
            const unitPriceInput = row.querySelector(".unit-price");
            const deliveryChargeInput = row.querySelector(".delivery-charge");
            const quantityInput = row.querySelector(".quantity");
            const subtotalInput = row.querySelector(".subtotal");

            function calculateSubtotal() {
                const unitPrice = parseFloat(unitPriceInput.value) || 0;
                const deliveryCharge = parseFloat(deliveryChargeInput.value) || 0;
                const quantity = parseFloat(quantityInput.value) || 0;
                const subtotal = (unitPrice + deliveryCharge) * quantity;
                subtotalInput.value = subtotal.toFixed(2);
            }

            // Initial calculation
            calculateSubtotal();

            // Add event listeners for real-time updates
            unitPriceInput.addEventListener("input", calculateSubtotal);
            deliveryChargeInput.addEventListener("input", calculateSubtotal);
        });
    }
});