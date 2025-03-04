document.addEventListener("DOMContentLoaded", function () {
    function calculateSubtotal(row) {
        let unitPrice = parseFloat(row.querySelector("input[name^='order_line_unit_price']").value) || 0;
        let deliveryCharge = parseFloat(row.querySelector("input[name^='order_line_delivery_charges']").value) || 0;
        let quantity = parseFloat(row.querySelector("input[name^='order_line_quantity']").value) || 0;
        let subtotalField = row.querySelector("input[name^='order_line_subtotal']");

        let subtotal = (unitPrice * quantity) + deliveryCharge;
        subtotalField.value = subtotal.toFixed(2);
    }

    function calculateTotal() {
        let totalSum = 0;
        document.querySelectorAll("tbody#order_lines_container tr").forEach(row => {
            let subtotal = parseFloat(row.querySelector("input[name^='order_line_subtotal']").value) || 0;
            totalSum += subtotal;
        });
        document.getElementById("total-sum").textContent = totalSum.toFixed(2);
    }

    function attachEventListeners() {
        document.querySelectorAll("tbody#order_lines_container tr").forEach(row => {
            row.querySelector("input[name^='order_line_unit_price']").addEventListener("input", function () {
                calculateSubtotal(row);
                calculateTotal();
            });
            row.querySelector("input[name^='order_line_delivery_charges']").addEventListener("input", function () {
                calculateSubtotal(row);
                calculateTotal();
            });
        });
    }

    attachEventListeners();
    calculateTotal(); // Initial calculation on page load
});
