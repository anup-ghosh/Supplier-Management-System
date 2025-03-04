/** @odoo-module */
import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useState, onMounted, useRef } = owl;
import { useService } from "@web/core/utils/hooks";

export class MyDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            supplier: null,
            dateRange: "all_time",
            approvedRFQs: 0,
            totalAmount: 0,
            total_submission: 0,
            productBreakdown: [],
            suppliers: [],
            submitted_rfqs: 0,
            rfqStatus: {},
            rfps: [],
            no_data: true,
            currencySymbol: '$' // Default to empty string
        });

        this.chartRefLine = useRef("chartLine");
        this.chartRefDoughnut = useRef("chartDoughnut");
        this.chartRefBar = useRef("chartBar");
        this.chartInstanceLine = null;
        this.chartInstanceDoughnut = null;
        this.chartInstanceBar = null;

        this.onSupplierChange = this.onSupplierChange.bind(this);
        this.onDateRangeChange = this.onDateRangeChange.bind(this);
        this.fetchData = this.fetchData.bind(this);
        this.loadSuppliers = this.loadSuppliers.bind(this);

        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js");
            await this.loadSuppliers();
        });

        onMounted(() => {
            this.fetchData();
        });
    }

    async loadSuppliers() {
        const suppliers = await this.orm.searchRead("res.partner", [["supplier_rank", ">", 0]], ["id", "name"]);
        this.state.suppliers = suppliers;
    }

    async fetchData() {
        if (!this.state.supplier) return;

        const dateRange = this.getDateRange();
        const datedomain = [["accept_date", ">=", dateRange.start], ["accept_date", "<=", dateRange.end]];
        const domain = [
            ["approved_supplier", "=", this.state.supplier],
            ["status", "=", "accepted"],
        ];
        domain.push(...datedomain);

        const datedomain1 = [["create_date", ">=", dateRange.start], ["create_date", "<=", dateRange.end]];
        const domainSubmitted = [
            ["partner_id", "=", this.state.supplier],
            ["rfp_id", "!=", false],
        ];
        domainSubmitted.push(...datedomain1);

        this.state.approvedRFQs = await this.orm.searchCount("supplier.management.rfp", domain);
        const rfps = await this.orm.searchRead(
            "supplier.management.rfp",
            domain,
            ["id", "rfp_name", "total_amount", "product_lines", "status", "currency_id"]
        );
        this.state.rfps = rfps;

        // Set currency symbol using the logic: accepted_rfps[0].currency_id.symbol if accepted_rfps else ''
        // In Odoo JS, currency_id is typically an array [id, name], so we need to fetch the symbol separately
        let currencySymbol = '';
        if (rfps.length > 0 && rfps[0].currency_id) {
            const currencyId = rfps[0].currency_id[0]; // Get the ID from [id, name]
            const currency = await this.orm.read("res.currency", [currencyId], ["symbol"]);
            currencySymbol = currency[0].symbol || ''; // Fetch the symbol field
        }
        this.state.currencySymbol = currencySymbol;

        this.state.totalAmount = rfps.reduce((sum, rfp) => sum + rfp.total_amount, 0);

        this.state.rfqs_submitted = await this.orm.searchRead("purchase.order", domainSubmitted, ["state", "name", "create_date"]);
        this.state.total_submission = this.state.rfqs_submitted.length;

        const rfqStatus = this.state.rfqs_submitted.reduce((acc, order) => {
            acc[order.state] = (acc[order.state] || 0) + 1;
            return acc;
        }, {});
        this.state.rfqStatus = rfqStatus;

        const productLineIds = rfps.flatMap(rfp => rfp.product_lines);
        const rfp_lines = await this.orm.searchRead(
            "supplier.management.rfp.product.line",
            [["id", "in", productLineIds]],
            ["product_id", "product_name", "product_image", "quantity", "subtotal_price", "delivery_charges", "unit_price"]
        );

        const productMap = new Map();
        for (const line of rfp_lines) {
            const productId = line.product_id[0];
            if (!productMap.has(productId)) {
                productMap.set(productId, {
                    name: line.product_name,
                    image: line.product_image ? `data:image/png;base64,${line.product_image}` : "default_image_url",
                    total_quantity: 0,
                    total_price: 0,
                    total_delivery_charges: 0,
                    unit_price: line.unit_price || 0
                });
            }
            const productData = productMap.get(productId);
            productData.total_quantity += line.quantity;
            productData.total_price += line.subtotal_price;
            productData.total_delivery_charges += line.delivery_charges || 0;
        }

        this.state.productBreakdown = Array.from(productMap.values());
        this.renderCharts();
    }

    getDateRange() {
        const now = new Date();
        let start, end;

        switch (this.state.dateRange) {
            case "all_time":
                start = new Date(0);
                end = new Date();
                end.setHours(23, 59, 59, 999);
                break;
            case "this_week":
                start = new Date(now);
                start.setDate(now.getDate() - now.getDay());
                end = new Date(now);
                end.setDate(start.getDate() + 6);
                end.setHours(23, 59, 59, 999);
                break;
            case "last_week":
                start = new Date(now);
                start.setDate(now.getDate() - now.getDay() - 7);
                end = new Date(now);
                end.setDate(start.getDate() + 6);
                end.setHours(23, 59, 59, 999);
                break;
            case "last_month":
                start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                end = new Date(now.getFullYear(), now.getMonth(), 0);
                end.setHours(23, 59, 59, 999);
                break;
            case "last_year":
                start = new Date(now.getFullYear() - 1, 0, 1);
                end = new Date(now.getFullYear() - 1, 11, 31);
                end.setHours(23, 59, 59, 999);
                break;
            default:
                start = new Date(now);
                start.setDate(now.getDate() - 30);
                end = new Date(now);
                end.setHours(23, 59, 59, 999);
        }

        return {
            start: start.toISOString().split("T")[0],
            end: end.toISOString().split("T")[0],
        };
    }

    onSupplierChange(ev) {
        this.state.supplier = parseInt(ev.target.value);
        this.fetchData();
    }

    onDateRangeChange(ev) {
        this.state.dateRange = ev.target.value;
        this.fetchData();
    }

    renderCharts() {
        if (!this.chartRefBar.el || !this.chartRefDoughnut.el || !this.chartRefLine.el) {
            console.warn("One or more chart canvas elements are missing.");
            this.state.no_data = false;
            return;
        }
        const ctxLine = this.chartRefLine.el.getContext("2d");
        const ctxDoughnut = this.chartRefDoughnut.el.getContext("2d");
        const ctxBar = this.chartRefBar.el.getContext("2d");

        if (this.chartInstanceLine) this.chartInstanceLine.destroy();
        if (this.chartInstanceDoughnut) this.chartInstanceDoughnut.destroy();
        if (this.chartInstanceBar) this.chartInstanceBar.destroy();

        const rfpLabels = this.state.rfps.map(rfp => rfp.rfp_name || `RFP #${rfp.id}`);
        const rfpTotalAmounts = this.state.rfps.map(rfp => rfp.total_amount);

        this.chartInstanceLine = new Chart(ctxLine, {
            type: "line",
            data: {
                labels: rfpLabels,
                datasets: [{
                    label: "Total Amount per RFP",
                    data: rfpTotalAmounts,
                    fill: false,
                    borderColor: "rgba(75, 192, 192, 1)",
                    backgroundColor: "rgba(75, 192, 192, 0.6)",
                    tension: 0.1,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Total Amount",
                        },
                    },
                    x: {
                        title: {
                            display: true,
                            text: "RFP",
                        },
                    },
                },
            },
        });

        const statusLabels = Object.keys(this.state.rfqStatus);
        const statusCounts = Object.values(this.state.rfqStatus);

        this.chartInstanceDoughnut = new Chart(ctxDoughnut, {
            type: "doughnut",
            data: {
                labels: statusLabels,
                datasets: [{
                    label: "RFQ Status Distribution",
                    data: statusCounts,
                    backgroundColor: ["rgba(75, 192, 192, 0.6)", "rgba(153, 102, 255, 0.6)", "rgba(255, 159, 64, 0.6)", "rgba(255, 99, 132, 0.6)"],
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            },
        });

        const productLabels = this.state.productBreakdown.map(product => product.name);
        const productQuantities = this.state.productBreakdown.map(product => product.total_quantity);

        this.chartInstanceBar = new Chart(ctxBar, {
            type: "bar",
            data: {
                labels: productLabels,
                datasets: [{
                    label: "Total Quantity per Product",
                    data: productQuantities,
                    backgroundColor: "rgba(255, 159, 64, 0.2)",
                    borderColor: "rgba(255, 159, 64, 1)",
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Total Quantity",
                        },
                    },
                    x: {
                        title: {
                            display: true,
                            text: "Product",
                        },
                    },
                },
            },
        });
    }

    static template = "supplier_management.dashboard";
}

registry.category("actions").add("supplier_management.supplier_dashboard", MyDashboard);