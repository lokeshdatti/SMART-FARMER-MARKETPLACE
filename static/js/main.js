// Smart Farmer-to-Consumer Green Vegetable Marketplace
// Core Front-end Interactivity Engine

document.addEventListener('DOMContentLoaded', () => {
    // 1. Light / Dark Theme Toggle
    initThemeToggle();
    
    // 2. Farmer Dashboard Edit Modal Handler
    initFarmerModals();
    
    // 3. Dynamic AI Price Prediction Graph
    initPredictionChart();
    
    // 4. Quantity inputs and cart update auto-submit
    initCartQuantityAutoSubmit();
});

// --- Theme Toggle Implementation ---
function initThemeToggle() {
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (!themeBtn) return;
    
    // Check saved theme or system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-theme');
        themeBtn.innerHTML = '☀️'; // Sun icon for light mode
    } else {
        themeBtn.innerHTML = '🌙'; // Moon icon for dark mode
    }
    
    themeBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        themeBtn.innerHTML = isDark ? '☀️' : '🌙';
    });
}

// --- Farmer Dashboard Add/Edit Modals ---
function initFarmerModals() {
    // Edit Product modal
    const editButtons = document.querySelectorAll('.edit-product-btn');
    const editModal = document.getElementById('edit-product-modal');
    const closeEditModalBtn = document.getElementById('close-edit-modal-btn');
    
    if (editButtons.length && editModal) {
        editButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const name = btn.dataset.name;
                const category = btn.dataset.category;
                const price = btn.dataset.price;
                const quantity = btn.dataset.quantity;
                const unit = btn.dataset.unit;
                const description = btn.dataset.description;
                const imageUrl = btn.dataset.imageurl;
                
                // Prefill form action
                const form = document.getElementById('edit-product-form');
                form.action = `/farmer/product/update/${id}`;
                
                // Prefill fields
                document.getElementById('edit-name').value = name;
                document.getElementById('edit-category').value = category;
                document.getElementById('edit-price').value = price;
                document.getElementById('edit-quantity').value = quantity;
                document.getElementById('edit-unit').value = unit;
                document.getElementById('edit-description').value = description;
                document.getElementById('edit-image-url').value = imageUrl;
                
                // Show modal
                editModal.style.display = 'flex';
            });
        });
        
        closeEditModalBtn.addEventListener('click', () => {
            editModal.style.display = 'none';
        });
        
        // Close on clicking overlay
        editModal.addEventListener('click', (e) => {
            if (e.target === editModal) {
                editModal.style.display = 'none';
            }
        });
    }
    
    // Add Product Modal
    const addProductBtn = document.getElementById('add-product-btn');
    const addModal = document.getElementById('add-product-modal');
    const closeAddModalBtn = document.getElementById('close-add-modal-btn');
    
    if (addProductBtn && addModal) {
        addProductBtn.addEventListener('click', () => {
            addModal.style.display = 'flex';
        });
        
        closeAddModalBtn.addEventListener('click', () => {
            addModal.style.display = 'none';
        });
        
        addModal.addEventListener('click', (e) => {
            if (e.target === addModal) {
                addModal.style.display = 'none';
            }
        });
    }
}

// --- AI Price Prediction Graphing ---
let predictionChartInstance = null;

function initPredictionChart() {
    const canvas = document.getElementById('predictionChart');
    if (!canvas) return;
    
    const category = canvas.dataset.category;
    const demandSelector = document.getElementById('demand-select');
    const supplySelector = document.getElementById('supply-select');
    const currentMonthNum = parseInt(canvas.dataset.currentMonth || '6');
    
    // Function to fetch and update graph
    const updateGraph = async () => {
        const demand = demandSelector ? demandSelector.value : 'Medium';
        const supply = supplySelector ? supplySelector.value : 'Medium';
        
        try {
            const response = await fetch(`/api/price-predict?category=${encodeURIComponent(category)}&demand=${demand}&supply=${supply}`);
            const data = await response.json();
            
            if (data.error) {
                console.error("API Error:", data.error);
                return;
            }
            
            const labels = data.trend.map(item => item.month_name);
            const prices = data.trend.map(item => item.price);
            
            // Highlight the current month in the styling
            const pointBackgroundColors = data.trend.map(item => 
                item.month_num === currentMonthNum ? '#ffb703' : '#40916c'
            );
            const pointRadii = data.trend.map(item => 
                item.month_num === currentMonthNum ? 8 : 4
            );
            
            renderChart(canvas, labels, prices, pointBackgroundColors, pointRadii);
            updatePredictiveStats(data.trend, currentMonthNum);
            
        } catch (err) {
            console.error("Failed to load predictions:", err);
        }
    };
    
    // Event listeners
    if (demandSelector) demandSelector.addEventListener('change', updateGraph);
    if (supplySelector) supplySelector.addEventListener('change', updateGraph);
    
    // Initial draw
    updateGraph();
}

function renderChart(canvas, labels, dataPoints, pointColors, pointRadii) {
    const ctx = canvas.getContext('2d');
    
    // Destroy previous chart to avoid overlapping
    if (predictionChartInstance) {
        predictionChartInstance.destroy();
    }
    
    // Get colors based on dark mode status
    const isDark = document.body.classList.contains('dark-theme');
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = isDark ? '#a0aec0' : '#4a5568';
    
    predictionChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Predicted Price (Rs./Unit)',
                data: dataPoints,
                borderColor: '#2d6a4f',
                borderWidth: 3,
                backgroundColor: 'rgba(116, 198, 157, 0.15)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: pointColors,
                pointBorderColor: '#1b4332',
                pointHoverRadius: 9,
                pointRadius: pointRadii
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` Rs. ${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor,
                        font: {
                            family: "'Inter', sans-serif"
                        }
                    }
                },
                y: {
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor,
                        font: {
                            family: "'Inter', sans-serif"
                        }
                    }
                }
            }
        }
    });
}

function updatePredictiveStats(trendData, currentMonthNum) {
    const currentPriceElement = document.getElementById('current-predict-price');
    const minPriceElement = document.getElementById('min-predict-price');
    const maxPriceElement = document.getElementById('max-predict-price');
    
    if (!currentPriceElement) return;
    
    const currentMonthData = trendData.find(item => item.month_num === currentMonthNum);
    if (currentMonthData) {
        currentPriceElement.innerText = `Rs. ${currentMonthData.price.toFixed(2)}`;
    }
    
    const prices = trendData.map(item => item.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    
    minPriceElement.innerText = `Rs. ${minPrice.toFixed(2)}`;
    maxPriceElement.innerText = `Rs. ${maxPrice.toFixed(2)}`;
}

// --- Cart auto-updates on input blur/change ---
function initCartQuantityAutoSubmit() {
    const qtyInputs = document.querySelectorAll('.cart-qty-input');
    qtyInputs.forEach(input => {
        input.addEventListener('change', () => {
            const form = input.closest('form');
            if (form) form.submit();
        });
    });
}
