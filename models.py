from datetime import datetime
import uuid
from extensions import db # Import db from extensions.py

class Asset(db.Model):
    __tablename__ = 'asset'
    
    # Core Asset Fields
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    initial_value = db.Column(db.Float, nullable=False, default=0.0)
    current_value = db.Column(db.Float, nullable=False, default=0.0)

    # Discriminator column for single-table inheritance
    type = db.Column(db.String(50), nullable=False)

    # Fields for Stock (nullable)
    ticker_symbol = db.Column(db.String(20), nullable=True)
    shares_owned = db.Column(db.Float, nullable=True)
    exchange = db.Column(db.String(50), nullable=True)

    # Fields for Cryptocurrency (nullable)
    symbol = db.Column(db.String(20), nullable=True)
    quantity_owned = db.Column(db.Float, nullable=True)
    wallet_address = db.Column(db.String(150), nullable=True)

    # Fields for PhysicalAsset (nullable)
    location = db.Column(db.String(100), nullable=True)
    condition = db.Column(db.String(100), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'asset',
        'polymorphic_on': type
    }

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.type}', current_value={self.current_value:.2f})>"

    def update_value(self, new_value: float):
        self.current_value = new_value
    
    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'initial_value': self.initial_value,
            'current_value': self.current_value,
            'asset_type': self.type
        }
        if self.type == 'stock':
            data['ticker_symbol'] = self.ticker_symbol
            data['shares_owned'] = self.shares_owned
            data['exchange'] = self.exchange
        elif self.type == 'cryptocurrency':
            data['symbol'] = self.symbol
            data['quantity_owned'] = self.quantity_owned
            data['wallet_address'] = self.wallet_address
        elif self.type == 'physical_asset':
            data['location'] = self.location
            data['condition'] = self.condition
        return data

class Stock(Asset):
    # No __tablename__ needed for single-table inheritance subclasses
    __mapper_args__ = {
        'polymorphic_identity': 'stock',
    }
    # Specific fields (ticker_symbol, shares_owned, exchange) are on Asset model

class Cryptocurrency(Asset):
    __mapper_args__ = {
        'polymorphic_identity': 'cryptocurrency',
    }
    # Specific fields (symbol, quantity_owned, wallet_address) are on Asset model

class PhysicalAsset(Asset):
    __mapper_args__ = {
        'polymorphic_identity': 'physical_asset',
    }
    # Specific fields (location, condition) are on Asset model

    def update_estimated_value(self, new_estimated_value: float):
        self.update_value(new_estimated_value)

# The old Portfolio class is removed as its functionality will be handled by DB queries in app.py 