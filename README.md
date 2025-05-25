# Portfolio Tracker

A web application to track your diverse financial assets, including stocks, cryptocurrencies, and physical assets. Built with Python, Flask, and a touch of JavaScript for a dynamic frontend experience.

## Features

*   **Add Assets**: Easily add various types of assets (Stocks, Cryptocurrencies, Physical Assets) with specific details.
*   **View Portfolio**: See an overview of all your assets and their current total value.
*   **Dynamic Price Updates**: Fetches and updates current prices for stocks (via Alpha Vantage) and cryptocurrencies (via CoinGecko).
*   **Asset Management**: Delete assets from your portfolio.
*   **Data Persistence**: Uses an SQLite database to store asset information.
*   **Web Interface**: User-friendly interface for managing and viewing your portfolio.

## Tech Stack

*   **Python 3.x**
*   **Flask**: For the web framework and backend API.
*   **SQLAlchemy**: For ORM and database interaction.
*   **SQLite**: As the database (included with Python).
*   **Requests**: For making external API calls to fetch prices.
*   **HTML/CSS/JavaScript**: For the frontend interface.
    *   **Bootstrap 5**: For responsive design and pre-styled components.
    *   **Google Fonts (Montserrat & Open Sans)**: For enhanced typography.

## Application Structure

*   `app.py`: The main Flask application. Handles routing, API endpoints for managing assets, and fetching prices.
*   `models.py`: Defines the database schema using SQLAlchemy, including the `Asset` base class and inherited classes for `Stock`, `Cryptocurrency`, and `PhysicalAsset`.
*   `extensions.py`: Initializes shared extensions like SQLAlchemy.
*   `static/`: Contains static files.
    *   `style.css`: Custom CSS for styling the web interface, providing a more human-friendly look than default Bootstrap.
    *   `script.js`: Frontend JavaScript for dynamically loading portfolio data, handling the "Add Asset" form (including showing/hiding type-specific fields), and deleting assets.
*   `templates/`: Contains HTML templates.
    *   `index.html`: The main page of the application, displaying the portfolio overview, assets list, and the form to add new assets.
*   `instance/portfolio.db`: The SQLite database file where all asset data is stored (created automatically).


### Main Page (`/`)

*   **Portfolio Overview**:
    *   Displays the total current value of all assets.
*   **Assets List**:
    *   Shows a card for each asset in the portfolio, displaying:
        *   Name, Type, ID
        *   Current Value, Initial Value, Purchase Date
        *   Description (if provided)
        *   Type-specific details (e.g., Ticker/Shares for Stocks, Symbol/Quantity for Crypto).
    *   Provides a "Delete" button for each asset.
*   **Add New Asset Form**:
    *   Select asset type (Stock, Cryptocurrency, Physical Asset).
    *   Dynamically shows relevant fields based on the selected type.
    *   Input common details: Name, Initial Value, Description, Purchase Date.
    *   Input type-specific details:
        *   **Stock**: Ticker Symbol, Shares Owned, Exchange, Current Total Value (Optional - will fetch if not provided).
        *   **Cryptocurrency**: Symbol, Quantity Owned, Wallet Address, Current Total Value (Optional - will fetch if not provided).
        *   **Physical Asset**: Current Estimated Value, Location, Condition.


## Future Improvements

*   **User Authentication**: Secure the portfolio with user login.
*   **Edit Functionality**: Allow editing of existing assets.
*   **Enhanced Analytics**: Add charts and graphs to visualize portfolio performance, diversification, and historical value.
*   **More Price Sources**: Integrate additional APIs for broader asset coverage or more robust price fetching.
*   **Error Handling & UI Feedback**: Improve user feedback for API errors, form validation, etc.
*   **Configuration File**: Move API keys and other settings to a configuration file.
*   **Dockerization**: Package the application in a Docker container for easier deployment.
*   **Testing**: Add unit and integration tests. 
