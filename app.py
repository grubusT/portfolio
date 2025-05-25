from flask import Flask, jsonify, request, render_template
from datetime import datetime
import os
import requests # Added for API calls

from extensions import db # Import db from extensions.py

# Alpha Vantage API Key - REPLACE WITH YOUR KEY
ALPHA_VANTAGE_API_KEY = "YWBWKOL7A0CJRCCA" # User provided this key
# CoinGecko API base URL
COINGECKO_API_BASE_URL = "https://api.coingecko.com/api/v3"

app = Flask(__name__)

# Database Configuration
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'portfolio.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) # Initialize db with app, db is imported from extensions

# Import models after db is initialized and app is created
from models import Asset, Stock, Cryptocurrency, PhysicalAsset



# --- Price Fetching Services ---

def get_stock_price(ticker_symbol: str):
    """Fetches the latest price for a stock from Alpha Vantage."""
    if ALPHA_VANTAGE_API_KEY == "YWBWKOL7A0CJRCCA":
        app.logger.warning("Alpha Vantage API key is not set. Stock prices will not be updated.")
        return None
    
    # Alpha Vantage returns the price per share
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker_symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url, timeout=10) # Added timeout
        response.raise_for_status()
        data = response.json()
        quote = data.get("Global Quote")
        if quote and '05. price' in quote:
            return float(quote['05. price'])
        else:
            app.logger.warning(f"Could not parse price for stock {ticker_symbol} from Alpha Vantage. Response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching stock price for {ticker_symbol} from Alpha Vantage: {e}")
        return None
    except (ValueError, KeyError) as e: # Catch errors if 'Global Quote' or '05. price' is missing
        app.logger.error(f"Error parsing stock price data for {ticker_symbol} from Alpha Vantage: {e}. Response: {data if 'data' in locals() else 'No data'}")
        return None

def get_crypto_price(coingecko_id: str):
    """Fetches the latest price for a cryptocurrency from CoinGecko."""
    # coingecko_id should be like 'bitcoin', 'ethereum'
    url = f"{COINGECKO_API_BASE_URL}/simple/price?ids={coingecko_id}&vs_currencies=usd"
    try:
        response = requests.get(url, timeout=10) # Added timeout
        response.raise_for_status()
        data = response.json()
        if coingecko_id in data and 'usd' in data[coingecko_id]:
            return float(data[coingecko_id]['usd'])
        else:
            app.logger.warning(f"Could not parse price for crypto {coingecko_id} from CoinGecko. Response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching crypto price for {coingecko_id} from CoinGecko: {e}")
        return None
    except (ValueError, KeyError) as e: # Catch errors if coingecko_id or 'usd' is missing
        app.logger.error(f"Error parsing crypto price data for {coingecko_id} from CoinGecko: {e}. Response: {data if 'data' in locals() else 'No data'}")
        return None

# --- End Price Fetching Services ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    """
    Returns the entire portfolio, attempting to update stock/crypto prices.
    """
    assets = Asset.query.all()
    updated_assets_data = []
    price_updates_made = False

    for asset in assets:
        original_current_value = asset.current_value
        new_total_value_for_asset = None # This will be total value for the holding

        if asset.type == 'stock' and asset.ticker_symbol:
            price_per_share = get_stock_price(asset.ticker_symbol)
            if price_per_share is not None and asset.shares_owned is not None:
                new_total_value_for_asset = price_per_share * asset.shares_owned
                app.logger.info(f"Stock {asset.ticker_symbol}: Fetched price per share ${price_per_share:.2f}, new total value ${new_total_value_for_asset:.2f}")
            else:
                app.logger.info(f"Stock {asset.ticker_symbol}: Could not fetch or calculate new price.")
        elif asset.type == 'cryptocurrency' and asset.symbol:
            common_crypto_map = {
                "BTC": "bitcoin", "ETH": "ethereum", "DOGE": "dogecoin",
                "ADA": "cardano", "SOL": "solana", "XRP": "ripple",
                "DOT": "polkadot", "LTC": "litecoin", "BCH": "bitcoin-cash"
                # User might need to input coingecko_id directly for less common cryptos
            }
            coingecko_id = common_crypto_map.get(asset.symbol.upper())
            if coingecko_id:
                price_per_unit = get_crypto_price(coingecko_id)
                if price_per_unit is not None and asset.quantity_owned is not None:
                    new_total_value_for_asset = price_per_unit * asset.quantity_owned
                    app.logger.info(f"Crypto {asset.symbol} ({coingecko_id}): Fetched price per unit ${price_per_unit:.2f}, new total value ${new_total_value_for_asset:.2f}")
                else:
                    app.logger.info(f"Crypto {asset.symbol} ({coingecko_id}): Could not fetch or calculate new price.")
            else:
                app.logger.warning(f"No CoinGecko ID mapping for crypto symbol: {asset.symbol}. Price not updated.")

        if new_total_value_for_asset is not None and abs(new_total_value_for_asset - original_current_value) > 0.001:
            asset.current_value = new_total_value_for_asset
            db.session.add(asset) # Mark for update
            price_updates_made = True
            app.logger.info(f"Updating {asset.type} {asset.name} current value to ${asset.current_value:.2f}")
        
        updated_assets_data.append(asset.to_dict())
    
    if price_updates_made:
        try:
            db.session.commit()
            app.logger.info("Successfully committed price updates to DB.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error committing price updates to DB: {e}")

    total_value = db.session.query(db.func.sum(Asset.current_value)).scalar() or 0.0

    return jsonify({
        "total_value": total_value,
        "assets": updated_assets_data
    })

@app.route('/assets', methods=['POST'])
def add_asset_to_portfolio():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, no JSON data provided"}), 400

    asset_type_str = data.pop('asset_type', None)
    if not asset_type_str:
        return jsonify({"error": "Missing 'asset_type' field"}), 400

    name = data.get('name')
    if not name:
        return jsonify({"error": f"Missing 'name' for {asset_type_str}"}), 400
    
    initial_value = data.get('initial_value', 0.0)
    current_value_from_payload = data.get('current_value') 
    purchase_date_str = data.get('purchase_date')
    purchase_date = None
    if purchase_date_str:
        try:
            purchase_date = datetime.fromisoformat(purchase_date_str)
        except ValueError:
            return jsonify({"error": "Invalid 'purchase_date' format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
    
    asset_args = {
        'name': name,
        'description': data.get('description', ""),
        'initial_value': float(initial_value),
        'purchase_date': purchase_date if purchase_date else datetime.utcnow(),
        'type': asset_type_str.lower()
    }
    asset_args['current_value'] = float(initial_value) 

    new_asset = None

    try:
        if asset_type_str.lower() == 'stock':
            ticker_symbol = data.get('ticker_symbol')
            shares_owned = data.get('shares_owned')
            if not ticker_symbol or shares_owned is None:
                return jsonify({"error": "Missing 'ticker_symbol' or 'shares_owned' for stock"}), 400
            
            asset_args.update({
                'ticker_symbol': ticker_symbol,
                'shares_owned': float(shares_owned),
                'exchange': data.get('exchange', "")
            })
            if current_value_from_payload is not None:
                asset_args['current_value'] = float(current_value_from_payload)
            # Attempt to fetch live price on creation for initial current_value
            price_per_share = get_stock_price(ticker_symbol)
            if price_per_share is not None:
                asset_args['current_value'] = price_per_share * float(shares_owned)
            
            new_asset = Stock(**asset_args)

        elif asset_type_str.lower() == 'cryptocurrency':
            symbol = data.get('symbol') # e.g., BTC, ETH
            quantity_owned = data.get('quantity_owned')
            if not symbol or quantity_owned is None:
                return jsonify({"error": "Missing 'symbol' or 'quantity_owned' for cryptocurrency"}), 400

            asset_args.update({
                'symbol': symbol.upper(), # Store symbol consistently
                'quantity_owned': float(quantity_owned),
                'wallet_address': data.get('wallet_address', "")
            })
            if current_value_from_payload is not None:
                asset_args['current_value'] = float(current_value_from_payload)
            
            # Attempt to fetch live price on creation
            common_crypto_map = {
                "BTC": "bitcoin", "ETH": "ethereum", "DOGE": "dogecoin",
                "ADA": "cardano", "SOL": "solana", "XRP": "ripple",
                "DOT": "polkadot", "LTC": "litecoin", "BCH": "bitcoin-cash"
            }
            coingecko_id = common_crypto_map.get(symbol.upper())
            if coingecko_id:
                price_per_unit = get_crypto_price(coingecko_id)
                if price_per_unit is not None:
                    asset_args['current_value'] = price_per_unit * float(quantity_owned)

            new_asset = Cryptocurrency(**asset_args)

        elif asset_type_str.lower() == 'physical_asset':
            current_estimated_value = data.get('current_estimated_value')
            if current_estimated_value is None:
                 return jsonify({"error": "Missing 'current_estimated_value' for physical_asset"}), 400
            
            asset_args.update({
                'location': data.get('location', ""),
                'condition': data.get('condition', "")
            })
            asset_args['current_value'] = float(current_estimated_value)
            new_asset = PhysicalAsset(**asset_args)
        else:
            return jsonify({"error": f"Unknown asset_type: {asset_type_str}"}), 400

        if new_asset:
            db.session.add(new_asset)
            db.session.commit()
            return jsonify({"message": "Asset added successfully", "asset": new_asset.to_dict()}), 201
        else:
            return jsonify({"error": "Failed to create asset"}), 500

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding asset: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/assets/<string:asset_id>', methods=['DELETE'])
def delete_asset_from_portfolio(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    try:
        db.session.delete(asset)
        db.session.commit()
        return jsonify({"message": "Asset deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting asset {asset_id}: {e}")
        return jsonify({"error": "An unexpected error occurred during deletion"}), 500

@app.route('/assets/<string:asset_id>', methods=['PUT'])
def update_asset_in_portfolio(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, no JSON data provided"}), 400

    try:
        if 'name' in data: asset.name = data['name']
        if 'description' in data: asset.description = data['description']
        if 'initial_value' in data: asset.initial_value = float(data['initial_value'])
        
        if asset.type == 'physical_asset':
            if 'current_estimated_value' in data:
                asset.current_value = float(data['current_estimated_value'])
        elif 'current_value' in data: 
             asset.current_value = float(data['current_value'])

        if 'purchase_date' in data and data['purchase_date']:
            try:
                asset.purchase_date = datetime.fromisoformat(data['purchase_date'])
            except ValueError:
                return jsonify({"error": "Invalid 'purchase_date' format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400

        if asset.type == 'stock':
            if 'ticker_symbol' in data: asset.ticker_symbol = data['ticker_symbol']
            if 'shares_owned' in data: asset.shares_owned = float(data['shares_owned'])
            if 'exchange' in data: asset.exchange = data['exchange']
        elif asset.type == 'cryptocurrency':
            if 'symbol' in data: asset.symbol = data['symbol'].upper()
            if 'quantity_owned' in data: asset.quantity_owned = float(data['quantity_owned'])
            if 'wallet_address' in data: asset.wallet_address = data['wallet_address']
        elif asset.type == 'physical_asset':
            if 'location' in data: asset.location = data['location']
            if 'condition' in data: asset.condition = data['condition']
        
        db.session.commit()
        return jsonify({"message": "Asset updated successfully", "asset": asset.to_dict()}), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data for update: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating asset {asset_id}: {e}")
        return jsonify({"error": "An unexpected error occurred during update"}), 500

if __name__ == '__main__':
    with app.app_context(): # Create an application context
        db.create_all()    # Create database tables for our data models
    app.run(debug=True) 