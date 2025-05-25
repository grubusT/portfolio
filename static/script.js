// JavaScript for fetching and displaying portfolio data will go here. 

document.addEventListener('DOMContentLoaded', () => {
    const totalValueElement = document.getElementById('total-value');
    const assetsContainer = document.getElementById('assets-container');
    const addAssetForm = document.getElementById('add-asset-form');
    const assetTypeSelect = document.getElementById('asset-type');

    // Helper function to format ISO date string to DD-MM-YYYY
    function formatDateDDMMYYYY(isoString) {
        if (!isoString) return 'N/A'; // Handle cases where date might be null or undefined
        const date = new Date(isoString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
        const year = date.getFullYear();
        return `${day}-${month}-${year}`;
    }

    // Function to show/hide asset-specific fields based on selection
    function toggleAssetSpecificFields() {
        const selectedType = assetTypeSelect.value;
        document.querySelectorAll('.asset-specific-fields').forEach(fieldSection => {
            fieldSection.style.display = 'none';
        });

        if (selectedType === 'stock') {
            document.getElementById('stock-fields').style.display = 'block';
        } else if (selectedType === 'cryptocurrency') {
            document.getElementById('crypto-fields').style.display = 'block';
        } else if (selectedType === 'physical_asset') {
            document.getElementById('physical-asset-fields').style.display = 'block';
        }
    }

    if (assetTypeSelect) {
        assetTypeSelect.addEventListener('change', toggleAssetSpecificFields);
    }

    // Function to fetch and display portfolio data
    async function fetchAndDisplayPortfolio() {
        try {
            const response = await fetch('/portfolio');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            // Update total value
            totalValueElement.textContent = `$${data.total_value.toFixed(2)}`;

            // Clear previous assets
            assetsContainer.innerHTML = '';

            if (data.assets && data.assets.length > 0) {
                data.assets.forEach(asset => {
                    const assetCol = document.createElement('div');
                    assetCol.classList.add('col'); // For Bootstrap grid

                    const cardDiv = document.createElement('div');
                    cardDiv.classList.add('card', 'h-100'); // h-100 for equal height cards in a row

                    let cardBodyContent = `
                        <div class="card-header">${asset.name} <small class="text-muted">(${asset.asset_type})</small></div>
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item"><strong>ID:</strong> ${asset.id}</li>
                            <li class="list-group-item"><strong>Current Value:</strong> <span class="fw-bold text-success">$${asset.current_value.toFixed(2)}</span></li>
                            <li class="list-group-item"><strong>Initial Value:</strong> $${asset.initial_value.toFixed(2)}</li>
                            <li class="list-group-item"><strong>Purchase Date:</strong> ${formatDateDDMMYYYY(asset.purchase_date)}</li>
                    `;

                    if (asset.description) {
                        cardBodyContent += `<li class="list-group-item"><strong>Description:</strong> ${asset.description}</li>`;
                    }

                    // Type-specific details
                    if (asset.asset_type === 'Stock') {
                        cardBodyContent += `<li class="list-group-item"><strong>Ticker:</strong> ${asset.ticker_symbol}</li>`;
                        cardBodyContent += `<li class="list-group-item"><strong>Shares:</strong> ${asset.shares_owned}</li>`;
                        if (asset.exchange) cardBodyContent += `<li class="list-group-item"><strong>Exchange:</strong> ${asset.exchange}</li>`;
                    } else if (asset.asset_type === 'Cryptocurrency') {
                        cardBodyContent += `<li class="list-group-item"><strong>Symbol:</strong> ${asset.symbol}</li>`;
                        cardBodyContent += `<li class="list-group-item"><strong>Quantity:</strong> ${asset.quantity_owned}</li>`;
                        if (asset.wallet_address) cardBodyContent += `<li class="list-group-item"><strong>Wallet:</strong> ${asset.wallet_address}</li>`;
                    } else if (asset.asset_type === 'PhysicalAsset') {
                        if (asset.location) cardBodyContent += `<li class="list-group-item"><strong>Location:</strong> ${asset.location}</li>`;
                        if (asset.condition) cardBodyContent += `<li class="list-group-item"><strong>Condition:</strong> ${asset.condition}</li>`;
                    }
                    cardBodyContent += `</ul>`; // Close list-group
                    
                    // Card footer for actions
                    cardBodyContent += `
                        <div class="card-footer text-end">
                            <button class="btn btn-danger btn-sm delete-btn" data-id="${asset.id}">Delete</button>
                        </div>
                    `;

                    cardDiv.innerHTML = cardBodyContent;
                    assetCol.appendChild(cardDiv);
                    assetsContainer.appendChild(assetCol);
                });
            } else {
                assetsContainer.innerHTML = '<p>No assets in the portfolio yet.</p>';
            }
        } catch (error) {
            console.error("Failed to fetch portfolio:", error);
            totalValueElement.textContent = 'Error loading data';
            assetsContainer.innerHTML = '<p>Could not load assets. Please check the console.</p>';
        }
    }

    // Handle Add Asset form submission
    if (addAssetForm) {
        addAssetForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            const formData = new FormData(addAssetForm);
            const assetData = {
                asset_type: formData.get('asset_type')
            };

            // Common fields
            assetData.name = formData.get('name');
            assetData.initial_value = parseFloat(formData.get('initial_value'));
            if (formData.get('description')) assetData.description = formData.get('description');
            if (formData.get('purchase_date')) assetData.purchase_date = formData.get('purchase_date'); // API expects ISO string or handles default

            // Type-specific fields
            if (assetData.asset_type === 'stock') {
                assetData.ticker_symbol = formData.get('ticker_symbol');
                assetData.shares_owned = parseFloat(formData.get('shares_owned'));
                if (formData.get('exchange')) assetData.exchange = formData.get('exchange');
                if (formData.get('current_value')) {
                     const stockCurrentValue = formData.get('current_value');
                     if(stockCurrentValue) assetData.current_value = parseFloat(stockCurrentValue);
                }
            } else if (assetData.asset_type === 'cryptocurrency') {
                assetData.symbol = formData.get('symbol');
                assetData.quantity_owned = parseFloat(formData.get('quantity_owned'));
                if (formData.get('wallet_address')) assetData.wallet_address = formData.get('wallet_address');
                // The name for current_value input for crypto is also 'current_value'
                const cryptoCurrentValue = addAssetForm.querySelector('#crypto-fields input[name="current_value"]').value;
                if (cryptoCurrentValue) {
                    assetData.current_value = parseFloat(cryptoCurrentValue);
                }
            } else if (assetData.asset_type === 'physical_asset') {
                assetData.current_estimated_value = parseFloat(formData.get('current_estimated_value'));
                if (formData.get('location')) assetData.location = formData.get('location');
                if (formData.get('condition')) assetData.condition = formData.get('condition');
            }

            // Basic client-side validation for required fields based on type
            let missingFields = [];
            if (!assetData.name) missingFields.push("Name");
            if (isNaN(assetData.initial_value)) missingFields.push("Initial Value");

            if (assetData.asset_type === 'stock'){
                if (!assetData.ticker_symbol) missingFields.push("Ticker Symbol (Stock)");
                if (isNaN(assetData.shares_owned)) missingFields.push("Shares Owned (Stock)");
            } else if (assetData.asset_type === 'cryptocurrency'){
                if (!assetData.symbol) missingFields.push("Symbol (Crypto)");
                if (isNaN(assetData.quantity_owned)) missingFields.push("Quantity Owned (Crypto)");
            } else if (assetData.asset_type === 'physical_asset'){
                if (isNaN(assetData.current_estimated_value)) missingFields.push("Current Estimated Value (Physical Asset)");
            }

            if (missingFields.length > 0) {
                alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
                return;
            }

            try {
                const response = await fetch('/assets', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(assetData),
                });

                if (response.ok) {
                    alert('Asset added successfully!');
                    addAssetForm.reset();
                    toggleAssetSpecificFields(); // Reset to initial hidden state
                    fetchAndDisplayPortfolio(); // Refresh list
                } else {
                    const errorResult = await response.json();
                    alert(`Failed to add asset: ${errorResult.error || response.statusText}`);
                    console.error("Failed to add asset:", errorResult);
                }
            } catch (error) {
                alert('An error occurred while adding the asset.');
                console.error("Error adding asset:", error);
            }
        });
    }

    // Event delegation for delete buttons
    assetsContainer.addEventListener('click', async (event) => {
        if (event.target.classList.contains('delete-btn')) {
            const assetId = event.target.dataset.id;
            if (confirm(`Are you sure you want to delete asset ${assetId}?`)) {
                try {
                    const response = await fetch(`/assets/${assetId}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        alert('Asset deleted successfully');
                        fetchAndDisplayPortfolio(); // Refresh the list
                    } else {
                        const errorData = await response.json();
                        alert(`Failed to delete asset: ${errorData.error || response.statusText}`);
                    }
                } catch (error) {
                    console.error("Error deleting asset:", error);
                    alert('An error occurred while deleting the asset.');
                }
            }
        }
    });

    // Initial fetch
    fetchAndDisplayPortfolio();
}); 